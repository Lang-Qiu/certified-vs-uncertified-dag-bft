import json
import tempfile
import unittest
from pathlib import Path

from stage7_deployment.multivalidator.tools.generate_validator_configs import (
    DEFAULT_FAULT_TOLERANCE,
    DEFAULT_VALIDATOR_COUNT,
    build_network_plan,
    stable_run_id,
    write_network_plan,
)


class ConfigGenerationTests(unittest.TestCase):
    def test_defaults_are_fixed_for_seven_validator_committee(self):
        self.assertEqual(DEFAULT_VALIDATOR_COUNT, 7)
        self.assertEqual(DEFAULT_FAULT_TOLERANCE, 2)

    def test_generates_seven_isolated_validator_specs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = build_network_plan(
                seed=20260524,
                scenario="baseline",
                repeat_index=1,
                output_root=Path(tmpdir),
            )

            validators = plan["validators"]
            self.assertEqual(len(validators), 7)

            all_ports = []
            config_dirs = set()
            db_paths = set()
            log_paths = set()
            required_fields = {
                "network_alias",
                "container_name",
                "config_path",
                "db_path",
                "log_path",
                "fault_target_interface",
            }

            for index, validator in enumerate(validators, start=1):
                self.assertTrue(required_fields.issubset(validator))
                self.assertEqual(validator["validator_index"], index)
                all_ports.extend(validator["ports"].values())
                config_dirs.add(validator["config_dir"])
                db_paths.add(validator["db_path"])
                log_paths.add(validator["log_path"])

            self.assertEqual(len(all_ports), len(set(all_ports)))
            self.assertEqual(len(config_dirs), 7)
            self.assertEqual(len(db_paths), 7)
            self.assertEqual(len(log_paths), 7)

    def test_same_seed_scenario_repeat_produces_same_run_id_and_spec(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            first = build_network_plan(
                seed=20260524,
                scenario="baseline",
                repeat_index=1,
                output_root=Path(tmpdir),
            )
            second = build_network_plan(
                seed=20260524,
                scenario="baseline",
                repeat_index=1,
                output_root=Path(tmpdir),
            )

            self.assertEqual(first["run_id"], "baseline_seed20260524_rep01")
            self.assertEqual(first["run_id"], second["run_id"])
            self.assertEqual(first, second)

    def test_different_seed_produces_different_run_id(self):
        self.assertNotEqual(
            stable_run_id("baseline", 20260524, 1),
            stable_run_id("baseline", 20260525, 1),
        )

    def test_write_creates_network_plan_and_validator_specs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = build_network_plan(
                seed=20260524,
                scenario="baseline",
                repeat_index=1,
                output_root=Path(tmpdir),
            )

            write_network_plan(plan)

            run_root = Path(tmpdir) / "data" / "runs" / plan["run_id"]
            network_plan_path = run_root / "network_plan.json"
            self.assertTrue(network_plan_path.exists())

            persisted_plan = json.loads(network_plan_path.read_text(encoding="utf-8"))
            self.assertEqual(
                persisted_plan["primary_evidence_layer"], "independent_containers"
            )
            self.assertIn("sui genesis --committee-size 7", persisted_plan["official_genesis_command"])
            self.assertIn("--with-faucet", persisted_plan["official_genesis_command"])

            for index in range(1, 8):
                spec_path = (
                    run_root
                    / "config"
                    / f"validator-{index}"
                    / "validator_spec.json"
                )
                self.assertTrue(spec_path.exists())
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                self.assertIsNone(spec["pending_official_generation"]["sui_key_material"])
                self.assertIsNone(spec["pending_official_generation"]["genesis_hash"])
                self.assertIn("sui genesis", spec["unsupported_fields"])


if __name__ == "__main__":
    unittest.main()
