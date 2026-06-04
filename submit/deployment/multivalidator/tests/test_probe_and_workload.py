import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from stage7_deployment.multivalidator.tools.rpc_probe import (
    build_rpc_payload,
    classify_rpc_response,
    make_event,
    parse_args as parse_rpc_probe_args,
)
from stage7_deployment.multivalidator.tools import run_workload as run_workload_module
from stage7_deployment.multivalidator.tools.run_workload import (
    _select_sender_recipient,
    build_docker_sui_client_command,
    build_new_address_client_args,
    build_workload_client_config,
    build_workload_events,
    make_actual_transaction_event,
    parse_addresses,
    parse_args as parse_workload_args,
    parse_gas_objects,
    write_jsonl,
)


class RpcProbeTests(unittest.TestCase):
    def test_build_rpc_payload_uses_json_rpc_2_0_shape(self):
        payload = build_rpc_payload(
            "sui_getLatestCheckpointSequenceNumber",
            params=["example"],
            request_id="probe-1",
        )

        self.assertEqual(
            payload,
            {
                "jsonrpc": "2.0",
                "id": "probe-1",
                "method": "sui_getLatestCheckpointSequenceNumber",
                "params": ["example"],
            },
        )

    def test_classify_rpc_response_distinguishes_success_and_error(self):
        ok, error = classify_rpc_response('{"jsonrpc":"2.0","result":"42","id":1}')
        self.assertTrue(ok)
        self.assertEqual("", error)

        ok, error = classify_rpc_response(
            '{"jsonrpc":"2.0","error":{"code":-32601,"message":"missing"},"id":1}'
        )
        self.assertFalse(ok)
        self.assertIn("missing", error)

        ok, error = classify_rpc_response("not-json")
        self.assertFalse(ok)
        self.assertIn("invalid_json", error)

    def test_make_event_records_latency_and_rpc_status(self):
        started = datetime(2026, 5, 24, 10, 0, 0, tzinfo=timezone.utc)
        ended = datetime(2026, 5, 24, 10, 0, 0, 250000, tzinfo=timezone.utc)

        event = make_event(
            run_id="run-a",
            endpoint="http://127.0.0.1:9000",
            method="sui_getTotalTransactionBlocks",
            started_at=started,
            ended_at=ended,
            ok=True,
            response_text='{"result":"7"}',
        )

        self.assertEqual("rpc_probe", event["source"])
        self.assertEqual("rpc_ok", event["event_type"])
        self.assertIsNone(event["validator"])
        self.assertGreaterEqual(event["payload"]["latency_ms"], 0)
        self.assertEqual(250, event["payload"]["latency_ms"])
        self.assertIn("evidence_ref", event)

    def test_rpc_probe_cli_accepts_repeated_endpoints_and_defaults_methods(self):
        args = parse_rpc_probe_args(
            [
                "--run-id",
                "run-a",
                "--endpoint",
                "http://127.0.0.1:9000",
                "--endpoint",
                "http://127.0.0.1:9001",
                "--output",
                "probe.jsonl",
            ]
        )

        self.assertEqual("run-a", args.run_id)
        self.assertEqual(
            ["http://127.0.0.1:9000", "http://127.0.0.1:9001"],
            args.endpoint,
        )
        self.assertIn("sui_getLatestCheckpointSequenceNumber", args.methods)
        self.assertIn("sui_getTotalTransactionBlocks", args.methods)
        self.assertEqual("probe.jsonl", args.output)


class WorkloadPlanTests(unittest.TestCase):
    def test_same_seed_generates_same_workload_events(self):
        first = build_workload_events(
            run_id="run-a",
            seed=123,
            accounts=4,
            tps=2,
            duration_seconds=3,
        )
        second = build_workload_events(
            run_id="run-a",
            seed=123,
            accounts=4,
            tps=2,
            duration_seconds=3,
        )

        self.assertEqual(first, second)

    def test_different_seed_changes_account_selection_or_event_details(self):
        first = build_workload_events(
            run_id="run-a",
            seed=123,
            accounts=4,
            tps=2,
            duration_seconds=3,
        )
        second = build_workload_events(
            run_id="run-a",
            seed=124,
            accounts=4,
            tps=2,
            duration_seconds=3,
        )

        self.assertNotEqual(first, second)

    def test_workload_events_are_planned_not_submitted(self):
        events = build_workload_events(
            run_id="run-a",
            seed=123,
            accounts=4,
            tps=2,
            duration_seconds=2,
        )

        self.assertGreater(len(events), 1)
        for sequence, event in enumerate(events):
            self.assertEqual("workload", event["source"])
            self.assertIn(
                event["event_type"],
                {"workload_plan", "tx_submit_planned"},
            )
            self.assertEqual(123, event["payload"]["seed"])
            self.assertEqual(sequence, event["payload"]["sequence"])
            self.assertIn("scheduled_at_offset_ms", event["payload"])
            status = event["payload"]["status"]
            self.assertEqual("planned_not_submitted", status)
            self.assertNotIn(status, {"success", "finalized"})

    def test_write_jsonl_persists_one_json_object_per_line(self):
        events = build_workload_events(
            run_id="run-a",
            seed=123,
            accounts=2,
            tps=1,
            duration_seconds=2,
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "workload.jsonl"

            write_jsonl(events, output)

            lines = output.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(events), len(lines))
            self.assertEqual(events[0], json.loads(lines[0]))

    def test_workload_cli_accepts_required_generation_flags(self):
        args = parse_workload_args(
            [
                "--run-id",
                "run-a",
                "--seed",
                "20260524",
                "--accounts",
                "7",
                "--tps",
                "2.5",
                "--duration-seconds",
                "30",
                "--output",
                "workload.jsonl",
            ]
        )

        self.assertEqual("run-a", args.run_id)
        self.assertEqual(20260524, args.seed)
        self.assertEqual(7, args.accounts)
        self.assertEqual(2.5, args.tps)
        self.assertEqual(30, args.duration_seconds)
        self.assertEqual("workload.jsonl", args.output)

    def test_workload_cli_accepts_actual_transfer_flags(self):
        args = parse_workload_args(
            [
                "--run-id",
                "run-a",
                "--seed",
                "20260524",
                "--mode",
                "actual-transfer",
                "--data-root",
                "data",
                "--sui-image",
                "stage7-sui:local",
                "--container-rpc-url",
                "http://172.28.7.20:9000",
                "--amount-mist",
                "1000",
                "--gas-budget",
                "10000000",
                "--output",
                "workload.jsonl",
            ]
        )

        self.assertEqual("actual-transfer", args.mode)
        self.assertEqual(Path("data"), args.data_root)
        self.assertEqual("stage7-sui:local", args.sui_image)
        self.assertEqual("http://172.28.7.20:9000", args.container_rpc_url)
        self.assertEqual(1000, args.amount_mist)
        self.assertEqual(10000000, args.gas_budget)

    def test_build_workload_client_config_repoints_local_rpc(self):
        source = (
            "---\n"
            "keystore:\n"
            "  File: /mvdata/runs/run-a/official-genesis/sui.keystore\n"
            "envs:\n"
            "  - alias: localnet\n"
            "    rpc: \"http://127.0.0.1:9000\"\n"
        )

        rewritten = build_workload_client_config(
            source,
            container_rpc_url="http://172.28.7.20:9000",
        )

        self.assertIn("http://172.28.7.20:9000", rewritten)
        self.assertNotIn("http://127.0.0.1:9000", rewritten)
        self.assertIn("/mvdata/runs/run-a/official-genesis/sui.keystore", rewritten)

    def test_build_workload_client_config_can_use_evidence_keystore_copy(self):
        source = (
            "---\n"
            "keystore:\n"
            "  File: /mvdata/runs/run-a/official-genesis/sui.keystore\n"
            "envs:\n"
            "  - alias: localnet\n"
            "    rpc: \"http://127.0.0.1:9000\"\n"
        )

        rewritten = build_workload_client_config(
            source,
            container_rpc_url="http://172.28.7.20:9000",
            container_keystore_path="/mvdata/runs/run-a/evidence/workload/sui.workload.keystore",
        )

        self.assertIn("/mvdata/runs/run-a/evidence/workload/sui.workload.keystore", rewritten)
        self.assertNotIn("/mvdata/runs/run-a/official-genesis/sui.keystore", rewritten)

    def test_parse_addresses_and_gas_objects_from_sui_json(self):
        addresses = parse_addresses(
            json.dumps(
                {
                    "activeAddress": "0xbbb",
                    "addresses": [["sender", "0xaaa"], ["recipient", "0xbbb"]],
                }
            )
        )
        gas_objects = parse_gas_objects(
            json.dumps(
                [
                    {"gasCoinId": "0xgas1", "mistBalance": 5},
                    {"gasCoinId": "0xgas2", "mistBalance": 10},
                ]
            )
        )

        self.assertEqual(["0xaaa", "0xbbb"], addresses)
        self.assertEqual(["0xgas2", "0xgas1"], gas_objects)

    def test_build_docker_sui_client_command_targets_experiment_network(self):
        command = build_docker_sui_client_command(
            data_root=Path("E:/project/stage7_deployment/multivalidator/data"),
            run_id="run-a",
            image="stage7-sui:local",
            network="run-a_net",
            client_config="/mvdata/runs/run-a/evidence/workload/client.yaml",
            client_args=["gas", "0xabc"],
        )

        self.assertEqual("docker", command[0])
        self.assertIn("--network", command)
        self.assertIn("run-a_net", command)
        self.assertIn("stage7-sui:local", command)
        self.assertIn("sui", command)
        self.assertIn("client", command)
        self.assertIn("--json", command)
        self.assertEqual(["gas", "0xabc"], command[-2:])

    def test_build_new_address_client_args_creates_deterministic_alias(self):
        self.assertEqual(
            ["new-address", "ed25519", "workload-recipient"],
            build_new_address_client_args("workload-recipient"),
        )

    def test_make_actual_transaction_event_records_submission_result(self):
        event = make_actual_transaction_event(
            run_id="run-a",
            sequence=1,
            sender="0xaaa",
            recipient="0xbbb",
            gas_coin_id="0xgas",
            amount_mist=1000,
            gas_budget=10000000,
            latency_ms=42,
            exit_code=0,
            stdout='{"digest":"abc"}',
            stderr="",
        )

        self.assertEqual("workload", event["source"])
        self.assertEqual("tx_success", event["event_type"])
        self.assertEqual("submitted", event["payload"]["status"])
        self.assertEqual(42, event["payload"]["latency_ms"])
        self.assertEqual("0xgas", event["payload"]["gas_coin_id"])

    def test_actual_transfer_failure_overwrites_stale_output_with_failure_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "actual_transfers.jsonl"
            output.write_text(
                '{"event_type":"tx_success","source":"workload","payload":{"sequence":1}}\n',
                encoding="utf-8",
            )

            original = run_workload_module.run_actual_transfer_workload

            def fail_workload(**_kwargs):
                raise RuntimeError("no gas object found for any generated client address")

            try:
                run_workload_module.run_actual_transfer_workload = fail_workload
                exit_code = run_workload_module.main(
                    [
                        "--run-id",
                        "run-a",
                        "--seed",
                        "20260524",
                        "--mode",
                        "actual-transfer",
                        "--data-root",
                        str(Path(tmp) / "data"),
                        "--output",
                        str(output),
                    ]
                )
            finally:
                run_workload_module.run_actual_transfer_workload = original

            self.assertEqual(1, exit_code)
            lines = output.read_text(encoding="utf-8").splitlines()
            self.assertEqual(1, len(lines))
            event = json.loads(lines[0])
            self.assertEqual("workload_failed", event["event_type"])
            self.assertEqual("failed", event["payload"]["status"])
            self.assertIn("no gas object", event["payload"]["error"])
            self.assertNotIn("tx_success", output.read_text(encoding="utf-8"))

    def test_select_sender_recipient_retries_transient_empty_gas_results(self):
        calls = {"sender_gas": 0}

        def fake_run_sui_client(**kwargs):
            client_args = kwargs["client_args"]
            if client_args == ["addresses"]:
                return (
                    0,
                    json.dumps({"addresses": [["sender", "0xaaa"], ["recipient", "0xbbb"]]}),
                    "",
                    1,
                )
            if client_args == ["gas", "0xaaa"]:
                calls["sender_gas"] += 1
                if calls["sender_gas"] == 1:
                    return (0, "[]", "", 1)
                return (
                    0,
                    json.dumps([{"gasCoinId": "0xgas", "mistBalance": "100000000"}]),
                    "",
                    1,
                )
            if client_args == ["gas", "0xbbb"]:
                return (0, "[]", "", 1)
            raise AssertionError(f"unexpected client args: {client_args}")

        original_client = run_workload_module._run_sui_client
        original_sleep = run_workload_module.time.sleep
        try:
            run_workload_module._run_sui_client = fake_run_sui_client
            run_workload_module.time.sleep = lambda _seconds: None
            sender, recipient = _select_sender_recipient(
                data_root=Path("E:/project/stage7_deployment/multivalidator/data"),
                run_id="run-a",
                image="stage7-sui:local",
                network="run-a_net",
                client_config="/mvdata/runs/run-a/evidence/workload/client.yaml",
                timeout_seconds=1,
                gas_discovery_attempts=2,
                gas_discovery_interval_seconds=0,
            )
        finally:
            run_workload_module._run_sui_client = original_client
            run_workload_module.time.sleep = original_sleep

        self.assertEqual("0xaaa", sender)
        self.assertEqual("0xbbb", recipient)
        self.assertEqual(2, calls["sender_gas"])


if __name__ == "__main__":
    unittest.main()
