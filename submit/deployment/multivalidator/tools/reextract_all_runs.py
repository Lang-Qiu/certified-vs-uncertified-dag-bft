"""Run extract_ckpt_metrics_from_logs.py on all 60 formal reps + any others.

Writes metrics/consensus_metrics_true.json into each rep dir. Also writes
a combined summary table summary_true_<ts>.csv / .md in reports/.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "runs"
TOOL = ROOT / "tools" / "extract_ckpt_metrics_from_logs.py"
REPORTS = ROOT / "reports"

PLAN = [
    ("baseline", "seed2026052402", 10),
    ("delay_low", "seed2026052402", 10),
    ("delay_high", "seed2026052402", 10),
    ("loss_low", "seed2026052402", 10),
    ("crash_one_validator", "seed2026052406", 10),
    ("two_validator_pressure", "seed2026052406", 10),
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


def run_one(rep_dir: Path):
    out = rep_dir / "metrics" / "consensus_metrics_true.json"
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--run-root", str(rep_dir), "--output", str(out)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return {"run_id": rep_dir.name, "error": proc.stderr.strip()}
    return json.loads(out.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extra-scenarios", nargs="*", default=[],
                        help="extra <scenario>_<seed> prefixes to include (auto-finds reps)")
    parser.add_argument("--report-name", default=None)
    args = parser.parse_args()

    targets = []
    for scen, seed, n in PLAN:
        for i in range(1, n + 1):
            rid = f"{scen}_{seed}_rep{i:02d}"
            targets.append(RUNS / rid)
    for extra in args.extra_scenarios:
        for d in sorted(RUNS.glob(f"{extra}_rep*")):
            targets.append(d)

    rows = []
    for t in targets:
        if not t.exists():
            rows.append({"run_id": t.name, "error": "missing"})
            continue
        rows.append(run_one(t))

    # per-scenario aggregate
    by_scen = {}
    for r in rows:
        if r.get("error"):
            continue
        by_scen.setdefault(r["scenario"], []).append(r)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    report_name = args.report_name or f"summary_true_{ts}.md"
    out_md = REPORTS / report_name
    L = []
    L.append("# True-cadence checkpoint summary (log-derived)")
    L.append("")
    L.append(f"- Generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    L.append(f"- Tool: tools/extract_ckpt_metrics_from_logs.py (parses execute_checkpoint{{seq=N}} from fullnode INFO log)")
    L.append(f"- Reps processed: {sum(1 for r in rows if not r.get('error'))} / {len(rows)}")
    L.append("")
    L.append("## Per-scenario aggregate (n=10)")
    L.append("")
    L.append("| scenario | p50_true median(ms) | p50_true CV% | p95_true median(ms) | p95_true CV% | max median | n_epoch_gaps median | n_mid_tail median |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for scen, rs in by_scen.items():
        p50s = [r["checkpoint_interval_ms_p50_true"] for r in rs]
        p95s = [r["checkpoint_interval_ms_p95_true"] for r in rs]
        maxs = [r["checkpoint_interval_ms_max_true"] for r in rs]
        ngaps = [r["n_intervals_gt_2000ms"] for r in rs]
        nmid = [r["n_intervals_500_to_2000ms"] for r in rs]
        L.append(f"| {scen} | {nearest_rank(p50s, 50):.1f} | {cv(p50s):.2f} | "
                 f"{nearest_rank(p95s, 50):.1f} | {cv(p95s):.2f} | "
                 f"{nearest_rank(maxs, 50):.1f} | {nearest_rank(ngaps, 50)} | "
                 f"{nearest_rank(nmid, 50)} |")
    L.append("")
    L.append("## Per-rep raw")
    L.append("")
    L.append("| scenario | rep | p50_true | p95_true | max | n_gt_2000 | n_500_2000 |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in rows:
        if r.get("error"):
            L.append(f"| {r['run_id']} | ERR | — | — | — | — | — |")
            continue
        L.append(f"| {r['scenario']} | {r['repeat_index']} | "
                 f"{r['checkpoint_interval_ms_p50_true']:.1f} | "
                 f"{r['checkpoint_interval_ms_p95_true']:.1f} | "
                 f"{r['checkpoint_interval_ms_max_true']:.1f} | "
                 f"{r['n_intervals_gt_2000ms']} | "
                 f"{r['n_intervals_500_to_2000ms']} |")
    out_md.write_text("\n".join(L), encoding="utf-8")
    print(out_md)


if __name__ == "__main__":
    main()
