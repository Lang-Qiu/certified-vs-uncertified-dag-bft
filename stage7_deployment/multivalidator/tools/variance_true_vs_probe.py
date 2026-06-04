"""Compare probe-based vs log-derived ckpt p50/p95 variance.

Reads each of the 60 formal reps' `consensus_metrics.json` (probe-based)
and `consensus_metrics_true.json` (log-derived) and produces:

  - reports/variance_true_vs_probe_<ts>.md  — side-by-side table
  - figures/ckpt_p95_true_vs_probe_<ts>.png — boxplot

This makes the measurement-pipeline distortion visible at a glance.
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
REPORTS = ROOT / "reports"
FIGURES = ROOT / "figures"
FIGURES.mkdir(exist_ok=True)

PLAN = [
    ("baseline", "2026052402"),
    ("delay_low", "2026052402"),
    ("delay_high", "2026052402"),
    ("loss_low", "2026052402"),
    ("crash_one_validator", "2026052406"),
    ("two_validator_pressure", "2026052406"),
]


def nearest_rank(values, p):
    if not values: return None
    s = sorted(values)
    r = max(1, int(p / 100.0 * len(s) + 0.999999999))
    return s[min(r, len(s)) - 1]


def cv(values):
    if len(values) < 2: return None
    m = statistics.mean(values)
    if m == 0: return None
    return statistics.stdev(values) / m * 100.0


def collect():
    data = {}
    for scen, seed in PLAN:
        probe, true_ = [], []
        for i in range(1, 11):
            d = RUNS / f"{scen}_seed{seed}_rep{i:02d}"
            try:
                p_json = json.loads((d / "metrics" / "consensus_metrics.json").read_text(encoding="utf-8"))
                t_json = json.loads((d / "metrics" / "consensus_metrics_true.json").read_text(encoding="utf-8"))
                probe.append(p_json["checkpoint_interval_ms_p95"])
                true_.append(t_json["checkpoint_interval_ms_p95_true"])
            except Exception:
                continue
        data[scen] = {"probe": probe, "true": true_}
    return data


def render(data) -> str:
    L = []
    L.append("# ckpt_interval_p95: probe-based metric vs log-derived truth")
    L.append("")
    L.append(f"- Generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    L.append("- probe metric: `consensus_metrics.json.checkpoint_interval_ms_p95` (averages over 14 rpc-probe windows)")
    L.append("- log-derived truth: `consensus_metrics_true.json.checkpoint_interval_ms_p95_true` (true per-checkpoint intervals)")
    L.append("- See `reports/ckpt_p95_layer_localization_report_20260525.md` for the measurement-pipeline failure mode")
    L.append("")
    L.append("| scenario | n | probe median | probe CV% | true median | true CV% | true/probe ratio |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for scen, _ in PLAN:
        probe = data[scen]["probe"]
        true_ = data[scen]["true"]
        if not probe or not true_:
            continue
        pm = nearest_rank(probe, 50)
        tm = nearest_rank(true_, 50)
        pcv = cv(probe)
        tcv = cv(true_)
        L.append(f"| {scen} | {len(probe)} | {pm:.1f} | {pcv:.2f} | {tm:.1f} | {tcv:.2f} | {tm/pm if pm else float('nan'):.2f} |")
    return "\n".join(L)


def plot(data, out_png: Path):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    labels = [scen for scen, _ in PLAN]
    probe_vals = [data[s]["probe"] for s in labels]
    true_vals = [data[s]["true"] for s in labels]

    axes[0].boxplot(probe_vals, labels=labels)
    axes[0].set_title("probe-based metric (consensus_metrics.json)")
    axes[0].set_ylabel("ckpt_interval_p95 (ms)")
    axes[0].tick_params(axis="x", rotation=20)

    axes[1].boxplot(true_vals, labels=labels)
    axes[1].set_title("log-derived truth (consensus_metrics_true.json)")
    axes[1].set_ylabel("ckpt_interval_p95_true (ms)")
    axes[1].tick_params(axis="x", rotation=20)

    plt.tight_layout()
    plt.savefig(out_png, dpi=144)
    plt.close()


def main():
    data = collect()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    report = REPORTS / f"variance_true_vs_probe_{ts}.md"
    figure = FIGURES / f"ckpt_p95_true_vs_probe_{ts}.png"
    report.write_text(render(data), encoding="utf-8")
    plot(data, figure)
    print(report)
    print(figure)


if __name__ == "__main__":
    main()
