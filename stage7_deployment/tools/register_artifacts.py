from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRIMARY_BASELINE_LOG = "baseline_20260523_141516.log"
SUI_COMMIT = "62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a"


def normalize_path(path: Path) -> str:
    return path.as_posix()


def repo_relative(root: Path, path: Path) -> str:
    return normalize_path(path.resolve().relative_to(root.resolve()))


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def file_facts(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "sha256": sha256_file(path),
        "bytes": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def repo_sha(repo_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return SUI_COMMIT


def load_manifest(path: Path) -> dict[str, Any]:
    if path.exists():
        return read_json(path)
    return {"schema_version": 1, "stage": "stage7_deployment", "entries": []}


def upsert_by_path(entries: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    path = entry["path"]
    for index, existing in enumerate(entries):
        if existing.get("path") == path:
            unchanged = all(
                existing.get(key) == entry.get(key)
                for key in ("sha256", "bytes", "mtime")
            )
            if unchanged and "registered_at" in existing:
                entry["registered_at"] = existing["registered_at"]
            merged = {**existing, **entry}
            entries[index] = merged
            return
    entries.append(entry)


def artifact_entry(
    root: Path,
    path: Path,
    *,
    source: str,
    artifact_type: str,
    experiment_label: str,
    paper_mapping: str,
    claim_boundary: str,
    notes: str,
    generated_by: str,
    generated_from: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rel_path = repo_relative(root, path)
    entry: dict[str, Any] = {
        "source": source,
        "artifact_type": artifact_type,
        "experiment_label": experiment_label,
        "path": rel_path,
        **file_facts(path),
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": generated_by,
        "paper_mapping": paper_mapping,
        "claim_boundary": claim_boundary,
        "notes": notes,
    }
    if generated_from is not None:
        entry["generated_from"] = generated_from
    if extra:
        entry.update(extra)
    return entry


def build_entries(root: Path, sui_dir: Path) -> list[dict[str, Any]]:
    raw_dir = root / "stage7_deployment" / "data" / "raw"
    derived_dir = root / "stage7_deployment" / "data" / "derived"
    report_dir = root / "stage7_deployment" / "reports"

    baseline_log = raw_dir / PRIMARY_BASELINE_LOG
    baseline_events = derived_dir / "baseline_events.jsonl"
    latency_summary = derived_dir / "baseline_latency_summary.json"
    calibration = derived_dir / "stage1_stage2_calibration.json"
    fault_log = raw_dir / "fault_restart_smoke.log"
    findings = report_dir / "phase2_findings_summary.md"

    required = [
        baseline_log,
        baseline_events,
        latency_summary,
        calibration,
        fault_log,
        findings,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required artifacts: " + ", ".join(missing))

    commit = repo_sha(sui_dir)
    common_boundary = (
        "Stage 2 real-deployment evidence only; it does not isolate the "
        "certification variable and is not a multi-validator consensus result."
    )
    baseline_from = repo_relative(root, baseline_log)
    events_from = repo_relative(root, baseline_events)
    latency = read_json(latency_summary)
    calibration_json = read_json(calibration)

    return [
        artifact_entry(
            root,
            baseline_log,
            source="real-deployment",
            artifact_type="raw-log",
            experiment_label="baseline_local_validator",
            paper_mapping="Stage 2 baseline local real-protocol smoke evidence; later review material for sections 7.1-7.2 and 10.",
            claim_boundary=common_boundary,
            notes=(
                "Primary baseline log from single-container `sui start --with-faucet "
                "--force-regenesis`; explicitly not fault_restart_smoke.log."
            ),
            generated_by="stage7_deployment/scripts/run_local_testnet.ps1",
            extra={
                "parameters": {
                    "target_repo": "https://github.com/MystenLabs/sui.git",
                    "target_commit": commit,
                    "service": "sui-local",
                    "command": "sui start --with-faucet --force-regenesis",
                }
            },
        ),
        artifact_entry(
            root,
            baseline_events,
            source="real-deployment",
            artifact_type="derived-jsonl-events",
            experiment_label="baseline_local_validator",
            paper_mapping="Stage 2 real-protocol log coverage evidence; later review material for sections 7.1-7.2 and 10.",
            claim_boundary=common_boundary,
            notes="JSONL conversion of the primary baseline log; records log surface, not committed throughput.",
            generated_by="stage7_deployment/tools/collect_logs.py",
            generated_from=baseline_from,
            extra={"record_count": line_count(baseline_events)},
        ),
        artifact_entry(
            root,
            latency_summary,
            source="real-deployment",
            artifact_type="derived-json",
            experiment_label="baseline_local_validator",
            paper_mapping="Stage 2 latency extraction and Stage 1 calibration input.",
            claim_boundary=common_boundary,
            notes=(
                "Latency samples are intentionally empty because reliable commit/checkpoint "
                "duration fields are not present. Transaction-token warnings are log-surface "
                "evidence, not committed throughput."
            ),
            generated_by="stage7_deployment/tools/extract_latency.py",
            generated_from=events_from,
            extra={
                "record_count": latency.get("event_count"),
                "observed_consensus_events": latency.get("observed_consensus_events"),
                "observed_checkpoint_events": latency.get("observed_checkpoint_events"),
                "observed_transaction_events": latency.get("observed_transaction_events"),
                "transaction_token_events": latency.get("transaction_token_events"),
                "latency_samples": len(latency.get("latency_ms", {}).get("samples", [])),
            },
        ),
        artifact_entry(
            root,
            calibration,
            source="stage1-stage2-calibration",
            artifact_type="derived-json",
            experiment_label="baseline_local_validator",
            paper_mapping="Stage 1/Stage 2 calibration boundary record; later review material for sections 7.1-7.2 and 10.",
            claim_boundary=common_boundary,
            notes=(
                "Compares Stage 2 real-deployment baseline evidence with Stage 6 "
                "simulation metadata while preserving the honest boundary."
            ),
            generated_by="stage7_deployment/tools/calibrate_stage6.py",
            generated_from=repo_relative(root, latency_summary),
            extra={
                "stage6_manifest": calibration_json.get("stage6_manifest_path"),
                "limits": calibration_json.get("limits"),
            },
        ),
        artifact_entry(
            root,
            fault_log,
            source="real-deployment",
            artifact_type="raw-log",
            experiment_label="fault_restart_smoke",
            paper_mapping="Stage 2 fault-injection recovery/log capture smoke evidence.",
            claim_boundary=common_boundary,
            notes=(
                "Single-container restart smoke log with netem/process-fault coverage; "
                "use as recovery/log-capture evidence only."
            ),
            generated_by="stage7_deployment/scripts/kill_validator.ps1; docker logs stage7-sui-local --since 5m",
            extra={
                "parameters": {
                    "target_repo": "https://github.com/MystenLabs/sui.git",
                    "target_commit": commit,
                    "netem_injection": "verified in Stage 2 smoke scope",
                }
            },
        ),
        artifact_entry(
            root,
            findings,
            source="real-deployment",
            artifact_type="findings-report",
            experiment_label="phase2_findings_package",
            paper_mapping="Stage 3 approval material only; not directly inserted into the paper.",
            claim_boundary=common_boundary,
            notes=(
                "Chinese findings summary for approval before any Stage 3 paper "
                "integration. It must not be treated as already approved paper text."
            ),
            generated_by="stage7_deployment/tools/register_artifacts.py",
        ),
    ]


def update_retention(retention_path: Path, entries: list[dict[str, Any]]) -> None:
    header = (
        "# 阶段二真实部署留存清单\n\n"
        "| 时间 | 类型 | 文件 | 实验标签 | 论文映射 | 说明 |\n"
        "|---|---|---|---|---|---|\n"
    )
    if retention_path.exists():
        text = retention_path.read_text(encoding="utf-8")
    else:
        text = header

    lines = text.splitlines()
    retained: list[str] = []
    entry_paths = {entry["path"] for entry in entries}
    for line in lines:
        if not line.startswith("|") or line.startswith("|---"):
            retained.append(line)
            continue
        if any(f"`{path}`" in line for path in entry_paths):
            continue
        retained.append(line)

    if not any(line.startswith("| 时间 |") for line in retained):
        retained = header.splitlines()

    rows = []
    for entry in entries:
        rows.append(
            "| {mtime} | {artifact_type} | `{path}` | {label} | {mapping} | {notes} |".format(
                mtime=entry["mtime"],
                artifact_type=entry["artifact_type"],
                path=entry["path"],
                label=entry["experiment_label"],
                mapping=entry["paper_mapping"],
                notes=entry["notes"].replace("|", "/"),
            )
        )
    retention_path.write_text("\n".join(retained + rows) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register Stage 2 artifacts in the manifest and retention list."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--sui-dir", default="stage7_deployment/external/sui")
    parser.add_argument("--manifest", default="stage7_deployment/data/manifest.json")
    parser.add_argument("--retention", default="stage7_deployment/data/留存清单.md")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    manifest_path = root / args.manifest
    retention_path = root / args.retention
    sui_dir = root / args.sui_dir

    entries_to_register = build_entries(root, sui_dir)
    manifest = load_manifest(manifest_path)
    entries = manifest.setdefault("entries", [])
    if not isinstance(entries, list):
        raise ValueError(f"{manifest_path} entries must be a list")

    for entry in entries_to_register:
        upsert_by_path(entries, entry)

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    update_retention(retention_path, entries_to_register)

    print(f"updated {repo_relative(root, manifest_path)}")
    print(f"updated {repo_relative(root, retention_path)}")
    print(f"registered_or_updated={len(entries_to_register)} total_entries={len(entries)}")
    for entry in entries_to_register:
        print(f"- {entry['artifact_type']}: {entry['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
