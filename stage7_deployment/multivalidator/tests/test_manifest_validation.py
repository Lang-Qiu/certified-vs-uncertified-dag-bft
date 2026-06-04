import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "stage7_deployment" / "multivalidator" / "tools" / "validate_manifest.py"


def minimal_environment_snapshot():
    return {
        "captured_at": "2026-05-24T10:00:00+08:00",
        "host": {"os": "Windows", "timezone": "Asia/Shanghai"},
        "docker": {"server_version": "", "memory_total_bytes": None},
        "sui": {
            "commit": "62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a",
            "cli_version": "",
        },
        "stage2": {"baseline_manifest": "stage7_deployment/data/manifest.json"},
    }


def run_validator(snapshot_path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--environment", str(snapshot_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_manifest_validator(manifest_path, root):
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--manifest",
            str(manifest_path),
            "--root",
            str(root),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class EnvironmentSnapshotValidationTests(unittest.TestCase):
    def test_environment_snapshot_minimal_schema_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "environment_snapshot.json"
            snapshot.write_text(
                json.dumps(minimal_environment_snapshot()),
                encoding="utf-8",
            )

            result = run_validator(snapshot)

            self.assertEqual(0, result.returncode, result.stderr + result.stdout)
            self.assertIn("environment snapshot valid", result.stdout)

    def test_environment_snapshot_requires_known_sui_commit(self):
        data = minimal_environment_snapshot()
        data["sui"]["commit"] = "unexpected"
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "environment_snapshot.json"
            snapshot.write_text(json.dumps(data), encoding="utf-8")

            result = run_validator(snapshot)

            self.assertEqual(1, result.returncode)
            self.assertIn("sui.commit", result.stderr)

    def test_environment_snapshot_accepts_windows_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "environment_snapshot.json"
            snapshot.write_text(
                json.dumps(minimal_environment_snapshot()),
                encoding="utf-8-sig",
            )

            result = run_validator(snapshot)

            self.assertEqual(0, result.returncode, result.stderr + result.stdout)


class EvidenceManifestValidationTests(unittest.TestCase):
    def test_manifest_validation_detects_sha256_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence" / "rpc_probe.jsonl"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text('{"event_type":"rpc_ok"}\n', encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "stage": "stage7_multivalidator",
                        "entries": [
                            {
                                "path": "evidence/rpc_probe.jsonl",
                                "sha256": "0" * 64,
                                "bytes": artifact.stat().st_size,
                                "source": "rpc_probe",
                                "artifact_type": "jsonl",
                                "primary_evidence": True,
                                "registered_at": "2026-05-24T00:00:00Z",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = run_manifest_validator(manifest, root)

            self.assertEqual(1, result.returncode)
            self.assertIn("sha256 mismatch", result.stderr)

    def test_manifest_validation_requires_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence" / "rpc_probe.jsonl"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text('{"event_type":"rpc_ok"}\n', encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "path": "evidence/rpc_probe.jsonl",
                                "sha256": "not-checked-because-bytes-fails",
                                "source": "rpc_probe",
                                "artifact_type": "jsonl",
                                "primary_evidence": True,
                                "registered_at": "2026-05-24T00:00:00Z",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = run_manifest_validator(manifest, root)

            self.assertEqual(1, result.returncode)
            self.assertIn("bytes", result.stderr)

    def test_manifest_validation_rejects_duplicate_paths_without_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "evidence" / "rpc_probe.jsonl"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text('{"event_type":"rpc_ok"}\n', encoding="utf-8")
            import hashlib

            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            entry = {
                "path": "evidence/rpc_probe.jsonl",
                "sha256": digest,
                "bytes": artifact.stat().st_size,
                "source": "rpc_probe",
                "artifact_type": "jsonl",
                "primary_evidence": True,
                "registered_at": "2026-05-24T00:00:00Z",
            }
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"entries": [entry, dict(entry)]}), encoding="utf-8")

            result = run_manifest_validator(manifest, root)

            self.assertEqual(1, result.returncode)
            self.assertIn("duplicates", result.stderr)


if __name__ == "__main__":
    unittest.main()
