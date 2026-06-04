"""Stage 2 supplementary analysis: cross-rep variance table + per-scenario plots.

Reads 60 formal runs (6 scenarios x 10 reps), computes mean/std/CV/IQR for the
core engineering-level metrics, and emits:
  - reports/variance_table_<ts>.md
  - figures/checkpoint_count_boxplot_<ts>.png
  - figures/rpc_latency_p50_p95_<ts>.png
  - figures/recovery_time_strip_<ts>.png

Median in the variance table uses the same nearest-rank (C=1) convention as
summarize_runs.py so numbers cross-check directly with the formal summary.
"""
from __future__ import annotations

import json
import os
import statistics
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "data" / "runs"
REPORTS = ROOT / "reports"
FIGURES = ROOT / "figures"
FIGURES.mkdir(exist_ok=True)

PLAN = {
    "baseline":               (2026052402, range(1, 11)),
    "delay_low":              (2026052402, range(1, 11)),
    "delay_high":             (2026052402, range(1, 11)),
    "loss_low":               (2026052402, range(1, 11)),
    "crash_one_validator":    (2026052406, range(1, 11)),
    "two_validator_pressure": (2026052406, range(1, 11)),
}

NUMERIC_FIELDS = [
    "checkpoint_count",
    "checkpoint_interval_ms_p50",
    "checkpoint_interval_ms_p95",
    "rpc_latency_ms_p50",
    "rpc_latency_ms_p95",
    "recovery_time_ms",
]


def nearest_rank(values, percentile):
    values = sorted(v for v in values if isinstance(v, (int, float)))
    if not values:
        return None
    rank = int(percentile / 100 * len(values) + 0.999999999)
    rank = min(max(rank, 1), len(values))
    return values[rank - 1]


def load_runs():
    by_scenario = {}
    for scenario, (seed, reps) in PLAN.items():
        rows = []
        for rep in reps:
            run_id = f"{scenario}_seed{seed}_rep{rep:02d}"
            mx_path = RUNS_ROOT / run_id / "metrics" / "consensus_metrics.json"
            with mx_path.open("r", encoding="utf-8") as fh:
                rows.append(json.load(fh))
        by_scenario[scenario] = rows
    return by_scenario


def variance_row(values):
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return {"n": 0}
    n = len(nums)
    mean = statistics.fmean(nums)
    stdev = statistics.stdev(nums) if n > 1 else 0.0
    cv = (stdev / mean) if mean else None
    return {
        "n": n,
        "mean": mean,
        "stdev": stdev,
        "cv": cv,
        "min": min(nums),
        "p25": nearest_rank(nums, 25),
        "median": nearest_rank(nums, 50),
        "p75": nearest_rank(nums, 75),
        "max": max(nums),
        "iqr": nearest_rank(nums, 75) - nearest_rank(nums, 25),
    }


def emit_variance_table(by_scenario, out_path):
    lines = []
    lines.append("# Stage 2 Cross-Rep Variance Table")
    lines.append("")
    lines.append(f"- Generated (UTC): {datetime.now(timezone.utc).isoformat()}")
    lines.append("- Source: 60 formal runs, 6 scenarios x 10 reps")
    lines.append("- Median / p25 / p75 use nearest-rank percentile (C=1), consistent with `summarize_runs.py`.")
    lines.append("- CV = stdev / mean (omitted when mean is zero or null)")
    lines.append("")
    for field in NUMERIC_FIELDS:
        lines.append(f"## {field}")
        lines.append("")
        lines.append("| scenario | n | mean | stdev | CV | min | p25 | median | p75 | max | IQR |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for scenario in PLAN.keys():
            vals = [r.get(field) for r in by_scenario[scenario]]
            stats = variance_row(vals)
            if stats["n"] == 0:
                lines.append(f"| {scenario} | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
                continue
            def f(v):
                if v is None:
                    return "n/a"
                if isinstance(v, float):
                    return f"{v:.3f}" if abs(v) < 1000 else f"{v:.0f}"
                return str(v)
            cv_str = "n/a" if stats["cv"] is None else f"{stats['cv']*100:.2f}%"
            lines.append(
                f"| {scenario} | {stats['n']} | {f(stats['mean'])} | {f(stats['stdev'])} | {cv_str} | "
                f"{f(stats['min'])} | {f(stats['p25'])} | {f(stats['median'])} | {f(stats['p75'])} | "
                f"{f(stats['max'])} | {f(stats['iqr'])} |"
            )
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def plot_checkpoint_boxplot(by_scenario, out_path):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    scenarios = list(PLAN.keys())
    data = [[r["checkpoint_count"] for r in by_scenario[s]] for s in scenarios]
    bp = ax.boxplot(data, tick_labels=scenarios, showmeans=True, meanline=True, patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#cfe2ff")
        patch.set_edgecolor("#1f4e8a")
    ax.set_ylabel("checkpoint_count per run")
    ax.set_title("Stage 2: checkpoint_count distribution across 10 reps (n=10 per scenario)")
    ax.grid(True, axis="y", alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_rpc_latency(by_scenario, out_path):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    scenarios = list(PLAN.keys())
    x = np.arange(len(scenarios))
    p50_med = [nearest_rank([r["rpc_latency_ms_p50"] for r in by_scenario[s]], 50) for s in scenarios]
    p95_med = [nearest_rank([r["rpc_latency_ms_p95"] for r in by_scenario[s]], 50) for s in scenarios]
    p50_lo  = [min(r["rpc_latency_ms_p50"] for r in by_scenario[s]) for s in scenarios]
    p50_hi  = [max(r["rpc_latency_ms_p50"] for r in by_scenario[s]) for s in scenarios]
    p95_lo  = [min(r["rpc_latency_ms_p95"] for r in by_scenario[s]) for s in scenarios]
    p95_hi  = [max(r["rpc_latency_ms_p95"] for r in by_scenario[s]) for s in scenarios]
    ax.errorbar(x - 0.1, p50_med, yerr=[np.subtract(p50_med, p50_lo), np.subtract(p50_hi, p50_med)],
                fmt="o-", color="#1f4e8a", label="p50 (median across reps, bars=min/max)")
    ax.errorbar(x + 0.1, p95_med, yerr=[np.subtract(p95_med, p95_lo), np.subtract(p95_hi, p95_med)],
                fmt="s-", color="#b8333a", label="p95 (median across reps, bars=min/max)")
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=15, ha="right")
    ax.set_ylabel("RPC latency (ms)")
    ax.set_title("Stage 2: RPC latency p50/p95 across scenarios")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_recovery_strip(by_scenario, out_path):
    fig, ax = plt.subplots(figsize=(8, 5))
    crash_rows = by_scenario["crash_one_validator"]
    rec = [r["recovery_time_ms"] for r in crash_rows]
    reps = [r["repeat_index"] for r in crash_rows]
    ax.scatter(reps, rec, s=80, color="#b8333a", zorder=3)
    med = nearest_rank(rec, 50)
    ax.axhline(med, color="#1f4e8a", linestyle="--", label=f"median (nearest-rank)={med} ms")
    ax.set_xlabel("rep index")
    ax.set_ylabel("recovery_time_ms")
    ax.set_xticks(reps)
    ax.set_title("Stage 2: crash_one_validator recovery_time_ms per rep (n=10)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    by_scenario = load_runs()
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    var_path = REPORTS / f"variance_table_{ts}.md"
    emit_variance_table(by_scenario, var_path)
    print(f"variance table -> {var_path}")
    fp1 = FIGURES / f"checkpoint_count_boxplot_{ts}.png"
    fp2 = FIGURES / f"rpc_latency_p50_p95_{ts}.png"
    fp3 = FIGURES / f"recovery_time_strip_{ts}.png"
    plot_checkpoint_boxplot(by_scenario, fp1); print(f"figure -> {fp1}")
    plot_rpc_latency(by_scenario, fp2);        print(f"figure -> {fp2}")
    plot_recovery_strip(by_scenario, fp3);     print(f"figure -> {fp3}")


if __name__ == "__main__":
    main()
