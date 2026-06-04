import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "stage7_deployment" / "multivalidator" / "tools"
sys.path.insert(0, str(TOOLS))

from calibrate_stage6_from_real import build_calibration_patch
from summarize_runs import summarize_metrics


class ReportingAndCalibrationTests(unittest.TestCase):
    def test_summarize_metrics_groups_by_scenario_without_dropping_nulls(self):
        metrics = [
            {
                "scenario": "baseline",
                "rpc_latency_ms_p50": 10,
                "rpc_latency_ms_p95": 30,
                "failed_transactions": 0,
                "unsupported_fields": {},
            },
            {
                "scenario": "baseline",
                "rpc_latency_ms_p50": None,
                "rpc_latency_ms_p95": 50,
                "failed_transactions": 1,
                "unsupported_fields": {"checkpoint_count": "missing"},
            },
        ]

        summary = summarize_metrics(metrics)

        self.assertEqual(1, len(summary))
        row = summary[0]
        self.assertEqual("baseline", row["scenario"])
        self.assertEqual(2, row["n"])
        self.assertEqual(1, row["null_fields"]["rpc_latency_ms_p50"])
        self.assertEqual(1, row["failed_runs"])
        self.assertIn("checkpoint_count", row["unsupported_fields"])

    def test_calibration_patch_distinguishes_measured_and_missing_parameters(self):
        metrics = [
            {
                "scenario": "delay_low",
                "rpc_latency_ms_p50": 143.2,
                "rpc_latency_ms_p95": 310.0,
            },
            {
                "scenario": "baseline",
                "rpc_latency_ms_p50": None,
                "rpc_latency_ms_p95": None,
            },
        ]

        patch = build_calibration_patch(metrics)

        measured = [item for item in patch["parameters"] if item["parameter"] == "delay_low.rpc_latency_ms_p50"][0]
        missing = [item for item in patch["parameters"] if item["parameter"] == "baseline.rpc_latency_ms_p50"][0]
        self.assertEqual("measured_distribution_p50_p95", measured["confidence"])
        self.assertEqual(143.2, measured["after"])
        self.assertIsNone(missing["after"])
        self.assertEqual("missing_real_measurement", missing["confidence"])

    def test_verify_no_paper_mutation_fails_when_stage8_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "final").mkdir()
            (root / "final" / "final_paper.md").write_text("paper", encoding="utf-8")
            (root / "stage8_paper_integration").mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "verify_no_paper_mutation.py"),
                    "--root",
                    str(root),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(1, result.returncode)
            self.assertIn("stage8_paper_integration", result.stderr)


if __name__ == "__main__":
    unittest.main()
