"""Cross-scale ablation: do n=7 additivity findings replicate at n=4?

Compares 4 matched scenarios at n=4 vs n=7 (physical fault parameters
identical: 150±30 ms delay, 2% loss). Per-scenario distributions are
shown side by side, and the additivity test is re-run at n=4.

Cells:
  n=7  baseline                 / n=4  baseline_n4
  n=7  delay_only_v1_match      / n=4  delay_only_v1_n4
  n=7  loss_only_v2_match       / n=4  loss_only_v2_n4
  n=7  two_validator_pressure   / n=4  two_validator_pressure_n4
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
REPORTS = ROOT / "reports"

CELLS = [
    # (label, n, prefix)
    ("baseline",                7, "baseline_seed2026052402"),
    ("delay_only_v1",           7, "delay_only_v1_match_seed2026052501"),
    ("loss_only_v2",            7, "loss_only_v2_match_seed2026052501"),
    ("two_validator_pressure",  7, "two_validator_pressure_seed2026052406"),
    ("baseline",                4, "baseline_n4_seed20260525"),
    ("delay_only_v1",           4, "delay_only_v1_n4_seed20260525"),
    ("loss_only_v2",            4, "loss_only_v2_n4_seed20260525"),
    ("two_validator_pressure",  4, "two_validator_pressure_n4_seed20260525"),
]

METRICS = [
    "checkpoint_interval_ms_p50_true",
    "checkpoint_interval_ms_p95_true",
    "checkpoint_interval_ms_max_true",
    "checkpoint_count_true",
    "n_intervals_gt_2000ms",
    "n_intervals_500_to_2000ms",
]


def nearest_rank(values, percentile):
    if not values:
        return None
    s = sorted(values)
    rank = max(1, int(percentile / 100.0 * len(s) + 0.999999999))
    return s[min(rank, len(s)) - 1]


def cv(values):
    if len(values) < 2:
        return None
    m = statistics.mean(values)
    if m == 0:
        return None
    return statistics.stdev(values) / m * 100.0


def load(prefix):
    rows = []
    for i in range(1, 11):
        rep_dir = RUNS / f"{prefix}_rep{i:02d}"
        true_path = rep_dir / "metrics" / "consensus_metrics_true.json"
        if true_path.exists():
            rows.append(json.loads(true_path.read_text(encoding="utf-8")))
    return rows


def agg(vals):
    if not vals:
        return {"n": 0, "median": None, "p25": None, "p75": None, "cv": None}
    return {
        "n": len(vals),
        "median": nearest_rank(vals, 50),
        "p25":    nearest_rank(vals, 25),
        "p75":    nearest_rank(vals, 75),
        "cv":     cv(vals),
    }


def main():
    data = {(label, n): load(prefix) for label, n, prefix in CELLS}

    aggs = {}
    for (label, n), reps in data.items():
        aggs[(label, n)] = {m: agg([r[m] for r in reps if r.get(m) is not None])
                            for m in METRICS}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out_path = REPORTS / f"scale_ablation_n4_vs_n7_{ts}.md"

    L = []
    L.append("# Scale ablation: n=4 vs n=7 with identical physical fault parameters")
    L.append("")
    L.append(f"- Generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    L.append("- Metric source: `consensus_metrics_true.json` (log-derived)")
    L.append("- Fault parameters held constant across scales: delay=150±30 ms, loss=2%")
    L.append("- BFT bounds: n=7 → f=2; n=4 → f=1 (two_validator_pressure meets f at n=4 and is below it at n=7)")
    L.append("")

    L.append("## Coverage")
    L.append("")
    for (label, n), reps in data.items():
        L.append(f"- **{label} (n={n})**: reps={len(reps)}")
    L.append("")

    # Cross-scale comparison per scenario
    L.append("## Per-scenario, n=7 vs n=4 (median [p25, p75], CV%)")
    L.append("")
    L.append("| scenario | metric | n=7 | n=4 | n=4 / n=7 (median ratio) |")
    L.append("| --- | --- | --- | --- | ---: |")
    scenarios = ["baseline", "delay_only_v1", "loss_only_v2", "two_validator_pressure"]
    for scen in scenarios:
        for m in METRICS:
            a7 = aggs.get((scen, 7), {}).get(m, {"median": None})
            a4 = aggs.get((scen, 4), {}).get(m, {"median": None})
            if a7.get("median") is None or a4.get("median") is None:
                continue
            cv7 = a7["cv"] if a7["cv"] is not None else 0.0
            cv4 = a4["cv"] if a4["cv"] is not None else 0.0
            ratio = a4["median"] / a7["median"] if a7["median"] else float("nan")
            L.append(f"| {scen} | {m} | "
                     f"{a7['median']:.1f} [{a7['p25']:.1f}, {a7['p75']:.1f}] (CV {cv7:.2f}%) | "
                     f"{a4['median']:.1f} [{a4['p25']:.1f}, {a4['p75']:.1f}] (CV {cv4:.2f}%) | "
                     f"{ratio:.2f} |")
        L.append("|  |  |  |  |  |")
    L.append("")

    # Additivity test at each scale
    L.append("## Additivity test, replicated at each scale")
    L.append("")
    L.append("**Definition**: expected_additive = X(delay_only_v1) + X(loss_only_v2) − X(baseline)")
    L.append("                observed = X(two_validator_pressure)")
    L.append("                ratio = observed / expected; Δ = observed − expected")
    L.append("")

    for n in (7, 4):
        L.append(f"### n={n}")
        L.append("")
        L.append("| metric | baseline | delay_only_v1 | loss_only_v2 | observed | expected | ratio | Δ_excess |")
        L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for m in METRICS:
            bl = aggs.get(("baseline", n), {}).get(m, {}).get("median")
            do = aggs.get(("delay_only_v1", n), {}).get(m, {}).get("median")
            lo = aggs.get(("loss_only_v2", n), {}).get(m, {}).get("median")
            obs = aggs.get(("two_validator_pressure", n), {}).get(m, {}).get("median")
            if None in (bl, do, lo, obs):
                L.append(f"| {m} | — | — | — | — | — | — | — |")
                continue
            expected = do + lo - bl
            ratio = obs / expected if expected else float("nan")
            excess = obs - expected
            L.append(f"| {m} | {bl:.1f} | {do:.1f} | {lo:.1f} | {obs:.1f} | {expected:.1f} | {ratio:.2f} | {excess:+.1f} |")
        L.append("")

    # Per-rep raw for n=4
    L.append("## Per-rep raw (n=4 only)")
    L.append("")
    L.append("| scenario | rep | p50_true | p95_true | max | n_>2000 | n_500_2000 | ckpt_count |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for scen in scenarios:
        for r in data.get((scen, 4), []):
            L.append(f"| {scen}_n4 | {r['repeat_index']} | "
                     f"{r['checkpoint_interval_ms_p50_true']:.1f} | "
                     f"{r['checkpoint_interval_ms_p95_true']:.1f} | "
                     f"{r['checkpoint_interval_ms_max_true']:.1f} | "
                     f"{r['n_intervals_gt_2000ms']} | "
                     f"{r['n_intervals_500_to_2000ms']} | "
                     f"{r['checkpoint_count_true']} |")
    L.append("")

    out_path.write_text("\n".join(L), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
