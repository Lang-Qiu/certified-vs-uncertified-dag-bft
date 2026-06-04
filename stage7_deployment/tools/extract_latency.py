from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def iter_events(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL record") from exc
            if not isinstance(event, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            yield event


def summarize_events(events_path: Path) -> dict[str, Any]:
    kind_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    transaction_token_counts: Counter[str] = Counter()
    event_count = 0

    for event in iter_events(events_path):
        event_count += 1
        kind = str(event.get("kind", "unknown"))
        kind_counts[kind] += 1
        source_counts[str(event.get("source", "unknown"))] += 1
        message = str(event.get("message", "")).lower()
        if any(
            token in message
            for token in ("transaction", "transactions", "tx ", "tx_digest")
        ):
            transaction_token_counts[kind] += 1

    token_transaction_events = sum(transaction_token_counts.values())
    classification_warnings = []
    if token_transaction_events and kind_counts.get("transaction", 0) < token_transaction_events:
        classification_warnings.append(
            {
                "kind": "transaction-token-kind-mismatch",
                "message": (
                    "Some log records contain transaction markers but were classified "
                    "under other kinds, often because consensus module names include "
                    "transaction-related terms. Use transaction_token_counts as log "
                    "surface evidence, not as committed transaction throughput."
                ),
                "transaction_token_events": token_transaction_events,
                "kind_distribution": dict(sorted(transaction_token_counts.items())),
            }
        )

    return {
        "source": "real-deployment",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_events": str(events_path),
        "event_count": event_count,
        "kind_counts": dict(sorted(kind_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "observed_consensus_events": kind_counts.get("consensus", 0),
        "observed_checkpoint_events": kind_counts.get("checkpoint", 0),
        "observed_transaction_events": kind_counts.get("transaction", 0),
        "transaction_token_events": token_transaction_events,
        "transaction_token_counts": dict(sorted(transaction_token_counts.items())),
        "classification_warnings": classification_warnings,
        "latency_ms": {
            "samples": [],
            "mean": None,
            "median": None,
            "p95": None,
            "limitation": (
                "No reliable per-event commit/checkpoint duration is available in "
                "baseline_events.jsonl. Log timestamps show observation surface only; "
                "precise latency extraction requires upstream timestamp or duration "
                "instrumentation before computing latency statistics."
            ),
        },
        "interpretation": (
            "This file records real-deployment event coverage from the local Sui "
            "smoke run. It does not estimate consensus latency without instrumented "
            "duration fields."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize Stage 2 real-deployment events without fabricating latency."
    )
    parser.add_argument("--events", required=True, help="Input JSONL event file.")
    parser.add_argument("--output", required=True, help="Output summary JSON file.")
    args = parser.parse_args()

    events_path = Path(args.events)
    output_path = Path(args.output)

    summary = summarize_events(events_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output_path}")
    print(f"events={summary['event_count']} kinds={summary['kind_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
