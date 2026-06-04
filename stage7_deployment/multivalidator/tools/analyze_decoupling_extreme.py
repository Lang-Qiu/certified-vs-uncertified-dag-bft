"""Extended additivity analysis: stress-test the additive interaction.

Two tests on top of the baseline (a) analysis:

  Test 1 — same-validator stacking (do delay+loss on the SAME node still add?):
      expected = X(delay_only_v1) + X(loss_only_v1) - X(baseline)
      observed = X(delay_loss_same_v1)

  Test 2 — higher loss rate (does additivity hold at 5% loss instead of 2%?):
      expected = X(delay_only_v1) + X(loss_high_v2) - X(baseline)
      observed = X(pressure_high_loss)

For comparison the original (a) test is included:

  Test 0 — different-validator (the canonical case from a/decoupling):
      expected = X(delay_only_v1) + X(loss_only_v2) - X(baseline)
      observed = X(two_validator_pressure)
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
REPORTS = ROOT / "reports"

# (label, run-id prefix)
CELLS = [
    ("baseline",                  "baseline_seed2026052402"),
    ("delay_only_v1",             "delay_only_v1_match_seed2026052501"),
    ("loss_only_v2",              "loss_only_v2_match_seed2026052501"),
    ("two_validator_pressure",    "two_validator_pressure_seed2026052406"),
    ("loss_only_v1",              "loss_only_v1_match_seed20260525"),
    ("delay_loss_same_v1",        "delay_loss_same_v1_seed20260525"),
    ("loss_high_v2",              "loss_high_v2_seed20260525"),
    ("pressure_high_loss",        "pressure_high_loss_seed20260525"),
]

METRICS = [
    "checkpoint_interval_ms_p50_true",
    "checkpoint_interval_ms_p95_true",
    "checkpoint_interval_ms_max_true",
    "checkpoint_count_true",
    "n_intervals_gt_2000ms",
    "n_intervals_500_to_2000ms",
]

TESTS = [
    ("Test 0 — diff-validator 2% loss (canonical, n=7)",
     "delay_only_v1", "loss_only_v2", "two_validator_pressure"),
    ("Test 1 — same-validator stacking (delay+loss both on v1)",
     "delay_only_v1", "loss_only_v1", "delay_loss_same_v1"),
    ("Test 2 — higher loss extreme (delay v1 + 5% loss v2)",
     "delay_only_v1", "loss_high_v2", "pressure_high_loss"),
]


def nearest_rank(values, percentile):
    if not values:
        return None
    s = sorted(values)
    rank = max(1, int(percentile / 100.0 * len(s) + 0.999999999))
    return s[min(rank, len(s)) - 1]


def load_cell(prefix):
    rows = []
    for i in range(1, 11):
        rep_dir = RUNS / f"{prefix}_rep{i:02d}"
        true_path = rep_dir / "metrics" / "consensus_metrics_true.json"
        if true_path.exists():
            rows.append(json.loads(true_path.read_text(encoding="utf-8")))
    return rows


def agg(vals):
    if not vals:
        return {"n": 0, "median": None, "p25": None, "p75": None,
                "min": None, "max": None, "mean": None, "stdev": None}
    return {
        "n": len(vals),
        "median": nearest_rank(vals, 50),
        "p25":    nearest_rank(vals, 25),
        "p75":    nearest_rank(vals, 75),
        "min":    min(vals),
        "max":    max(vals),
        "mean":   statistics.mean(vals),
        "stdev":  statistics.stdev(vals) if len(vals) > 1 else 0.0,
    }


def main():
    cells = {label: load_cell(prefix) for label, prefix in CELLS}

    aggs = {}
    for label, reps in cells.items():
        aggs[label] = {m: agg([r[m] for r in reps if r.get(m) is not None])
                       for m in METRICS}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out_path = REPORTS / f"fault_decoupling_extreme_{ts}.md"

    L = []
    L.append("# Additivity stress test (Tests 0/1/2)")
    L.append("")
    L.append(f"- Generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    L.append("- Metric source: `consensus_metrics_true.json` (log-derived)")
    L.append("- n=10 per cell")
    L.append("")
    L.append("## Coverage")
    L.append("")
    for label, reps in cells.items():
        L.append(f"- **{label}**: n={len(reps)}")
    L.append("")

    L.append("## Per-cell aggregate (median [p25, p75])")
    L.append("")
    header = ["metric"] + [label for label, _ in CELLS]
    L.append("| " + " | ".join(header) + " |")
    L.append("| " + " | ".join(["---"] * len(header)) + " |")
    for m in METRICS:
        row = [m]
        for label, _ in CELLS:
            a = aggs[label][m]
            if a["n"] == 0:
                row.append("—")
            else:
                row.append(f"{a['median']:.1f} [{a['p25']:.1f}, {a['p75']:.1f}]")
        L.append("| " + " | ".join(row) + " |")
    L.append("")

    L.append("## Additivity tests")
    L.append("")
    L.append("**Definition**: expected_additive(X) = X(single_A) + X(single_B) − X(baseline); ratio = observed / expected; Δ_excess = observed − expected.")
    L.append("- ratio ≈ 1: additive")
    L.append("- ratio > 1: super-additive (synergistic)")
    L.append("- ratio < 1: sub-additive (combined < sum)")
    L.append("")

    for test_label, A, B, OBS in TESTS:
        L.append(f"### {test_label}")
        L.append("")
        L.append(f"- single_A = `{A}`")
        L.append(f"- single_B = `{B}`")
        L.append(f"- observed = `{OBS}`")
        L.append("")
        L.append("| metric | baseline | single_A | single_B | observed | expected_additive | ratio | Δ_excess |")
        L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for m in METRICS:
            bl  = aggs["baseline"][m]["median"]
            sa  = aggs[A][m]["median"]
            sb  = aggs[B][m]["median"]
            obs = aggs[OBS][m]["median"]
            if None in (bl, sa, sb, obs):
                L.append(f"| {m} | — | — | — | — | — | — | — |")
                continue
            expected = sa + sb - bl
            ratio = obs / expected if expected else float("nan")
            excess = obs - expected
            L.append(f"| {m} | {bl:.1f} | {sa:.1f} | {sb:.1f} | {obs:.1f} | {expected:.1f} | {ratio:.2f} | {excess:+.1f} |")
        L.append("")

    L.append("## Per-rep raw (new cells only)")
    L.append("")
    L.append("| scenario | rep | p50_true | p95_true | max | n_>2000 | n_500_2000 | ckpt_count |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for label in ["loss_only_v1", "delay_loss_same_v1", "loss_high_v2", "pressure_high_loss"]:
        for r in cells[label]:
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
