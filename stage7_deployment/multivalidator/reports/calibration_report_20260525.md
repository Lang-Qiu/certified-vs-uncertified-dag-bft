# Stage 6 校准报告

本报告区分真实测量参数与缺失参数。`confidence=missing_real_measurement` 的项目不能用于论文中的定量外推。

| parameter | before | after | confidence | source |
|---|---:|---:|---|---|
| baseline.rpc_latency_ms_p50 | None | 8 | measured_distribution_p50_p95 | independent_containers.baseline.rpc_latency_ms_p50 |
| baseline.rpc_latency_ms_p95 | None | 23 | measured_distribution_p50_p95 | independent_containers.baseline.rpc_latency_ms_p95 |
| baseline.recovery_time_ms | None | None | missing_real_measurement | independent_containers.baseline.recovery_time_ms |
| baseline.availability_ratio | None | 1.0 | measured_distribution_p50_p95 | independent_containers.baseline.availability_ratio |
| crash_one_validator.rpc_latency_ms_p50 | None | 4 | measured_distribution_p50_p95 | independent_containers.crash_one_validator.rpc_latency_ms_p50 |
| crash_one_validator.rpc_latency_ms_p95 | None | 25 | measured_distribution_p50_p95 | independent_containers.crash_one_validator.rpc_latency_ms_p95 |
| crash_one_validator.recovery_time_ms | None | 130920 | measured_distribution_p50_p95 | independent_containers.crash_one_validator.recovery_time_ms |
| crash_one_validator.availability_ratio | None | 1.0 | measured_distribution_p50_p95 | independent_containers.crash_one_validator.availability_ratio |
| delay_high.rpc_latency_ms_p50 | None | 11 | measured_distribution_p50_p95 | independent_containers.delay_high.rpc_latency_ms_p50 |
| delay_high.rpc_latency_ms_p95 | None | 25 | measured_distribution_p50_p95 | independent_containers.delay_high.rpc_latency_ms_p95 |
| delay_high.recovery_time_ms | None | None | missing_real_measurement | independent_containers.delay_high.recovery_time_ms |
| delay_high.availability_ratio | None | 1.0 | measured_distribution_p50_p95 | independent_containers.delay_high.availability_ratio |
| delay_low.rpc_latency_ms_p50 | None | 13 | measured_distribution_p50_p95 | independent_containers.delay_low.rpc_latency_ms_p50 |
| delay_low.rpc_latency_ms_p95 | None | 26 | measured_distribution_p50_p95 | independent_containers.delay_low.rpc_latency_ms_p95 |
| delay_low.recovery_time_ms | None | None | missing_real_measurement | independent_containers.delay_low.recovery_time_ms |
| delay_low.availability_ratio | None | 1.0 | measured_distribution_p50_p95 | independent_containers.delay_low.availability_ratio |
| loss_low.rpc_latency_ms_p50 | None | 4 | measured_distribution_p50_p95 | independent_containers.loss_low.rpc_latency_ms_p50 |
| loss_low.rpc_latency_ms_p95 | None | 25 | measured_distribution_p50_p95 | independent_containers.loss_low.rpc_latency_ms_p95 |
| loss_low.recovery_time_ms | None | None | missing_real_measurement | independent_containers.loss_low.recovery_time_ms |
| loss_low.availability_ratio | None | 1.0 | measured_distribution_p50_p95 | independent_containers.loss_low.availability_ratio |
| two_validator_pressure.rpc_latency_ms_p50 | None | 4 | measured_distribution_p50_p95 | independent_containers.two_validator_pressure.rpc_latency_ms_p50 |
| two_validator_pressure.rpc_latency_ms_p95 | None | 25 | measured_distribution_p50_p95 | independent_containers.two_validator_pressure.rpc_latency_ms_p95 |
| two_validator_pressure.recovery_time_ms | None | None | missing_real_measurement | independent_containers.two_validator_pressure.recovery_time_ms |
| two_validator_pressure.availability_ratio | None | 1.0 | measured_distribution_p50_p95 | independent_containers.two_validator_pressure.availability_ratio |
