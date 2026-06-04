"""Compare per-checkpoint gap distributions across reps.

For 3 reps of two_validator_pressure:
  - rep01 (low metric p95 = 226)
  - rep08 (high metric p95 = 674)
  - rep10 (highest metric p95 = 1004)

parse fullnode `execute_checkpoint{seq=N}` lines, compute consecutive
intervals, and tabulate:
  - count of intervals
  - p50/p95/max of intervals
  - count of intervals > 2000 ms (epoch-boundary-like)
  - count of intervals in (500, 2000] ms (suspected fault-driven outliers)
  - count of intervals <= 500 ms (normal cadence)

This shows whether fault-driven outliers (500–2000ms) actually differ
between low-p95 and high-p95 reps.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSTATE_PARENT = ROOT / "data" / "runs"

REPS = ["rep01", "rep08", "rep09", "rep10"]
SCEN = "two_validator_pressure_seed2026052406"

LINE_TS = re.compile(r"^[\w:.\-]+\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(\w+)\s+(.*)$")
CKPT_SEQ = re.compile(r"execute_checkpoint\{seq=(\d+)\}")


def parse_iso(ts: str) -> datetime:
    ts = ts.rstrip("Z")
    if "." in ts:
        head, frac = ts.split(".")
        frac = (frac + "000000000")[:6]
        ts = f"{head}.{frac}"
    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)


def load_checkpoints(rep: str):
    rid = f"{SCEN}_{rep}"
    path = CSTATE_PARENT / rid / "evidence" / "container_state" / f"{rid}-fullnode.logs.txt"
    seqs = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
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
            seqs[seq] = parse_iso(ts_str)
    return seqs


def gaps(seqs):
    ordered = sorted(seqs)
    out = []
    for s, t in zip(ordered, ordered[1:]):
        if t == s + 1:
            out.append((seqs[t] - seqs[s]).total_seconds() * 1000.0)
    return out


def nearest_rank(values, p):
    if not values:
        return None
    s = sorted(values)
    r = max(1, int(p / 100 * len(s) + 0.999999999))
    return s[min(r, len(s)) - 1]


def main():
    print("rep | n_intervals | p50 | p95 | max | n_gt_2000ms | n_in_(500,2000] | n_le_500ms")
    print("-" * 95)
    for rep in REPS:
        seqs = load_checkpoints(rep)
        g = gaps(seqs)
        n_huge = sum(1 for x in g if x > 2000)
        n_mid = sum(1 for x in g if 500 < x <= 2000)
        n_low = sum(1 for x in g if x <= 500)
        print(f"{rep} | {len(g)} | {nearest_rank(g, 50):.1f} | "
              f"{nearest_rank(g, 95):.1f} | {max(g):.1f} | "
              f"{n_huge} | {n_mid} | {n_low}")


if __name__ == "__main__":
    main()
