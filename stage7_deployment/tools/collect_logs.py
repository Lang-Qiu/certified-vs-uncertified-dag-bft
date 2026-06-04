from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def classify(message: str) -> str:
    text = message.lower()
    if any(token in text for token in ("error", "warn", "warning", "panic", "failed", "failure")):
        return "warning_or_error"
    if "consensus" in text:
        return "consensus"
    if "checkpoint" in text:
        return "checkpoint"
    if any(token in text for token in ("transaction", "transactions", "tx ", "tx_digest")):
        return "transaction"
    return "other"


def iter_records(input_path: Path, experiment_label: str, captured_at: str):
    with input_path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            message = line.rstrip("\r\n")
            yield {
                "source": "real-deployment",
                "experiment_label": experiment_label,
                "captured_at": captured_at,
                "input_file": str(input_path),
                "line_no": line_no,
                "kind": classify(message),
                "message": message,
            }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Stage 7 real-deployment raw logs to JSONL events."
    )
    parser.add_argument("--input", required=True, help="Raw baseline log file.")
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument(
        "--experiment-label",
        default="baseline_local_validator",
        help="Experiment label to attach to each event.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    captured_at = datetime.now(timezone.utc).isoformat()
    records = list(iter_records(input_path, args.experiment_label, captured_at))

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(
        f"read {len(records)} lines from {input_path}; "
        f"wrote {len(records)} real-deployment records to {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
