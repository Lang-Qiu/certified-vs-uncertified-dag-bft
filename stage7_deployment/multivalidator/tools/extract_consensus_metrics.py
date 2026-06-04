#!/usr/bin/env python
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


METRIC_FIELDS = [
    "run_id",
    "scenario",
    "repeat_index",
    "validator_count",
    "fault_tolerance",
    "successful_transactions",
    "failed_transactions",
    "checkpoint_count",
    "checkpoint_interval_ms_p50",
    "checkpoint_interval_ms_p95",
    "rpc_latency_ms_p50",
    "rpc_latency_ms_p95",
    "recovery_time_ms",
    "availability_ratio",
    "primary_evidence_layer",
    "unsupported_fields",
]


def _read_jsonl(path):
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                yield value


def _iter_jsonl_events(run_root):
    for path in sorted(Path(run_root).rglob("*.jsonl")):
        for event in _read_jsonl(path):
            yield path, event


def _iter_container_state_logs(run_root):
    run_root = Path(run_root)
    for path in sorted(run_root.rglob("*")):
        if not path.is_file():
            continue
        parts = {part.lower() for part in path.parts}
        if "container_state" not in parts:
            continue
        if path.suffix.lower() not in {".log", ".txt"}:
            continue
        yield path


def _nearest_rank(values, percentile):
    if not values:
        return None
    ordered = sorted(values)
    rank = int((percentile / 100) * len(ordered) + 0.999999999)
    rank = min(max(rank, 1), len(ordered))
    return ordered[rank - 1]


def _parse_event_time(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _json_rpc_result_int(response_text):
    if not isinstance(response_text, str) or not response_text.strip():
        return None
    try:
        response = json.loads(response_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(response, dict):
        return None
    value = response.get("result")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _metadata_from_run_root(run_root):
    name = Path(run_root).name
    metadata = {
        "run_id": name or None,
        "scenario": None,
        "repeat_index": None,
        "validator_count": None,
        "fault_tolerance": None,
    }
    for candidate in ("run_metadata.json", "metadata.json", "network_plan.json"):
        path = Path(run_root) / candidate
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        for field in metadata:
            if field in data:
                metadata[field] = data[field]
    return metadata


def _unsupported(metrics, reasons):
    return {field: reason for field, reason in reasons.items() if metrics.get(field) is None}


def extract_metrics(run_root):
    run_root = Path(run_root)
    metrics = {
        "run_id": None,
        "scenario": None,
        "repeat_index": None,
        "validator_count": None,
        "fault_tolerance": None,
        "successful_transactions": 0,
        "failed_transactions": 0,
        "checkpoint_count": None,
        "checkpoint_interval_ms_p50": None,
        "checkpoint_interval_ms_p95": None,
        "rpc_latency_ms_p50": None,
        "rpc_latency_ms_p95": None,
        "recovery_time_ms": None,
        "availability_ratio": None,
        "primary_evidence_layer": None,
        "unsupported_fields": {},
    }
    metrics.update(_metadata_from_run_root(run_root))

    rpc_latencies = []
    checkpoint_intervals = []
    checkpoint_count = None
    checkpoint_samples = []
    availability_samples = []
    recovery_time_ms = None
    evidence_layers = set()

    for path, event in _iter_jsonl_events(run_root):
        relative = path.relative_to(run_root)
        if relative.parts:
            if relative.parts[0] == "evidence" and len(relative.parts) > 1:
                evidence_layers.add(relative.parts[1])
            else:
                evidence_layers.add(relative.parts[0])
        if event.get("run_id") and (not metrics["run_id"] or metrics["run_id"] == run_root.name):
            metrics["run_id"] = event["run_id"]

        source = event.get("source")
        event_type = event.get("event_type")
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}

        if source == "rpc_probe" and event_type == "rpc_ok":
            latency = payload.get("latency_ms")
            if isinstance(latency, (int, float)):
                rpc_latencies.append(latency)
            availability_samples.append(True)
            if payload.get("method") == "sui_getLatestCheckpointSequenceNumber":
                value = _json_rpc_result_int(payload.get("response_text"))
                event_time = _parse_event_time(event.get("ts"))
                if value is not None:
                    checkpoint_count = max(checkpoint_count or value, value)
                    if event_time is not None:
                        checkpoint_samples.append((event_time, value))
        elif source == "rpc_probe" and event_type == "rpc_error":
            availability_samples.append(False)

        if source == "workload":
            if event_type in {"tx_success", "transaction_success", "tx_commit"}:
                metrics["successful_transactions"] += 1
            elif event_type in {"tx_failed", "transaction_failed", "tx_error", "workload_failed"}:
                metrics["failed_transactions"] += 1

        if source == "fault_timeline":
            if event_type in {"recovery_complete", "validator_recovered"}:
                value = payload.get("recovery_time_ms")
                if isinstance(value, (int, float)):
                    recovery_time_ms = value

        if event_type in {"checkpoint", "checkpoint_created"}:
            checkpoint_count = (checkpoint_count or 0) + 1
            interval = payload.get("interval_ms")
            if isinstance(interval, (int, float)):
                checkpoint_intervals.append(interval)
        elif event_type == "checkpoint_summary":
            value = payload.get("checkpoint_count")
            if isinstance(value, int):
                checkpoint_count = value

    for (previous_time, previous_seq), (current_time, current_seq) in zip(
        checkpoint_samples,
        checkpoint_samples[1:],
    ):
        seq_delta = current_seq - previous_seq
        time_delta_ms = int((current_time - previous_time).total_seconds() * 1000)
        if seq_delta > 0 and time_delta_ms >= 0:
            checkpoint_intervals.append(int(time_delta_ms / seq_delta))

    for path in _iter_container_state_logs(run_root):
        evidence_layers.add("container_state")

    metrics["rpc_latency_ms_p50"] = _nearest_rank(rpc_latencies, 50)
    metrics["rpc_latency_ms_p95"] = _nearest_rank(rpc_latencies, 95)
    if checkpoint_count is not None:
        metrics["checkpoint_count"] = checkpoint_count
    metrics["checkpoint_interval_ms_p50"] = _nearest_rank(checkpoint_intervals, 50)
    metrics["checkpoint_interval_ms_p95"] = _nearest_rank(checkpoint_intervals, 95)
    metrics["recovery_time_ms"] = recovery_time_ms
    if availability_samples:
        metrics["availability_ratio"] = sum(1 for sample in availability_samples if sample) / len(
            availability_samples
        )
    if evidence_layers:
        metrics["primary_evidence_layer"] = ",".join(sorted(evidence_layers))

    metrics["unsupported_fields"] = _unsupported(
        metrics,
        {
            "checkpoint_count": "no checkpoint events or checkpoint summary found",
            "checkpoint_interval_ms_p50": "no checkpoint interval_ms values found",
            "checkpoint_interval_ms_p95": "no checkpoint interval_ms values found",
            "rpc_latency_ms_p50": "no rpc_probe rpc_ok payload.latency_ms values found",
            "rpc_latency_ms_p95": "no rpc_probe rpc_ok payload.latency_ms values found",
            "recovery_time_ms": "no fault_timeline recovery event with recovery_time_ms found",
            "availability_ratio": "no rpc_probe rpc_ok/rpc_error samples found",
            "scenario": "no run metadata scenario found",
            "repeat_index": "no run metadata repeat_index found",
            "validator_count": "no run metadata validator_count found",
            "fault_tolerance": "no run metadata fault_tolerance found",
            "primary_evidence_layer": "no JSONL evidence files found",
        },
    )
    return metrics


def write_json(metrics, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(metrics, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS)
        writer.writeheader()
        row = dict(metrics)
        row["unsupported_fields"] = json.dumps(row["unsupported_fields"], ensure_ascii=False, sort_keys=True)
        writer.writerow(row)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Extract consensus metrics from run evidence.")
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    metrics = extract_metrics(args.run_root)
    write_json(metrics, args.output_json)
    write_csv(metrics, args.output_csv)
    print(f"wrote metrics: {args.output_json} {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
