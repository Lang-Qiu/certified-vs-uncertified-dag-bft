"""ckpt_p95 root-cause investigation.

For each of the 6 formal scenarios, load all 10 reps' consensus_metrics.json
and dump per-rep checkpoint_interval_ms_p50 / _p95 / checkpoint_count /
rpc_latency_p50/p95 / availability / successful_transactions.

Then compute distribution stats (min/median/max/IQR/CV) per scenario, and
flag which reps are outliers relative to the per-scenario median.

Writes a markdown report next to summarize_runs.py output style.
"""
from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
REPORT_DIR = ROOT / "reports"

# Formal plan (mirrors summarize_runs.py / audit script).
PLAN = [
    ("baseline", "seed2026052402", 10),
    ("delay_low", "seed2026052402", 10),
    ("delay_high", "seed2026052402", 10),
    ("loss_low", "seed2026052402", 10),
    ("crash_one_validator", "seed2026052406", 10),
    ("two_validator_pressure", "seed2026052406", 10),
]

FIELDS = [
    "checkpoint_count",
    "checkpoint_interval_ms_p50",
    "checkpoint_interval_ms_p95",
    "rpc_latency_ms_p50",
    "rpc_latency_ms_p95",
    "availability_ratio",
    "successful_transactions",
    "failed_transactions",
    "recovery_time_ms",
]


def load_rep(scenario: str, seed: str, rep: int) -> dict:
    run_id = f"{scenario}_{seed}_rep{rep:02d}"
    path = RUNS / run_id / "metrics" / "consensus_metrics.json"
    with path.open(encoding="utf-8") as fh:
        m = json.load(fh)
    return {"run_id": run_id, **{k: m.get(k) for k in FIELDS}}


def nearest_rank(values, percentile):
    if not values:
        return None
    s = sorted(values)
    rank = int((percentile / 100.0) * len(s) + 0.999999999)
    rank = max(1, min(rank, len(s)))
    return s[rank - 1]


def cv(values):
    if len(values) < 2:
        return None
    m = statistics.mean(values)
    if m == 0:
        return None
    return statistics.stdev(values) / m * 100.0


def per_scenario_stats(field, reps):
    xs = [r[field] for r in reps if isinstance(r[field], (int, float))]
    if not xs:
        return None
    return {
        "n": len(xs),
        "min": min(xs),
        "p25": nearest_rank(xs, 25),
        "median": nearest_rank(xs, 50),
        "p75": nearest_rank(xs, 75),
        "max": max(xs),
        "mean": statistics.mean(xs),
        "stdev": statistics.stdev(xs) if len(xs) > 1 else 0.0,
        "cv_pct": cv(xs),
    }


def collect() -> dict:
    out = {}
    for scenario, seed, reps in PLAN:
        all_reps = [load_rep(scenario, seed, i) for i in range(1, reps + 1)]
        out[scenario] = {
            "seed": seed,
            "reps": all_reps,
            "stats": {f: per_scenario_stats(f, all_reps) for f in FIELDS},
        }
    return out


def render(data: dict) -> str:
    lines = []
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    lines.append("# Checkpoint p95 instability — root-cause investigation")
    lines.append("")
    lines.append(f"- Generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"- Source: 60 formal reps under data/runs/<scenario>_<seed>_rep01..10")
    lines.append("- Triggered by: variance_table_20260525104240.md observation that "
                 "two_validator_pressure ckpt_p95 CV ~ 63%")
    lines.append("")
    lines.append("## 1. Per-rep checkpoint metrics (all scenarios)")
    lines.append("")
    lines.append("| scenario | rep | ckpt_count | ckpt_int_p50 (ms) | ckpt_int_p95 (ms) | rpc_p50 | rpc_p95 | avail | tx_ok | rec_ms |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for scenario, sd in data.items():
        for r in sd["reps"]:
            rec = r.get("recovery_time_ms")
            rec_s = f"{rec}" if isinstance(rec, (int, float)) else "n/a"
            lines.append(
                f"| {scenario} | {r['run_id'].rsplit('_rep', 1)[1]} | "
                f"{r['checkpoint_count']} | {r['checkpoint_interval_ms_p50']} | "
                f"{r['checkpoint_interval_ms_p95']} | "
                f"{r['rpc_latency_ms_p50']} | {r['rpc_latency_ms_p95']} | "
                f"{r['availability_ratio']:.3f} | {r['successful_transactions']} | "
                f"{rec_s} |"
            )
    lines.append("")
    lines.append("## 2. Per-scenario distribution (focus: ckpt_interval_ms_p95)")
    lines.append("")
    lines.append("| scenario | n | min | p25 | median | p75 | max | mean | stdev | CV% |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for scenario, sd in data.items():
        s = sd["stats"]["checkpoint_interval_ms_p95"]
        if s is None:
            continue
        cv_s = f"{s['cv_pct']:.2f}" if s["cv_pct"] is not None else "-"
        lines.append(
            f"| {scenario} | {s['n']} | {s['min']} | {s['p25']} | {s['median']} | "
            f"{s['p75']} | {s['max']} | {s['mean']:.1f} | {s['stdev']:.1f} | {cv_s} |"
        )
    lines.append("")
    lines.append("## 3. Per-scenario distribution (control: ckpt_interval_ms_p50)")
    lines.append("")
    lines.append("| scenario | n | min | median | max | mean | stdev | CV% |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for scenario, sd in data.items():
        s = sd["stats"]["checkpoint_interval_ms_p50"]
        if s is None:
            continue
        cv_s = f"{s['cv_pct']:.2f}" if s["cv_pct"] is not None else "-"
        lines.append(
            f"| {scenario} | {s['n']} | {s['min']} | {s['median']} | {s['max']} | "
            f"{s['mean']:.1f} | {s['stdev']:.1f} | {cv_s} |"
        )
    lines.append("")
    lines.append("## 4. Per-scenario distribution (control: checkpoint_count)")
    lines.append("")
    lines.append("| scenario | n | min | median | max | mean | stdev | CV% |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for scenario, sd in data.items():
        s = sd["stats"]["checkpoint_count"]
        if s is None:
            continue
        cv_s = f"{s['cv_pct']:.2f}" if s["cv_pct"] is not None else "-"
        lines.append(
            f"| {scenario} | {s['n']} | {s['min']} | {s['median']} | {s['max']} | "
            f"{s['mean']:.1f} | {s['stdev']:.1f} | {cv_s} |"
        )
    lines.append("")

    # Outlier detection — rep whose ckpt_p95 is > p75 + 1.5*(p75-p25) or
    # < p25 - 1.5*(p75-p25) per scenario.
    lines.append("## 5. ckpt_p95 outlier reps (Tukey 1.5*IQR fence)")
    lines.append("")
    lines.append("| scenario | rep | ckpt_p95 | scenario_median | scenario_IQR | distance_above_p75 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    any_outlier = False
    for scenario, sd in data.items():
        s = sd["stats"]["checkpoint_interval_ms_p95"]
        if s is None or s["p75"] is None or s["p25"] is None:
            continue
        iqr = s["p75"] - s["p25"]
        upper = s["p75"] + 1.5 * iqr
        lower = s["p25"] - 1.5 * iqr
        for r in sd["reps"]:
            v = r["checkpoint_interval_ms_p95"]
            if not isinstance(v, (int, float)):
                continue
            if v > upper or v < lower:
                any_outlier = True
                lines.append(
                    f"| {scenario} | {r['run_id'].rsplit('_rep', 1)[1]} | {v} | "
                    f"{s['median']} | {iqr} | {v - s['p75']:+.1f} |"
                )
    if not any_outlier:
        lines.append("| _none_ | | | | | |")
    lines.append("")

    return "\n".join(lines)


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = collect()
    body = render(data)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out = REPORT_DIR / f"ckpt_p95_root_cause_{ts}.md"
    out.write_text(body, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
