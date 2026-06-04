"""Localize long checkpoint intervals from existing sui-node logs.

Parse fullnode's `execute_checkpoint{seq=N}` log lines to build the
per-checkpoint timeline for two_validator_pressure rep10, then identify
the top-K longest gaps and look in validator-1 (netem delay) and
validator-2 (netem loss) logs at those windows for layer signals.

Output: a markdown table of the long-gap events + heuristic layer
attribution.
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "data" / "runs" / "two_validator_pressure_seed2026052406_rep10"
CSTATE = RUN / "evidence" / "container_state"
REPORT_DIR = ROOT / "reports"

# fullnode line shape (Docker --timestamps prefix then sui-node line):
#   2026-05-24T12:44:11.575360030Z 2026-05-24T12:44:11.575104Z  INFO execute_checkpoint{seq=2}: ...
LINE_TS = re.compile(r"^[\w:.\-]+\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(\w+)\s+(.*)$")
CKPT_SEQ = re.compile(r"execute_checkpoint\{seq=(\d+)\}")

# Validator-side checkpoint creation marker (the certified path):
# `Recording certified checkpoint` / `Built checkpoint`
VAL_CKPT = re.compile(r"checkpoint.*sequence_number=(\d+)|Recording certified checkpoint")

# Categorical patterns to bucket per-validator activity inside a gap window.
LAYER_PATTERNS = {
    "consensus_round": re.compile(r"consensus_handler|commit_subdag|new_round|leader_schedule"),
    "mysticeti_block": re.compile(r"mysticeti|new_block|block_proposed|block_committed", re.I),
    "rbc_certify":     re.compile(r"certificate|certified.*broadcast|aggregator", re.I),
    "checkpoint_builder": re.compile(r"checkpoint_builder|CheckpointBuilder|Built (a )?checkpoint", re.I),
    "narwhal_dag":     re.compile(r"narwhal|primary|worker_message", re.I),
    "warn_or_error":   re.compile(r"\bWARN\b|\bERROR\b"),
    "network_io":      re.compile(r"connection|peer.*disconnect|timed out|deadline|stalled", re.I),
}

K_TOP_GAPS = 10


def parse_iso(ts: str) -> datetime:
    # Handle Z suffix and nanosecond precision.
    ts = ts.rstrip("Z")
    if "." in ts:
        head, frac = ts.split(".")
        frac = (frac + "000000000")[:6]
        ts = f"{head}.{frac}"
    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)


def load_fullnode_checkpoints():
    path = CSTATE / f"{RUN.name}-fullnode.logs.txt"
    seq_to_ts = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            mt = LINE_TS.match(line.strip())
            if not mt:
                continue
            ts_str, _level, payload = mt.groups()
            ms = CKPT_SEQ.search(payload)
            if not ms:
                continue
            seq = int(ms.group(1))
            if seq in seq_to_ts:
                continue
            seq_to_ts[seq] = parse_iso(ts_str)
    return seq_to_ts


def compute_gaps(seq_to_ts):
    seqs = sorted(seq_to_ts)
    gaps = []
    prev = None
    for s in seqs:
        ts = seq_to_ts[s]
        if prev is not None:
            ps, pts = prev
            if s == ps + 1:
                gap_ms = (ts - pts).total_seconds() * 1000.0
                gaps.append({
                    "from_seq": ps, "to_seq": s,
                    "from_ts": pts, "to_ts": ts,
                    "gap_ms": gap_ms,
                })
        prev = (s, ts)
    return gaps


def scan_validator_window(val_path: Path, t_lo: datetime, t_hi: datetime,
                          counts: dict):
    with val_path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            mt = LINE_TS.match(line.strip())
            if not mt:
                continue
            ts_str, _level, payload = mt.groups()
            try:
                ts = parse_iso(ts_str)
            except Exception:
                continue
            if ts < t_lo or ts > t_hi:
                continue
            for label, pat in LAYER_PATTERNS.items():
                if pat.search(payload):
                    counts[label] += 1


def analyze_gap(gap, validators=("validator-1", "validator-2", "validator-3")):
    # widen window: 200 ms before and after
    from datetime import timedelta
    lo = gap["from_ts"] - timedelta(milliseconds=200)
    hi = gap["to_ts"] + timedelta(milliseconds=200)
    out = {}
    for v in validators:
        counts = defaultdict(int)
        scan_validator_window(CSTATE / f"{RUN.name}-{v}.logs.txt", lo, hi, counts)
        out[v] = dict(counts)
    return out


def render(seq_to_ts, gaps, gap_attribs) -> str:
    L = []
    L.append("# Checkpoint long-gap localization — two_validator_pressure rep10")
    L.append("")
    L.append(f"- Generated (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    L.append(f"- Source: existing INFO-level sui-node logs from rep10 evidence/container_state/")
    L.append(f"- Fullnode checkpoint events parsed: {len(seq_to_ts)}")
    L.append(f"- Consecutive (seq, seq+1) intervals analysed: {len(gaps)}")
    if gaps:
        gm = sorted(g["gap_ms"] for g in gaps)
        p50 = gm[len(gm) // 2]
        p95_rank = max(1, int(0.95 * len(gm) + 0.999999999)) - 1
        L.append(f"- Gap distribution (ms): min={min(gm):.1f}, p50={p50:.1f}, p95={gm[p95_rank]:.1f}, max={max(gm):.1f}")
    L.append("")
    L.append(f"## Top {K_TOP_GAPS} longest checkpoint gaps")
    L.append("")
    L.append("| rank | from_seq | to_seq | gap_ms | from_ts (UTC) |")
    L.append("| ---: | ---: | ---: | ---: | --- |")
    top = sorted(gaps, key=lambda g: -g["gap_ms"])[:K_TOP_GAPS]
    for i, g in enumerate(top, 1):
        L.append(f"| {i} | {g['from_seq']} | {g['to_seq']} | {g['gap_ms']:.1f} | {g['from_ts'].isoformat(timespec='milliseconds')} |")
    L.append("")
    L.append("## Per-validator activity counts during each long-gap window")
    L.append("(window = [from_ts - 200ms, to_ts + 200ms]; counts are log-line matches per layer pattern)")
    L.append("")
    layer_keys = list(LAYER_PATTERNS.keys())
    val_keys = sorted(next(iter(gap_attribs.values())).keys()) if gap_attribs else []
    for i, g in enumerate(top, 1):
        L.append(f"### Gap #{i}: seq {g['from_seq']}→{g['to_seq']}, {g['gap_ms']:.1f} ms")
        attribs = gap_attribs[(g['from_seq'], g['to_seq'])]
        header = "| validator | " + " | ".join(layer_keys) + " |"
        sep = "| --- | " + " | ".join(["---:" for _ in layer_keys]) + " |"
        L.append(header)
        L.append(sep)
        for v in val_keys:
            counts = attribs[v]
            row = "| " + v + " | " + " | ".join(str(counts.get(k, 0)) for k in layer_keys) + " |"
            L.append(row)
        L.append("")
    return "\n".join(L)


def main():
    seq_to_ts = load_fullnode_checkpoints()
    gaps = compute_gaps(seq_to_ts)
    top = sorted(gaps, key=lambda g: -g["gap_ms"])[:K_TOP_GAPS]
    gap_attribs = {}
    for g in top:
        gap_attribs[(g['from_seq'], g['to_seq'])] = analyze_gap(g)
    body = render(seq_to_ts, gaps, gap_attribs)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out = REPORT_DIR / f"ckpt_p95_layer_localization_{ts}.md"
    out.write_text(body, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
