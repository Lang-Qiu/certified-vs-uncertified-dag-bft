#!/usr/bin/env python
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ARTIFACT_SUFFIXES = {
    ".jsonl": "jsonl",
    ".log": "log",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".blob": "blob",
}


def _utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _posix_relative(root, path):
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_source(path):
    parts = Path(path).parts
    joined = "/".join(part.lower() for part in parts)
    name = Path(path).name.lower()
    for source in ("rpc_probe", "workload", "fault_timeline", "container_state"):
        if source in joined or source in name:
            return source
    if len(parts) > 1:
        return parts[0]
    return "unknown"


def artifact_entry(root, path, source, artifact_type, primary_evidence):
    path = Path(path)
    return {
        "path": _posix_relative(root, path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "source": source,
        "artifact_type": artifact_type,
        "primary_evidence": bool(primary_evidence),
        "registered_at": _utc_now(),
    }


def _iter_artifact_paths(run_root, exclude_paths=None):
    run_root = Path(run_root)
    excluded = {Path(path).resolve() for path in (exclude_paths or set())}
    for path in sorted(run_root.rglob("*")):
        if not path.is_file():
            continue
        if path.resolve() in excluded:
            continue
        suffix = path.suffix.lower()
        if suffix in ARTIFACT_SUFFIXES:
            yield path


def collect_run_evidence(run_root, exclude_paths=None):
    run_root = Path(run_root)
    entries = []
    for path in _iter_artifact_paths(run_root, exclude_paths=exclude_paths):
        artifact_type = ARTIFACT_SUFFIXES[path.suffix.lower()]
        relative_parts = path.relative_to(run_root).parts
        primary_evidence = bool(relative_parts and relative_parts[0] in {"evidence", "raw"})
        entries.append(
            artifact_entry(
                run_root,
                path,
                source=infer_source(path.relative_to(run_root)),
                artifact_type=artifact_type,
                primary_evidence=primary_evidence,
            )
        )
    return {
        "schema_version": "1.0",
        "stage": "stage7_multivalidator",
        "run_root": str(run_root),
        "generated_at": _utc_now(),
        "entries": entries,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Collect run evidence into a manifest JSON.")
    parser.add_argument("--run-root", required=True, help="Run directory to scan.")
    parser.add_argument("--output-manifest", required=True, help="Manifest JSON to write.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    output = Path(args.output_manifest)
    manifest = collect_run_evidence(args.run_root, exclude_paths={output})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote manifest: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
