#!/usr/bin/env python
import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


EXPECTED_SUI_COMMIT = "62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a"
EXPECTED_BASELINE_MANIFEST = "stage7_deployment/data/manifest.json"


def _require_mapping(value, path, errors):
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def _require_string(value, path, errors, allow_empty=False):
    if not isinstance(value, str):
        errors.append(f"{path} must be a string")
        return
    if not allow_empty and not value:
        errors.append(f"{path} must not be empty")


def _validate_iso8601(value, path, errors):
    _require_string(value, path, errors)
    if not isinstance(value, str):
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path} must be ISO-8601")


def validate_environment_snapshot(data):
    errors = []
    if not isinstance(data, dict):
        return ["environment snapshot must be a JSON object"]

    _validate_iso8601(data.get("captured_at"), "captured_at", errors)

    host = _require_mapping(data.get("host"), "host", errors)
    _require_string(host.get("os"), "host.os", errors)
    _require_string(host.get("timezone"), "host.timezone", errors)
    if host.get("os") != "Windows":
        errors.append("host.os must be Windows")
    if host.get("timezone") != "Asia/Shanghai":
        errors.append("host.timezone must be Asia/Shanghai")

    docker = _require_mapping(data.get("docker"), "docker", errors)
    _require_string(docker.get("server_version"), "docker.server_version", errors, allow_empty=True)
    memory_total = docker.get("memory_total_bytes")
    if memory_total is not None and not isinstance(memory_total, int):
        errors.append("docker.memory_total_bytes must be an integer or null")
    if isinstance(memory_total, int) and memory_total < 0:
        errors.append("docker.memory_total_bytes must not be negative")

    sui = _require_mapping(data.get("sui"), "sui", errors)
    _require_string(sui.get("commit"), "sui.commit", errors)
    _require_string(sui.get("cli_version"), "sui.cli_version", errors, allow_empty=True)
    if sui.get("commit") != EXPECTED_SUI_COMMIT:
        errors.append(f"sui.commit must be {EXPECTED_SUI_COMMIT}")

    stage2 = _require_mapping(data.get("stage2"), "stage2", errors)
    _require_string(stage2.get("baseline_manifest"), "stage2.baseline_manifest", errors)
    if stage2.get("baseline_manifest") != EXPECTED_BASELINE_MANIFEST:
        errors.append(f"stage2.baseline_manifest must be {EXPECTED_BASELINE_MANIFEST}")

    warnings = data.get("warnings", [])
    if warnings is not None and not isinstance(warnings, list):
        errors.append("warnings must be a list when present")
    elif isinstance(warnings, list) and not all(isinstance(item, str) for item in warnings):
        errors.append("warnings entries must be strings")

    return errors


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_evidence_manifest(data, root="."):
    errors = []
    root = Path(root)
    if not isinstance(data, dict):
        return ["manifest must be a JSON object"]

    entries = data.get("entries")
    if not isinstance(entries, list):
        return ["entries must be a list"]

    seen_run_paths = set()
    for index, entry in enumerate(entries):
        path_prefix = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{path_prefix} must be an object")
            continue

        entry_path = entry.get("path")
        if not isinstance(entry_path, str) or not entry_path:
            errors.append(f"{path_prefix}.path must be a non-empty string")
            continue

        run_id = entry.get("run_id")
        key = (run_id or "", entry_path)
        if key in seen_run_paths:
            errors.append(f"{path_prefix} duplicates run_id/path: {run_id or '<none>'} {entry_path}")
        seen_run_paths.add(key)

        artifact_path = root / entry_path
        if not artifact_path.exists():
            errors.append(f"{path_prefix}.path does not exist: {entry_path}")
            continue
        if not artifact_path.is_file():
            errors.append(f"{path_prefix}.path is not a file: {entry_path}")
            continue

        expected_sha = entry.get("sha256")
        if not isinstance(expected_sha, str) or not expected_sha:
            errors.append(f"{path_prefix}.sha256 must be a non-empty string")
        else:
            actual_sha = _sha256_file(artifact_path)
            if actual_sha != expected_sha:
                errors.append(
                    f"{path_prefix}.sha256 mismatch for {entry_path}: expected {expected_sha}, got {actual_sha}"
                )

        expected_bytes = entry.get("bytes")
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            errors.append(f"{path_prefix}.bytes must be a non-negative integer")
        elif artifact_path.stat().st_size != expected_bytes:
            errors.append(f"{path_prefix}.bytes mismatch for {entry_path}")

    return errors


def load_json(path):
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate stage7 multivalidator manifests.")
    parser.add_argument("--environment", help="Path to environment_snapshot.json")
    parser.add_argument("--manifest", help="Path to evidence manifest JSON")
    parser.add_argument("--root", default=".", help="Root for manifest entry paths")
    args = parser.parse_args(argv)

    if not args.environment and not args.manifest:
        parser.error("--environment or --manifest is required")

    if args.environment:
        try:
            data = load_json(args.environment)
        except FileNotFoundError:
            print(f"environment manifest not found: {args.environment}", file=sys.stderr)
            return 1
        except json.JSONDecodeError as exc:
            print(f"environment manifest is not valid JSON: {exc}", file=sys.stderr)
            return 1

        errors = validate_environment_snapshot(data)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1

        print("environment snapshot valid")

    if args.manifest:
        try:
            data = load_json(args.manifest)
        except FileNotFoundError:
            print(f"evidence manifest not found: {args.manifest}", file=sys.stderr)
            return 1
        except json.JSONDecodeError as exc:
            print(f"evidence manifest is not valid JSON: {exc}", file=sys.stderr)
            return 1

        errors = validate_evidence_manifest(data, root=args.root)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1

        print("evidence manifest valid")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
