"""Analyze additivity vs synergy of double-fault scenario.

Compares 4 conditions on true (log-derived) ckpt metrics:
  - baseline            (no faults)
  - delay_only_v1_match (150±30 ms netem delay on v1)
  - loss_only_v2_match  (2% netem loss on v2)
  - two_validator_pressure  (both)

Test:
  expected_additive = X(delay) + X(loss) - X(baseline)
  observed = X(two_pressure)
  ratio = observed / expected_additive

Reports:
  - per-rep raw and per-scenario aggregate
  - additivity ratio per metric
  - non-parametric medians and IQR (n=10 per cell is small)
"""
from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
REPORTS = ROOT / "reports"

# (scenario_logical_label, scenario_prefix in run dirs)
SCENARIOS = [
    ("baseline",                 "baseline_seed2026052402"),
    ("delay_only_v1_match",      "delay_only_v1_match_seed2026052501"),
    ("loss_only_v2_match",       "loss_only_v2_match_seed2026052501"),
    ("two_validator_pressure",   "two_validator_pressure_seed2026052406"),
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


def load_scenario(prefix: str):
    reps = []
    for i in range(1, 11):
        rep_dir = RUNS / f"{prefix}_rep{i:02d}"
        true_path = rep_dir / "metrics" / "consensus_metrics_true.json"
        if not true_path.exists():
            continue
        reps.append(json.loads(true_path.read_text(encoding="utf-8")))
    return reps


def agg(vals):
    if not vals:
        return {"n": 0}
    return {
        "n": len(vals),
        "median": nearest_rank(vals, 50),
        "p25": nearest_rank(vals, 25),
        "p75": nearest_rank(vals, 75),
        "min": min(vals),
        "max": max(vals),
        "mean": statistics.mean(vals),
        "stdev": statistics.stdev(vals) if len(vals) > 1 else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    cells = {}
    for label, prefix in SCENARIOS:
        cells[label] = load_scenario(prefix)

    aggs = {}
    for label, reps in cells.items():
        aggs[label] = {m: agg([r[m] for r in reps if r.get(m) is not None])
                       for m in METRICS}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out_path = Path(args.output) if args.output else REPORTS / f"fault_decoupling_{ts}.md"

    L = []
    L.append("# Double-fault decoupling analysis (additivity vs synergy)")
    L.append("")
    L.append(f"- Generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    L.append("- Metric source: `consensus_metrics_true.json` (log-derived, true per-checkpoint intervals)")
    L.append("- n=10 per scenario (where available)")
    L.append("")
    L.append("## Coverage")
    L.append("")
    for label, reps in cells.items():
        L.append(f"- **{label}**: n={len(reps)}")
    L.append("")

    L.append("## Per-scenario aggregate (median [p25, p75])")
    L.append("")
    L.append("| metric | baseline | delay_only_v1 | loss_only_v2 | two_validator_pressure |")
    L.append("| --- | --- | --- | --- | --- |")
    for m in METRICS:
        cols = []
        for label, _ in SCENARIOS:
            a = aggs[label].get(m, {"n": 0})
            if a["n"] == 0:
                cols.append("—")
                continue
            cols.append(f"{a['median']:.1f} [{a['p25']:.1f}, {a['p75']:.1f}]")
        L.append(f"| {m} | " + " | ".join(cols) + " |")
    L.append("")

    L.append("## Additivity test")
    L.append("")
    L.append("**Definition**: For each metric X,")
    L.append("- expected_additive(X) = X(delay_only_v1) + X(loss_only_v2) - X(baseline)")
    L.append("- observed(X) = X(two_validator_pressure)")
    L.append("- ratio = observed / expected_additive")
    L.append("- Δ_excess = observed - expected_additive (the part NOT explained by additivity)")
    L.append("")
    L.append("**Interpretation**:")
    L.append("- ratio ≈ 1 (Δ_excess ≈ 0): additive — combining faults gives no extra cost beyond their sum")
    L.append("- ratio > 1 (Δ_excess > 0): synergistic / multiplicative — combined effect exceeds sum")
    L.append("- ratio < 1: anti-synergistic — combined effect less than sum")
    L.append("")
    L.append("Using **medians** (n=10 per cell, small-sample non-parametric):")
    L.append("")
    L.append("| metric | baseline med | delay_only med | loss_only med | observed med | expected_additive | ratio | Δ_excess |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for m in METRICS:
        bl = aggs["baseline"].get(m, {}).get("median")
        do = aggs["delay_only_v1_match"].get(m, {}).get("median")
        lo = aggs["loss_only_v2_match"].get(m, {}).get("median")
        obs = aggs["two_validator_pressure"].get(m, {}).get("median")
        if None in (bl, do, lo, obs):
            L.append(f"| {m} | — | — | — | — | — | — | — |")
            continue
        expected = do + lo - bl
        ratio = obs / expected if expected else float("nan")
        excess = obs - expected
        L.append(f"| {m} | {bl:.1f} | {do:.1f} | {lo:.1f} | {obs:.1f} | {expected:.1f} | {ratio:.2f} | {excess:+.1f} |")
    L.append("")

    L.append("## Per-rep raw")
    L.append("")
    L.append("| scenario | rep | p50_true | p95_true | max | n_>2000 | n_500_2000 | ckpt_count |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for label, reps in cells.items():
        for r in reps:
            L.append(f"| {label} | {r['repeat_index']} | "
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
