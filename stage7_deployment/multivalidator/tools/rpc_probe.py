import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_METHODS = (
    "sui_getLatestCheckpointSequenceNumber",
    "sui_getTotalTransactionBlocks",
)


def _isoformat(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_rpc_payload(method, params=None, request_id=1):
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
    }
    if params is not None:
        payload["params"] = params
    return payload


def classify_rpc_response(text):
    try:
        response = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, f"invalid_json: {exc.msg}"

    if not isinstance(response, dict):
        return False, "invalid_response: expected JSON object"
    if "error" in response:
        error = response["error"]
        if isinstance(error, dict):
            message = error.get("message") or json.dumps(error, sort_keys=True)
            code = error.get("code")
            if code is not None:
                return False, f"rpc_error {code}: {message}"
            return False, f"rpc_error: {message}"
        return False, f"rpc_error: {error}"
    if "result" in response:
        return True, ""
    return False, "invalid_response: missing result or error"


def make_event(
    run_id,
    endpoint,
    method,
    started_at,
    ended_at,
    ok,
    response_text="",
    error="",
):
    latency_ms = max(0, int((ended_at - started_at).total_seconds() * 1000))
    event_type = "rpc_ok" if ok else "rpc_error"
    ts = _isoformat(ended_at)
    payload = {
        "endpoint": endpoint,
        "method": method,
        "latency_ms": latency_ms,
        "ok": bool(ok),
        "response_text": response_text,
        "error": error,
    }
    return {
        "ts": ts,
        "run_id": run_id,
        "source": "rpc_probe",
        "validator": None,
        "event_type": event_type,
        "payload": payload,
        "evidence_ref": f"{run_id}/rpc_probe/{event_type}/{method}/{ts}",
    }


def post_rpc(endpoint, method, request_id, timeout_seconds=5):
    payload = build_rpc_payload(method, request_id=request_id)
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="replace")


def write_jsonl(events, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def run_probe(run_id, endpoints, methods, interval_seconds, samples):
    events = []
    request_id = 1
    for sample_index in range(samples):
        for endpoint in endpoints:
            for method in methods:
                started_at = datetime.now(timezone.utc)
                response_text = ""
                error = ""
                ok = False
                try:
                    response_text = post_rpc(endpoint, method, request_id)
                    ok, error = classify_rpc_response(response_text)
                except (urllib.error.URLError, TimeoutError, OSError) as exc:
                    error = f"transport_error: {exc}"
                ended_at = datetime.now(timezone.utc)
                events.append(
                    make_event(
                        run_id=run_id,
                        endpoint=endpoint,
                        method=method,
                        started_at=started_at,
                        ended_at=ended_at,
                        ok=ok,
                        response_text=response_text,
                        error=error,
                    )
                )
                request_id += 1
        if sample_index < samples - 1 and interval_seconds > 0:
            time.sleep(interval_seconds)
    return events


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Probe Sui JSON-RPC endpoints.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--endpoint", action="append", required=True)
    parser.add_argument(
        "--methods",
        default=",".join(DEFAULT_METHODS),
        help="Comma-separated JSON-RPC methods to call.",
    )
    parser.add_argument("--interval-seconds", type=float, default=5.0)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    methods = [method.strip() for method in args.methods.split(",") if method.strip()]
    events = run_probe(
        run_id=args.run_id,
        endpoints=args.endpoint,
        methods=methods,
        interval_seconds=args.interval_seconds,
        samples=args.samples,
    )
    write_jsonl(events, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
