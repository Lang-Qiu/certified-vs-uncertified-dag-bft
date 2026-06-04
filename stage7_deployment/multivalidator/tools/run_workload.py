import argparse
import json
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path


STATUS_PLANNED = "planned_not_submitted"
STATUS_SUBMITTED = "submitted"
STATUS_FAILED = "failed"


def _stable_ts(offset_ms):
    value = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
        milliseconds=offset_ms
    )
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def make_workload_event(run_id, event_type, payload):
    offset_ms = payload["scheduled_at_offset_ms"]
    return {
        "ts": _stable_ts(offset_ms),
        "run_id": run_id,
        "source": "workload",
        "event_type": event_type,
        "payload": payload,
        "evidence_ref": f"{run_id}/workload/{event_type}/{payload['sequence']}",
    }


def build_workload_client_config(
    source_text,
    *,
    container_rpc_url,
    container_keystore_path=None,
):
    text = source_text.replace("http://127.0.0.1:9000", container_rpc_url)
    if container_keystore_path:
        text = re.sub(
            r"(?m)^(\s*File:\s*).+$",
            lambda match: f"{match.group(1)}{container_keystore_path}",
            text,
            count=1,
        )
    return text


def parse_addresses(json_text):
    data = json.loads(json_text)
    if not isinstance(data, dict):
        return []
    addresses = []
    for entry in data.get("addresses", []):
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            addresses.append(entry[1])
        elif isinstance(entry, dict):
            value = entry.get("address")
            if value:
                addresses.append(value)
    return addresses


def parse_gas_objects(json_text):
    data = json.loads(json_text)
    if not isinstance(data, list):
        return []
    gas_objects = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        coin_id = entry.get("gasCoinId")
        balance = entry.get("mistBalance", 0)
        if not coin_id:
            continue
        try:
            balance = int(balance)
        except (TypeError, ValueError):
            balance = 0
        gas_objects.append((balance, coin_id))
    return [coin_id for _, coin_id in sorted(gas_objects, reverse=True)]


def build_docker_sui_client_command(
    *,
    data_root,
    run_id,
    image,
    network,
    client_config,
    client_args,
):
    del run_id
    volume = f"{Path(data_root).resolve()}:/mvdata"
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        network,
        "-v",
        volume,
        image,
        "sui",
        "client",
        "--client.config",
        client_config,
        "--json",
    ] + list(client_args)


def build_new_address_client_args(alias):
    return ["new-address", "ed25519", alias]


def _utc_now_text():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_actual_transaction_event(
    *,
    run_id,
    sequence,
    sender,
    recipient,
    gas_coin_id,
    amount_mist,
    gas_budget,
    latency_ms,
    exit_code,
    stdout,
    stderr,
):
    ok = exit_code == 0
    event_type = "tx_success" if ok else "tx_failed"
    status = STATUS_SUBMITTED if ok else STATUS_FAILED
    return {
        "ts": _utc_now_text(),
        "run_id": run_id,
        "source": "workload",
        "event_type": event_type,
        "payload": {
            "status": status,
            "sequence": sequence,
            "sender": sender,
            "recipient": recipient,
            "gas_coin_id": gas_coin_id,
            "amount_mist": amount_mist,
            "gas_budget": gas_budget,
            "latency_ms": latency_ms,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
        },
        "evidence_ref": f"{run_id}/workload/{event_type}/{sequence}",
    }


def make_workload_failure_event(*, run_id, error, phase="actual_transfer_initialization"):
    return {
        "ts": _utc_now_text(),
        "run_id": run_id,
        "source": "workload",
        "event_type": "workload_failed",
        "payload": {
            "status": STATUS_FAILED,
            "sequence": 0,
            "phase": phase,
            "error": str(error),
        },
        "evidence_ref": f"{run_id}/workload/workload_failed/0",
    }


def build_workload_events(run_id, seed, accounts=4, tps=1, duration_seconds=60):
    if accounts < 1:
        raise ValueError("accounts must be at least 1")
    if tps <= 0:
        raise ValueError("tps must be greater than 0")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be greater than 0")

    rng = random.Random(seed)
    account_names = [f"account-{index + 1}" for index in range(accounts)]
    tx_count = int(tps * duration_seconds)
    events = [
        make_workload_event(
            run_id,
            "workload_plan",
            {
                "status": STATUS_PLANNED,
                "seed": seed,
                "sequence": 0,
                "scheduled_at_offset_ms": 0,
                "accounts": accounts,
                "tps": tps,
                "duration_seconds": duration_seconds,
                "planned_transaction_count": tx_count,
                "note": "Plan only; no Sui CLI transaction submission performed.",
            },
        )
    ]

    interval_ms = int(1000 / tps)
    for index in range(tx_count):
        sender = rng.choice(account_names)
        if accounts == 1:
            recipient = sender
        else:
            recipient_choices = [name for name in account_names if name != sender]
            recipient = rng.choice(recipient_choices)
        amount = rng.randint(1, 1000)
        sequence = index + 1
        payload = {
            "status": STATUS_PLANNED,
            "seed": seed,
            "sequence": sequence,
            "scheduled_at_offset_ms": index * interval_ms,
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "operation": "transfer_sui_planned",
        }
        events.append(make_workload_event(run_id, "tx_submit_planned", payload))
    return events


def _run_command(command, timeout_seconds):
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout or ""
        stderr = exc.stderr or f"command timed out after {timeout_seconds}s"
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
    latency_ms = int((time.perf_counter() - started) * 1000)
    return exit_code, stdout, stderr, latency_ms


def _container_client_config_path(data_root, client_config_path):
    relative = client_config_path.relative_to(Path(data_root).resolve())
    return "/mvdata/" + relative.as_posix()


def _write_actual_client_config(data_root, run_id, output_dir, container_rpc_url):
    data_root = Path(data_root).resolve()
    official_config = data_root / "runs" / run_id / "official-genesis" / "client.yaml"
    official_keystore = data_root / "runs" / run_id / "official-genesis" / "sui.keystore"
    source_text = official_config.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    workload_keystore = output_dir / "sui.workload.keystore"
    workload_aliases = output_dir / "sui.workload.aliases"
    if workload_aliases.exists():
        workload_aliases.unlink()
    shutil.copy2(official_keystore, workload_keystore)
    client_config_path = output_dir / "client.actual.yaml"
    container_keystore_path = _container_client_config_path(
        data_root,
        workload_keystore.resolve(),
    )
    client_config_path.write_text(
        build_workload_client_config(
            source_text,
            container_rpc_url=container_rpc_url,
            container_keystore_path=container_keystore_path,
        ),
        encoding="utf-8",
    )
    return _container_client_config_path(data_root, client_config_path.resolve())


def _run_sui_client(
    *,
    data_root,
    run_id,
    image,
    network,
    client_config,
    client_args,
    timeout_seconds,
):
    command = build_docker_sui_client_command(
        data_root=data_root,
        run_id=run_id,
        image=image,
        network=network,
        client_config=client_config,
        client_args=client_args,
    )
    return _run_command(command, timeout_seconds)


def _require_success(label, result):
    exit_code, stdout, stderr, _latency_ms = result
    if exit_code != 0:
        raise RuntimeError(f"{label} failed with exit code {exit_code}: {stderr or stdout}")
    return stdout


def _load_addresses(
    *,
    data_root,
    run_id,
    image,
    network,
    client_config,
    timeout_seconds,
):
    addresses_stdout = _require_success(
        "sui client addresses",
        _run_sui_client(
            data_root=data_root,
            run_id=run_id,
            image=image,
            network=network,
            client_config=client_config,
            client_args=["addresses"],
            timeout_seconds=timeout_seconds,
        ),
    )
    return parse_addresses(addresses_stdout)


def _select_sender_recipient(
    *,
    data_root,
    run_id,
    image,
    network,
    client_config,
    timeout_seconds,
    gas_discovery_attempts=6,
    gas_discovery_interval_seconds=2,
):
    addresses = _load_addresses(
        data_root=data_root,
        run_id=run_id,
        image=image,
        network=network,
        client_config=client_config,
        timeout_seconds=timeout_seconds,
    )
    if len(addresses) < 2:
        _require_success(
            "sui client new-address",
            _run_sui_client(
                data_root=data_root,
                run_id=run_id,
                image=image,
                network=network,
                client_config=client_config,
                client_args=build_new_address_client_args("workload-recipient"),
                timeout_seconds=timeout_seconds,
            ),
        )
        addresses = _load_addresses(
            data_root=data_root,
            run_id=run_id,
            image=image,
            network=network,
            client_config=client_config,
            timeout_seconds=timeout_seconds,
        )
    if len(addresses) < 2:
        raise RuntimeError("actual-transfer mode requires at least two client addresses")

    attempts = max(1, int(gas_discovery_attempts))
    for attempt in range(attempts):
        for sender in addresses:
            gas_stdout = _require_success(
                f"sui client gas {sender}",
                _run_sui_client(
                    data_root=data_root,
                    run_id=run_id,
                    image=image,
                    network=network,
                    client_config=client_config,
                    client_args=["gas", sender],
                    timeout_seconds=timeout_seconds,
                ),
            )
            if parse_gas_objects(gas_stdout):
                recipient = next(address for address in addresses if address != sender)
                return sender, recipient
        if attempt + 1 < attempts and gas_discovery_interval_seconds > 0:
            time.sleep(gas_discovery_interval_seconds)
    raise RuntimeError(
        "no gas object found for any generated client address "
        f"after {attempts} discovery attempt(s)"
    )


def _select_gas_coin(
    *,
    data_root,
    run_id,
    image,
    network,
    client_config,
    sender,
    timeout_seconds,
):
    gas_stdout = _require_success(
        f"sui client gas {sender}",
        _run_sui_client(
            data_root=data_root,
            run_id=run_id,
            image=image,
            network=network,
            client_config=client_config,
            client_args=["gas", sender],
            timeout_seconds=timeout_seconds,
        ),
    )
    gas_objects = parse_gas_objects(gas_stdout)
    if not gas_objects:
        raise RuntimeError(f"no gas object found for sender {sender}")
    return gas_objects[0]


def run_actual_transfer_workload(
    *,
    run_id,
    seed,
    data_root,
    output,
    image,
    network=None,
    container_rpc_url="http://172.28.7.20:9000",
    tps=1,
    duration_seconds=60,
    amount_mist=1_000_000,
    gas_budget=10_000_000,
    timeout_seconds=60,
):
    if tps <= 0:
        raise ValueError("tps must be greater than 0")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be greater than 0")

    del seed
    output = Path(output)
    network = network or f"{run_id}_net"
    client_config = _write_actual_client_config(
        data_root=Path(data_root),
        run_id=run_id,
        output_dir=output.parent,
        container_rpc_url=container_rpc_url,
    )
    sender, recipient = _select_sender_recipient(
        data_root=data_root,
        run_id=run_id,
        image=image,
        network=network,
        client_config=client_config,
        timeout_seconds=timeout_seconds,
    )

    events = []
    tx_count = int(tps * duration_seconds)
    interval_seconds = 1 / tps
    next_started_at = time.perf_counter()
    for sequence in range(1, tx_count + 1):
        gas_coin_id = _select_gas_coin(
            data_root=data_root,
            run_id=run_id,
            image=image,
            network=network,
            client_config=client_config,
            sender=sender,
            timeout_seconds=timeout_seconds,
        )
        exit_code, stdout, stderr, latency_ms = _run_sui_client(
            data_root=data_root,
            run_id=run_id,
            image=image,
            network=network,
            client_config=client_config,
            client_args=[
                "transfer-sui",
                "--sender",
                sender,
                "--to",
                recipient,
                "--sui-coin-object-id",
                gas_coin_id,
                "--amount",
                str(amount_mist),
                "--gas-budget",
                str(gas_budget),
            ],
            timeout_seconds=timeout_seconds,
        )
        events.append(
            make_actual_transaction_event(
                run_id=run_id,
                sequence=sequence,
                sender=sender,
                recipient=recipient,
                gas_coin_id=gas_coin_id,
                amount_mist=amount_mist,
                gas_budget=gas_budget,
                latency_ms=latency_ms,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
            )
        )
        next_started_at += interval_seconds
        sleep_seconds = next_started_at - time.perf_counter()
        if sequence < tx_count and sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return events


def write_jsonl(events, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate an auditable workload plan or submit real Sui transfers."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--mode",
        choices=["plan", "actual-transfer"],
        default="plan",
    )
    parser.add_argument("--accounts", type=int, default=4)
    parser.add_argument("--tps", type=float, default=1)
    parser.add_argument("--duration-seconds", type=int, default=60)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--sui-image", default="stage7-sui:local")
    parser.add_argument("--docker-network")
    parser.add_argument("--container-rpc-url", default="http://172.28.7.20:9000")
    parser.add_argument("--amount-mist", type=int, default=1_000_000)
    parser.add_argument("--gas-budget", type=int, default=10_000_000)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.mode == "actual-transfer":
        if args.data_root is None:
            raise SystemExit("--data-root is required for --mode actual-transfer")
        try:
            events = run_actual_transfer_workload(
                run_id=args.run_id,
                seed=args.seed,
                data_root=args.data_root,
                output=args.output,
                image=args.sui_image,
                network=args.docker_network,
                container_rpc_url=args.container_rpc_url,
                tps=args.tps,
                duration_seconds=args.duration_seconds,
                amount_mist=args.amount_mist,
                gas_budget=args.gas_budget,
                timeout_seconds=args.timeout_seconds,
            )
        except Exception as exc:
            write_jsonl([make_workload_failure_event(run_id=args.run_id, error=exc)], args.output)
            print(f"actual-transfer workload failed: {exc}", file=sys.stderr)
            return 1
    else:
        events = build_workload_events(
            run_id=args.run_id,
            seed=args.seed,
            accounts=args.accounts,
            tps=args.tps,
            duration_seconds=args.duration_seconds,
        )
    write_jsonl(events, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
