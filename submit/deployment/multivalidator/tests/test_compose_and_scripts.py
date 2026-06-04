import re
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MV_ROOT = ROOT / "stage7_deployment" / "multivalidator"


class ComposeAndScriptContracts(unittest.TestCase):
    def setUp(self):
        self.compose_path = MV_ROOT / "compose" / "compose.multivalidator.yaml"
        self.matrix_path = MV_ROOT / "config" / "experiment_matrix.yaml"
        self.prepare_path = MV_ROOT / "scripts" / "prepare_multivalidator.ps1"
        self.stop_path = MV_ROOT / "scripts" / "stop_multivalidator.ps1"
        self.collect_path = MV_ROOT / "scripts" / "collect_container_state.ps1"
        self.run_matrix_path = MV_ROOT / "scripts" / "run_experiment_matrix.ps1"
        self.inject_fault_path = MV_ROOT / "scripts" / "inject_fault.sh"

        self.compose = self.compose_path.read_text(encoding="utf-8")
        self.matrix = self.matrix_path.read_text(encoding="utf-8")
        self.prepare = self.prepare_path.read_text(encoding="utf-8")
        self.stop = self.stop_path.read_text(encoding="utf-8")
        self.collect = self.collect_path.read_text(encoding="utf-8")
        self.run_matrix = self.run_matrix_path.read_text(encoding="utf-8")
        self.inject_fault = self.inject_fault_path.read_text(encoding="utf-8")

    def test_compose_defines_seven_validators_and_fullnode(self):
        for index in range(1, 8):
            self.assertRegex(self.compose, rf"(?m)^  validator-{index}:$")
        self.assertRegex(self.compose, r"(?m)^  fullnode:$")

    def test_compose_uses_static_network_and_validator_ips(self):
        self.assertIn("subnet: 172.28.7.0/24", self.compose)
        for index in range(1, 8):
            self.assertIn(f"ipv4_address: 172.28.7.1{index}", self.compose)

    def test_validator_commands_use_official_genesis_yaml(self):
        ip_ports = [
            "172.28.7.11-2000",
            "172.28.7.12-2010",
            "172.28.7.13-2020",
            "172.28.7.14-2030",
            "172.28.7.15-2040",
            "172.28.7.16-2050",
            "172.28.7.17-2060",
        ]
        for ip_port in ip_ports:
            expected = (
                "sui-node --config-path "
                f"/mvdata/runs/${{RUN_ID}}/official-genesis/{ip_port}.yaml"
            )
            self.assertIn(expected, self.compose)

        self.assertIn(
            "sui-node --config-path /mvdata/runs/${RUN_ID}/official-genesis/fullnode.yaml",
            self.compose,
        )
        self.assertIn("${FULLNODE_RPC_PORT:-9000}:9000", self.compose)

    def test_validators_have_net_admin_and_memory_limit(self):
        for index in range(1, 8):
            block = self._service_block(f"validator-{index}")
            self.assertIn("cap_add:", block)
            self.assertIn("- NET_ADMIN", block)
            self.assertIn("mem_limit: 1g", block)
            self.assertIn("<<: *validator-common", block)
        self.assertIn("../data:/mvdata", self.compose)
        self.assertIn("primary_evidence_layer: independent_containers", self.compose)

    def test_prepare_calls_generator_checks_sui_node_and_uses_benchmark_ips(self):
        self.assertIn("generate_validator_configs.py", self.prepare)
        self.assertIn("--write", self.prepare)
        self.assertRegex(self.prepare, r"command -v sui-node")
        self.assertIn("docker-compose", self.prepare)
        self.assertIn("sui\", \"genesis\"", self.prepare)
        self.assertIn("--committee-size\", \"7\"", self.prepare)
        self.assertIn("--benchmark-ips", self.prepare)
        self.assertIn("--working-dir", self.prepare)
        self.assertIn("--force", self.prepare)
        self.assertIn("--with-faucet", self.prepare)
        self.assertIn("--epoch-duration-ms", self.prepare)
        self.assertIn("genesis.stdout.log", self.prepare)
        self.assertIn("genesis.stderr.log", self.prepare)
        for index in range(1, 8):
            self.assertIn(f"172.28.7.1{index}", self.prepare)
        for expected in [
            "172.28.7.11-2000.yaml",
            "172.28.7.12-2010.yaml",
            "172.28.7.13-2020.yaml",
            "172.28.7.14-2030.yaml",
            "172.28.7.15-2040.yaml",
            "172.28.7.16-2050.yaml",
            "172.28.7.17-2060.yaml",
            "network.yaml",
            "fullnode.yaml",
            "genesis.blob",
        ]:
            self.assertIn(expected, self.prepare)
        self.assertIn('Write-Host "Next:"', self.prepare)
        self.assertNotIn("Invoke-Compose", self.prepare)
        self.assertNotRegex(self.prepare, r"(?m)^\s*&\s*\$compose")

    def test_compose_scripts_probe_falls_back_without_terminating_on_stderr(self):
        for script in [self.prepare, self.stop, self.run_matrix]:
            self.assertIn("$previousErrorActionPreference = $ErrorActionPreference", script)
            self.assertIn('$ErrorActionPreference = "Continue"', script)
            self.assertIn("2> $null", script)
            self.assertNotIn("docker compose version *> $null", script)

    def test_prepare_process_capture_supports_windows_powershell_51(self):
        self.assertIn("function Join-ProcessArguments", self.prepare)
        self.assertIn("$process.StartInfo.Arguments = Join-ProcessArguments", self.prepare)
        self.assertNotIn("StartInfo.ArgumentList.Add", self.prepare)

    def test_prepare_prints_compose_command_with_array_spacing(self):
        self.assertIn("$composeText = (@($composeCommand) + @(", self.prepare)

    def test_prepare_patches_fullnode_static_network_addresses(self):
        self.assertIn("function Patch-FullnodeNetworkConfig", self.prepare)
        self.assertIn("172.28.7.20", self.prepare)
        self.assertIn("network-address: /ip4/172.28.7.20/tcp/2070/https", self.prepare)
        self.assertIn('listen-address: "0.0.0.0:2071"', self.prepare)
        self.assertIn("external-address: /ip4/172.28.7.20/udp/2071", self.prepare)
        self.assertIn("[System.Text.UTF8Encoding]::new($false)", self.prepare)
        self.assertIn("[System.IO.File]::WriteAllText", self.prepare)
        self.assertNotIn("Set-Content -Path $FullnodePath", self.prepare)

    def test_experiment_matrix_scenarios_repeat_ten_times(self):
        for scenario in [
            "baseline",
            "delay_low",
            "delay_high",
            "loss_low",
            "crash_one_validator",
            "two_validator_pressure",
        ]:
            block = self._scenario_block(scenario)
            self.assertIn("repeats: 10", block)

    def test_stop_collect_run_matrix_and_fault_scripts_keep_evidence_safe(self):
        self.assertIn('"down"', self.stop)
        self.assertNotIn("Remove-Item", self.stop)
        self.assertNotIn("-v", self.stop)

        self.assertIn("docker ps", self.collect)
        self.assertIn("docker inspect", self.collect)
        self.assertIn("docker logs", self.collect)
        self.assertIn("evidence\\container_state", self.collect)
        self.assertIn("warnings", self.collect)

        self.assertIn("experiment_matrix.yaml", self.run_matrix)
        self.assertRegex(self.run_matrix, r"foreach|ForEach-Object")
        self.assertIn("prepare_multivalidator.ps1", self.run_matrix)

        self.assertIn("netem_delay", self.inject_fault)
        self.assertIn("netem_loss", self.inject_fault)
        self.assertIn("pause_container", self.inject_fault)
        self.assertIn("fault_timeline.jsonl", self.inject_fault)
        self.assertIn("tc qdisc replace dev eth0 root netem", self.inject_fault)

    def test_run_matrix_plan_records_fault_parameters(self):
        result = subprocess.run(
            [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self.run_matrix_path),
                "-MaxRuns",
                "0",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

        plan_path = MV_ROOT / "data" / "runs" / "experiment_matrix_plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
        by_scenario = {entry["scenario"]: entry for entry in plan}
        self.assertEqual(by_scenario["baseline"]["faults"], [])
        self.assertEqual(
            by_scenario["delay_low"]["faults"],
            [
                {
                    "action": "netem_delay",
                    "target": "validator-1",
                    "delay_ms": 50,
                    "jitter_ms": 10,
                }
            ],
        )
        self.assertEqual(
            by_scenario["two_validator_pressure"]["faults"],
            [
                {
                    "action": "netem_delay",
                    "target": "validator-1",
                    "delay_ms": 150,
                    "jitter_ms": 30,
                },
                {
                    "action": "netem_loss",
                    "target": "validator-2",
                    "loss_percent": 2,
                },
            ],
        )

    def test_run_matrix_serial_controller_executes_evidence_pipeline(self):
        required_fragments = [
            "Wait-RpcCheckpoint",
            "Invoke-RpcProbe",
            "rpc_probe.py",
            "run_workload.py",
            "actual-transfer",
            "Invoke-StartFaults",
            "fault_timeline.jsonl",
            "Complete-PauseFaults",
            "collect_container_state.ps1",
            "extract_consensus_metrics.py",
            "collect_evidence.py",
            "validate_manifest.py",
            "stop_multivalidator.ps1",
            "controller_record.json",
            "finally",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, self.run_matrix)

    def test_run_matrix_extracts_metrics_after_container_state_collection(self):
        collect_index = self.run_matrix.index("collect container state")
        metrics_index = self.run_matrix.index("extract metrics")
        self.assertLess(collect_index, metrics_index)

    def test_run_matrix_finalizes_controller_record_before_manifest_collection(self):
        manifest_index = self.run_matrix.index("collect evidence manifest")
        before_manifest = self.run_matrix[:manifest_index]
        after_manifest = self.run_matrix[manifest_index:]
        self.assertIn("$record.ended_at = New-UtcIso", before_manifest)
        self.assertIn("Write-ControllerRecord -Record $record -RunRoot $runRoot", before_manifest)
        self.assertNotIn("$record.ended_at = New-UtcIso", after_manifest)

    def test_run_matrix_pause_fault_uses_indexed_fields_and_datetime_casts(self):
        function_start = self.run_matrix.index("function Complete-PauseFaults")
        function_end = self.run_matrix.index("function Write-ControllerRecord", function_start)
        function_block = self.run_matrix[function_start:function_end]
        self.assertIn('$startedAt = [DateTime]$fault["started_at"]', function_block)
        self.assertIn('$durationSeconds = [double]$fault["duration_seconds"]', function_block)
        self.assertIn('$target = [string]$fault["target"]', function_block)
        self.assertIn('$timeline = [string]$fault["timeline"]', function_block)
        self.assertNotIn("$fault.started_at", function_block)
        self.assertNotIn("$fault.duration_seconds", function_block)

    def test_run_matrix_returns_pause_fault_array_without_powershell_unrolling(self):
        function_start = self.run_matrix.index("function Invoke-StartFaults")
        function_end = self.run_matrix.index("function Complete-PauseFaults", function_start)
        function_block = self.run_matrix[function_start:function_end]
        self.assertIn("return ,$activePauseFaults", function_block)

    def test_run_matrix_suppresses_docker_fault_command_stdout(self):
        function_start = self.run_matrix.index("function Invoke-StartFaults")
        function_end = self.run_matrix.index("function Complete-PauseFaults", function_start)
        function_block = self.run_matrix[function_start:function_end]
        self.assertIn("& docker pause $target > $null", function_block)
        self.assertIn("& docker exec $target sh -c", function_block)
        self.assertIn("> $null", function_block)

    def test_run_matrix_continue_on_failure_does_not_write_terminating_error(self):
        catch_start = self.run_matrix.index('catch {\n        $record.status = "failed"')
        catch_end = self.run_matrix.index("finally {", catch_start)
        catch_block = self.run_matrix[catch_start:catch_end]
        self.assertIn("Write-Warning $_.Exception.Message", catch_block)
        self.assertNotIn("Write-Error $_.Exception.Message", catch_block)

    def _service_block(self, service_name):
        match = re.search(
            rf"(?ms)^  {re.escape(service_name)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:|\Z)",
            self.compose,
        )
        self.assertIsNotNone(match, f"missing service block for {service_name}")
        return match.group(1)

    def _scenario_block(self, scenario_name):
        match = re.search(
            rf"(?ms)^\s*-\s+name:\s+{re.escape(scenario_name)}\n(.*?)(?=^\s*-\s+name:|\Z)",
            self.matrix,
        )
        self.assertIsNotNone(match, f"missing scenario block for {scenario_name}")
        return match.group(1)


if __name__ == "__main__":
    unittest.main()
