import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "stage7_deployment" / "multivalidator" / "tools"
sys.path.insert(0, str(TOOLS))

from collect_evidence import collect_run_evidence
from extract_consensus_metrics import extract_metrics


def write_jsonl(path, events):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


class ConsensusMetricExtractionTests(unittest.TestCase):
    def test_rpc_ok_latency_calculates_p50_and_p95(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            write_jsonl(
                run_root / "evidence" / "rpc_probe.jsonl",
                [
                    {
                        "run_id": "run-a",
                        "event_type": "rpc_ok",
                        "source": "rpc_probe",
                        "payload": {"latency_ms": latency},
                    }
                    for latency in [10, 20, 30, 40, 100]
                ]
                + [
                    {
                        "run_id": "run-a",
                        "event_type": "rpc_error",
                        "source": "rpc_probe",
                        "payload": {"latency_ms": 999},
                    }
                ],
            )

            metrics = extract_metrics(run_root)

            self.assertEqual(30, metrics["rpc_latency_ms_p50"])
            self.assertEqual(100, metrics["rpc_latency_ms_p95"])

    def test_rpc_checkpoint_probe_derives_checkpoint_count_and_intervals(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            write_jsonl(
                run_root / "evidence" / "rpc_probe" / "probe.jsonl",
                [
                    {
                        "run_id": "run-a",
                        "event_type": "rpc_ok",
                        "source": "rpc_probe",
                        "ts": "2026-05-24T00:00:00Z",
                        "payload": {
                            "method": "sui_getLatestCheckpointSequenceNumber",
                            "latency_ms": 5,
                            "response_text": '{"jsonrpc":"2.0","id":1,"result":"10"}',
                        },
                    },
                    {
                        "run_id": "run-a",
                        "event_type": "rpc_ok",
                        "source": "rpc_probe",
                        "ts": "2026-05-24T00:00:05Z",
                        "payload": {
                            "method": "sui_getLatestCheckpointSequenceNumber",
                            "latency_ms": 5,
                            "response_text": '{"jsonrpc":"2.0","id":2,"result":"15"}',
                        },
                    },
                    {
                        "run_id": "run-a",
                        "event_type": "rpc_ok",
                        "source": "rpc_probe",
                        "ts": "2026-05-24T00:00:15Z",
                        "payload": {
                            "method": "sui_getLatestCheckpointSequenceNumber",
                            "latency_ms": 5,
                            "response_text": '{"jsonrpc":"2.0","id":3,"result":"20"}',
                        },
                    },
                ],
            )

            metrics = extract_metrics(run_root)

            self.assertEqual(20, metrics["checkpoint_count"])
            self.assertEqual(1000, metrics["checkpoint_interval_ms_p50"])
            self.assertEqual(2000, metrics["checkpoint_interval_ms_p95"])

    def test_network_plan_supplies_run_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            (run_root / "network_plan.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-meta",
                        "scenario": "baseline",
                        "repeat_index": 2,
                        "validator_count": 7,
                        "fault_tolerance": 2,
                    }
                ),
                encoding="utf-8",
            )

            metrics = extract_metrics(run_root)

            self.assertEqual("baseline", metrics["scenario"])
            self.assertEqual(2, metrics["repeat_index"])
            self.assertEqual(7, metrics["validator_count"])
            self.assertEqual(2, metrics["fault_tolerance"])

    def test_workload_planned_events_do_not_count_as_successful_transactions(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            write_jsonl(
                run_root / "raw" / "workload.jsonl",
                [
                    {
                        "run_id": "run-b",
                        "event_type": "tx_submit_planned",
                        "source": "workload",
                        "payload": {
                            "status": "planned_not_submitted",
                            "sequence": 1,
                            "planned_transaction_count": 100,
                        },
                    }
                ],
            )

            metrics = extract_metrics(run_root)

            self.assertEqual(0, metrics["successful_transactions"])

    def test_workload_failed_event_counts_as_failed_transaction_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            write_jsonl(
                run_root / "evidence" / "workload" / "actual_transfers.jsonl",
                [
                    {
                        "run_id": "run-failed",
                        "event_type": "workload_failed",
                        "source": "workload",
                        "payload": {
                            "status": "failed",
                            "sequence": 0,
                            "phase": "actual_transfer_initialization",
                            "error": "no gas object found",
                        },
                    }
                ],
            )

            metrics = extract_metrics(run_root)

            self.assertEqual(0, metrics["successful_transactions"])
            self.assertEqual(1, metrics["failed_transactions"])

    def test_missing_checkpoint_and_recovery_are_none_and_unsupported(self):
        with tempfile.TemporaryDirectory() as tmp:
            metrics = extract_metrics(Path(tmp))

            self.assertIsNone(metrics["checkpoint_count"])
            self.assertIsNone(metrics["checkpoint_interval_ms_p50"])
            self.assertIsNone(metrics["checkpoint_interval_ms_p95"])
            self.assertIsNone(metrics["recovery_time_ms"])
            self.assertIn("checkpoint_count", metrics["unsupported_fields"])
            self.assertIn("checkpoint_interval_ms_p50", metrics["unsupported_fields"])
            self.assertIn("checkpoint_interval_ms_p95", metrics["unsupported_fields"])
            self.assertIn("recovery_time_ms", metrics["unsupported_fields"])

    def test_container_state_logs_are_scanned_as_evidence_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            log_path = run_root / "evidence" / "container_state" / "validator-1.logs.txt"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("validator booted\ncheckpoint service ready\n", encoding="utf-8")

            metrics = extract_metrics(run_root)

            self.assertIn("container_state", metrics["primary_evidence_layer"])

    def test_collect_evidence_generates_sha256_and_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            artifact = run_root / "evidence" / "rpc_probe.jsonl"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            content = '{"event_type":"rpc_ok"}\n'
            artifact.write_text(content, encoding="utf-8")

            manifest = collect_run_evidence(run_root)

            entries = manifest["entries"]
            self.assertEqual(1, len(entries))
            self.assertEqual("evidence/rpc_probe.jsonl", entries[0]["path"])
            self.assertEqual(artifact.stat().st_size, entries[0]["bytes"])
            self.assertEqual(64, len(entries[0]["sha256"]))

    def test_collect_evidence_can_exclude_output_manifest_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            artifact = run_root / "evidence" / "rpc_probe.jsonl"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text('{"event_type":"rpc_ok"}\n', encoding="utf-8")
            output_manifest = run_root / "manifest.json"
            output_manifest.write_text('{"old": true}\n', encoding="utf-8")

            manifest = collect_run_evidence(
                run_root,
                exclude_paths={output_manifest},
            )

            paths = {entry["path"] for entry in manifest["entries"]}
            self.assertIn("evidence/rpc_probe.jsonl", paths)
            self.assertNotIn("manifest.json", paths)

    def test_metrics_cli_writes_json_and_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "run"
            write_jsonl(
                run_root / "rpc_probe.jsonl",
                [
                    {
                        "run_id": "run-c",
                        "event_type": "rpc_ok",
                        "source": "rpc_probe",
                        "payload": {"latency_ms": 5},
                    }
                ],
            )
            output_json = Path(tmp) / "metrics.json"
            output_csv = Path(tmp) / "metrics.csv"

            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "extract_consensus_metrics.py"),
                    "--run-root",
                    str(run_root),
                    "--output-json",
                    str(output_json),
                    "--output-csv",
                    str(output_csv),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, result.returncode, result.stderr + result.stdout)
            self.assertTrue(output_json.exists())
            self.assertTrue(output_csv.exists())


if __name__ == "__main__":
    unittest.main()
