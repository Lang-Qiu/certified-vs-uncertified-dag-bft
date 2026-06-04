"""Extract per-checkpoint interval metrics from fullnode INFO logs.

Why this exists (separate from extract_consensus_metrics.py)
------------------------------------------------------------
extract_consensus_metrics.py derives `checkpoint_interval_ms_p50/p95` by
averaging across rpc_probe windows (15 anchors / rep, 2-second probe cadence,
average = time_delta_ms / seq_delta). That metric is dominated by how rpc
probe ticks align with 60-second epoch boundary CheckpointBuilder pauses,
not by per-checkpoint cadence. See `reports/ckpt_p95_layer_localization_report_20260525.md`.

This tool parses `evidence/container_state/<run_id>-fullnode.logs.txt` for
`execute_checkpoint{seq=N}` events, computes true consecutive intervals at
millisecond precision, and writes a separate sidecar `consensus_metrics_true.json`.
It does NOT overwrite the existing `consensus_metrics.json`, so the original
manifest hash chain stays valid.

Fields written
--------------
  run_id, scenario, repeat_index
  checkpoint_count_true              — count of unique seq values parsed
  checkpoint_interval_ms_p50_true    — true median of consecutive intervals
  checkpoint_interval_ms_p95_true    — true p95 (nearest-rank C=1)
  checkpoint_interval_ms_max_true    — max
  checkpoint_interval_ms_min_true    — min
  n_intervals_gt_2000ms              — count of intervals > 2000 ms (epoch boundary class)
  n_intervals_500_to_2000ms          — count of (500, 2000]
  n_intervals_le_500ms               — count of <= 500 ms
  epoch_boundary_gaps_ms             — list of intervals > 2000 ms
  source_log_path                    — relative path of parsed log
  notes                              — fixed string describing the C=1 percentile convention
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

LINE_TS = re.compile(r"^[\w:.\-]+\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(\w+)\s+(.*)$")
CKPT_SEQ = re.compile(r"execute_checkpoint\{seq=(\d+)\}")


def parse_iso(ts: str) -> datetime:
    ts = ts.rstrip("Z")
    if "." in ts:
        head, frac = ts.split(".")
        frac = (frac + "000000000")[:6]
        ts = f"{head}.{frac}"
    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)


def nearest_rank(values, percentile):
    """Nearest-rank percentile, C=1 convention (matches summarize_runs.py)."""
    if not values:
        return None
    s = sorted(values)
    rank = max(1, int(percentile / 100.0 * len(s) + 0.999999999))
    return s[min(rank, len(s)) - 1]


def collect_intervals(log_path: Path):
    seqs = {}
    with log_path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            mt = LINE_TS.match(line.strip())
            if not mt:
                continue
            ts_str, _, payload = mt.groups()
            ms = CKPT_SEQ.search(payload)
            if not ms:
                continue
            seq = int(ms.group(1))
            if seq in seqs:
                continue
            try:
                seqs[seq] = parse_iso(ts_str)
            except Exception:
                continue
    ordered = sorted(seqs)
    intervals = []
    for s, t in zip(ordered, ordered[1:]):
        if t == s + 1:
            intervals.append((seqs[t] - seqs[s]).total_seconds() * 1000.0)
    return seqs, intervals


def extract(run_root: Path):
    rid = run_root.name
    log_path = run_root / "evidence" / "container_state" / f"{rid}-fullnode.logs.txt"
    early_log_path = run_root / "evidence" / "early_logs" / f"{rid}-fullnode.logs.txt"
    if not log_path.exists():
        if early_log_path.exists():
            log_path = early_log_path
        else:
            return {
                "run_id": rid,
                "error": f"missing fullnode log: {log_path} (also tried {early_log_path})",
            }
    seqs, intervals = collect_intervals(log_path)

    record = run_root / "controller_record.json"
    scenario, repeat_index = None, None
    if record.exists():
        try:
            data = json.loads(record.read_text(encoding="utf-8-sig"))
            scenario = data.get("scenario")
            repeat_index = data.get("repeat_index")
        except Exception:
            pass

    n_huge = sum(1 for x in intervals if x > 2000)
    n_mid = sum(1 for x in intervals if 500 < x <= 2000)
    n_low = sum(1 for x in intervals if x <= 500)

    return {
        "run_id": rid,
        "scenario": scenario,
        "repeat_index": repeat_index,
        "checkpoint_count_true": len(seqs),
        "n_intervals": len(intervals),
        "checkpoint_interval_ms_min_true": min(intervals) if intervals else None,
        "checkpoint_interval_ms_p50_true": nearest_rank(intervals, 50),
        "checkpoint_interval_ms_p95_true": nearest_rank(intervals, 95),
        "checkpoint_interval_ms_max_true": max(intervals) if intervals else None,
        "n_intervals_gt_2000ms": n_huge,
        "n_intervals_500_to_2000ms": n_mid,
        "n_intervals_le_500ms": n_low,
        "epoch_boundary_gaps_ms": sorted([round(x, 1) for x in intervals if x > 2000],
                                         reverse=True),
        "source_log_path": str(log_path.relative_to(run_root)),
        "notes": "nearest-rank percentile C=1; parsed from execute_checkpoint{seq=N} INFO log lines",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-root", required=True)
    p.add_argument("--output", required=True,
                   help="Output sidecar JSON (e.g. metrics/consensus_metrics_true.json)")
    args = p.parse_args()
    run_root = Path(args.run_root)
    out = extract(run_root)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
