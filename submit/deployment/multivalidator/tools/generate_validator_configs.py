"""Generate deterministic validator configuration records for Stage 7 runs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_VALIDATOR_COUNT = 7
DEFAULT_FAULT_TOLERANCE = 2
DEFAULT_SCENARIO = "baseline"
DEFAULT_REPEAT_INDEX = 1


def _slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or DEFAULT_SCENARIO


def stable_run_id(scenario: str, seed: int, repeat_index: int) -> str:
    return f"{_slug(scenario)}_seed{seed}_rep{repeat_index:02d}"


def _string_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def _validator_spec(run_root: Path, run_id: str, index: int) -> dict[str, Any]:
    config_dir = run_root / "config" / f"validator-{index}"
    db_path = run_root / "data" / f"validator-{index}" / "db"
    log_path = run_root / "logs" / f"validator-{index}" / "sui-node.log"

    return {
        "validator_index": index,
        "network_alias": f"validator-{index}",
        "container_name": f"{run_id}-validator-{index}",
        "config_dir": _string_path(config_dir),
        "config_path": _string_path(config_dir / "validator.yaml"),
        "db_path": _string_path(db_path),
        "log_path": _string_path(log_path),
        "fault_target_interface": "eth0",
        "ports": {
            "p2p": 8080 + index,
            "consensus": 8180 + index,
            "json_rpc": 9000 + index,
            "metrics": 9180 + index,
        },
        "pending_official_generation": {
            "validator_yaml": _string_path(config_dir / "validator.yaml"),
            "sui_key_material": None,
            "genesis_hash": None,
            "genesis_blob": None,
            "network_yaml": None,
            "note": "Populate these fields from official `sui genesis` output before running independent containers.",
        },
        "unsupported_fields": (
            "This generator does not fabricate Sui keys, genesis hashes, "
            "genesis.blob, network.yaml, validator.yaml, or fullnode.yaml; "
            "they must be produced by official sui genesis."
        ),
    }


def build_network_plan(
    *,
    seed: int,
    scenario: str = DEFAULT_SCENARIO,
    repeat_index: int = DEFAULT_REPEAT_INDEX,
    output_root: Path | str = Path("."),
    validators: int = DEFAULT_VALIDATOR_COUNT,
    fault_tolerance: int = DEFAULT_FAULT_TOLERANCE,
    run_id: str | None = None,
) -> dict[str, Any]:
    if validators <= 0:
        raise ValueError("validators must be positive")
    if fault_tolerance < 0:
        raise ValueError("fault_tolerance must be non-negative")

    resolved_run_id = run_id or stable_run_id(scenario, seed, repeat_index)
    root = Path(output_root)
    run_root = root / "data" / "runs" / resolved_run_id
    genesis_working_dir = run_root / "official-genesis"

    specs = [
        _validator_spec(run_root, resolved_run_id, index)
        for index in range(1, validators + 1)
    ]

    return {
        "schema_version": 1,
        "run_id": resolved_run_id,
        "seed": seed,
        "scenario": scenario,
        "repeat_index": repeat_index,
        "validator_count": validators,
        "fault_tolerance": fault_tolerance,
        "output_root": _string_path(root),
        "run_root": _string_path(run_root),
        "primary_evidence_layer": "independent_containers",
        "calibration_only_swarm_command": (
            f"sui start --committee-size {validators} "
            "--with-faucet=0.0.0.0:9123 --force-regenesis "
            "--fullnode-rpc-port 9000"
        ),
        "official_genesis_command": (
            f"sui genesis --committee-size {validators} "
            f"--working-dir {_string_path(genesis_working_dir)} "
            "--force --with-faucet"
        ),
        "official_execution_entrypoint": (
            "sui-node --config-path <validator-yaml>"
        ),
        "pending_official_generation": {
            "working_dir": _string_path(genesis_working_dir),
            "network_yaml": _string_path(genesis_working_dir / "network.yaml"),
            "genesis_blob": _string_path(genesis_working_dir / "genesis.blob"),
            "fullnode_yaml": _string_path(genesis_working_dir / "fullnode.yaml"),
            "validator_yamls": [
                spec["pending_official_generation"]["validator_yaml"]
                for spec in specs
            ],
            "note": "Run official sui genesis later; this file is only the deterministic input record.",
        },
        "validators": specs,
    }


def write_network_plan(plan: dict[str, Any]) -> Path:
    run_root = Path(plan["run_root"])
    run_root.mkdir(parents=True, exist_ok=True)

    for spec in plan["validators"]:
        spec_dir = Path(spec["config_dir"])
        spec_dir.mkdir(parents=True, exist_ok=True)
        spec_path = spec_dir / "validator_spec.json"
        spec_path.write_text(
            json.dumps(spec, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    plan_path = run_root / "network_plan.json"
    plan_path.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return plan_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic Stage 7 validator configuration records."
    )
    parser.add_argument("--run-id")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--repeat-index", type=int, default=DEFAULT_REPEAT_INDEX)
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--validators", type=int, default=DEFAULT_VALIDATOR_COUNT)
    parser.add_argument(
        "--fault-tolerance", type=int, default=DEFAULT_FAULT_TOLERANCE
    )
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_network_plan(
        seed=args.seed,
        scenario=args.scenario,
        repeat_index=args.repeat_index,
        output_root=args.output_root,
        validators=args.validators,
        fault_tolerance=args.fault_tolerance,
        run_id=args.run_id,
    )

    if args.write:
        plan_path = write_network_plan(plan)
        print(_string_path(plan_path))
    else:
        print(json.dumps(plan, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
