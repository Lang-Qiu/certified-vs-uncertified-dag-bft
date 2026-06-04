# 论文级 N=7 多验证者真实性实验 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to execute this plan.

**目标：** 在已完成的阶段二 Docker/Sui 本地部署基础上，扩展出论文级稳健版的 N=7、f=2 多验证者共识实验体系。最终证据必须来自 7 个相互独立的验证者容器、真实 Sui 共识路径、真实故障注入与真实日志/RPC/容器事件采集；Stage 6 仿真只作为由真实实验校准后的外推层，不能替代真实多验证者证据。

**架构：** 新增一个隔离的 `stage7_deployment/multivalidator/` 实验胶囊，保留现有阶段二工件不变。胶囊内包含配置生成、Compose 编排、场景控制、工作负载、日志采集、指标抽取、统计汇总、Stage 6 校准、证据登记与报告生成。实验链路分三层：真实协议层、校准仿真层、真实性审计层。

**技术栈：** Docker Desktop / Docker Compose、Sui CLI 与 pinned Sui checkout、PowerShell、Bash、Python 3 标准库、可选 PyYAML/pandas/matplotlib、Linux `tc netem`、JSONL/CSV/Markdown、现有 `stage7_deployment` 工具链。

---

## 真实性原则

1. 论文结论优先引用真实多验证者部署结果；Stage 6 只用于“经真实数据校准后的仿真推断”。
2. 每个验证者必须是独立容器、独立数据卷、独立日志、独立故障注入目标。
3. 所有实验均记录 seed、Sui commit、镜像 ID、Docker 配置、Compose 配置哈希、场景参数、开始/结束时间、失败原因与原始数据哈希。
4. 延迟、吞吐、恢复时间等指标只从可追溯证据计算；无法从原始证据支持的字段写入 `null`，不得用估算值填充。
5. 每个场景至少 10 次重复实验，失败运行和离群值保留并标注，不删除。
6. 报告中必须区分三类陈述：真实部署观察、校准仿真推断、尚无证据支持的限制项。
7. 不修改 `final/final_paper.md`，不新建或写入 `stage8_paper_integration/`，除非用户另行批准。

## 目标目录

```text
stage7_deployment/
  multivalidator/
    README.md
    config/
      experiment_matrix.yaml
      resource_budget.yaml
      schema/
        manifest.schema.json
        run_record.schema.json
    compose/
      compose.multivalidator.yaml
      compose.swarm-calibration.yaml
    scripts/
      check_docker_budget.ps1
      prepare_multivalidator.ps1
      run_experiment_matrix.ps1
      stop_multivalidator.ps1
      inject_fault.sh
      collect_container_state.ps1
    tools/
      generate_validator_configs.py
      run_workload.py
      rpc_probe.py
      collect_evidence.py
      extract_consensus_metrics.py
      summarize_runs.py
      calibrate_stage6_from_real.py
      validate_manifest.py
      verify_no_paper_mutation.py
    data/
      runs/
      derived/
      manifests/
    reports/
      multivalidator_findings.md
      calibration_report.md
      validity_audit.md
    tests/
      test_config_generation.py
      test_manifest_validation.py
      test_metric_extraction.py
      fixtures/
```

## 阶段 0：冻结实验边界与环境基线

- [ ] 新建 `stage7_deployment/multivalidator/README.md`，写明本实验的边界：真实 N=7 多验证者为主证据，内部 swarm/test-cluster 只用于预校准和排障。
- [ ] 新建 `config/resource_budget.yaml`，固定本机资源预算：

```yaml
host_memory_gb: 16
docker_memory_gb: 12
validator_count: 7
fault_tolerance_f: 2
recommended_parallel_scenarios: 1
validator_memory_limit: 1g
support_services_memory_limit: 2g
notes:
  - "12GB Docker Desktop memory may be used for this experiment, but keep browser/IDE/background jobs low."
  - "Run one experiment scenario at a time to preserve stability and measurement quality."
```

- [ ] 新建 `scripts/check_docker_budget.ps1`，采集 Docker Desktop 可用内存、Docker info、镜像 ID、Compose 版本、磁盘余量。
- [ ] 输出 `data/manifests/environment_snapshot.json`，包含：

```json
{
  "captured_at": "ISO-8601",
  "host": {"os": "Windows", "timezone": "Asia/Shanghai"},
  "docker": {"server_version": "", "memory_total_bytes": null},
  "sui": {"commit": "62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a", "cli_version": ""},
  "stage2": {"baseline_manifest": "stage7_deployment/data/manifest.json"}
}
```

- [ ] 验证命令：

```powershell
.\stage7_deployment\multivalidator\scripts\check_docker_budget.ps1
python .\stage7_deployment\multivalidator\tools\validate_manifest.py --environment .\stage7_deployment\multivalidator\data\manifests\environment_snapshot.json
```

## 阶段 1：Sui 内部 swarm/test-cluster 预校准

- [ ] 在 pinned Sui checkout 中确认可用的本地多节点入口，包括 swarm、test-cluster、benchmark、committee-size 相关命令或测试工具。
- [ ] 新建 `compose/compose.swarm-calibration.yaml`，只用于快速验证 N=7 配置、RPC 探针、日志格式和指标抽取器。
- [ ] 新建 `tools/rpc_probe.py`，周期性记录 RPC 可用性、checkpoint 高度、请求延迟和错误。
- [ ] 新建 `tools/run_workload.py`，提供低 TPS、固定 seed、固定账户数的工作负载。
- [ ] 输出 `data/runs/swarm_calibration_*`，但在 manifest 中标注：

```json
{
  "evidence_layer": "swarm_calibration",
  "eligible_for_primary_claim": false
}
```

- [ ] 完成标准：swarm/test-cluster 可以生成可解析日志与 RPC 指标；若 Sui 当前 commit 无稳定入口，则写入 `reports/validity_audit.md`，并跳过该层，不影响真实容器层推进。

## 阶段 2：独立验证者配置生成

- [ ] 新建 `tools/generate_validator_configs.py`，根据 `N=7, f=2, seed` 生成 deterministic validator spec。
- [ ] 每个 validator 输出独立目录：

```text
data/runs/<run_id>/config/validator-1/
data/runs/<run_id>/config/validator-2/
...
data/runs/<run_id>/config/validator-7/
```

- [ ] 配置生成器必须记录端口、网络别名、数据卷、日志路径、故障注入接口、key/genesis/config 哈希。
- [ ] 如果 Sui CLI 支持当前 commit 的多验证者 genesis/config 命令，优先调用官方 CLI；如果需要组合官方配置文件，所有变换必须记录输入输出哈希。
- [ ] 新建 `tests/test_config_generation.py`，验证：
  - N 固定为 7。
  - f 固定为 2。
  - 端口无冲突。
  - 7 个验证者的数据目录互不共享。
  - 同一 seed 生成相同配置，不同 seed 生成不同 run id。

## 阶段 3：真实 N=7 Docker Compose 编排

- [ ] 新建 `compose/compose.multivalidator.yaml`，包含：
  - `validator-1` 到 `validator-7`。
  - 可选 `fullnode` 或 RPC 聚合探针。
  - `workload` 容器或 host-side workload 脚本。
  - `observer`/`collector` 服务。
  - 独立 volume、独立日志挂载、独立 healthcheck。
- [ ] Compose 网络固定命名为 `stage7_mv_<run_id>`，所有服务使用明确别名。
- [ ] 容器资源限制遵循 `resource_budget.yaml`：validator 建议 1GB 内存上限，支撑服务合计不超过 2GB。
- [ ] 所有 validator 容器必须使用同一个 pinned image，并记录镜像 digest。
- [ ] 验证命令：

```powershell
docker compose -f .\stage7_deployment\multivalidator\compose\compose.multivalidator.yaml config
.\stage7_deployment\multivalidator\scripts\prepare_multivalidator.ps1 -RunId smoke-n7-f2 -Seed 20260524
```

- [ ] 完成标准：7 个 validator 容器全部 healthy，RPC probe 能观测 checkpoint 或等价进展信号。

## 阶段 4：工作负载与观测探针

- [ ] `tools/run_workload.py` 支持：
  - 固定 seed。
  - 固定账户池。
  - 低、中两档 TPS。
  - 写入 JSONL 原始事件。
  - 不因单笔失败终止整个实验。
- [ ] `tools/rpc_probe.py` 支持：
  - 多 endpoint 轮询。
  - checkpoint/epoch/committee 信息采样。
  - RPC latency 采样。
  - 错误分类。
- [ ] 原始事件格式：

```json
{
  "ts": "ISO-8601",
  "run_id": "baseline_seed_20260524_rep01",
  "source": "workload|rpc_probe|validator_log|docker_event|fault_controller",
  "validator": "validator-1",
  "event_type": "checkpoint|tx_submitted|tx_finalized|rpc_error|container_state|fault",
  "payload": {},
  "evidence_ref": "relative/path/to/raw/file"
}
```

- [ ] 新建 `tests/test_metric_extraction.py` fixture，保证 parser 对缺失字段输出 `null`，不输出伪造延迟。

## 阶段 5：故障与网络扰动场景矩阵

- [ ] 新建 `config/experiment_matrix.yaml`，至少包含以下场景：

```yaml
scenarios:
  - name: baseline
    repeats: 10
    duration_seconds: 300
    workload_tps: 1
    faults: []
  - name: delay_low
    repeats: 10
    duration_seconds: 300
    workload_tps: 1
    faults:
      - target: validator-3
        kind: netem_delay
        delay_ms: 100
        jitter_ms: 20
  - name: delay_high
    repeats: 10
    duration_seconds: 300
    workload_tps: 1
    faults:
      - target: validator-3
        kind: netem_delay
        delay_ms: 500
        jitter_ms: 100
  - name: loss_low
    repeats: 10
    duration_seconds: 300
    workload_tps: 1
    faults:
      - target: validator-4
        kind: netem_loss
        loss_percent: 1
  - name: crash_one_validator
    repeats: 10
    duration_seconds: 300
    workload_tps: 1
    faults:
      - target: validator-5
        kind: pause_container
        start_after_seconds: 120
        duration_seconds: 60
  - name: two_validator_pressure
    repeats: 10
    duration_seconds: 300
    workload_tps: 1
    faults:
      - target: validator-2
        kind: netem_delay
        delay_ms: 300
        jitter_ms: 80
      - target: validator-6
        kind: pause_container
        start_after_seconds: 120
        duration_seconds: 60
```

- [ ] 新建 `scripts/inject_fault.sh`，只在目标容器内注入 netem 或 pause/unpause，所有动作写入 `fault_timeline.jsonl`。
- [ ] 新建 `scripts/run_experiment_matrix.ps1`，按场景串行执行，禁止并行运行多个场景。
- [ ] 每次 repeat 都必须生成单独 run id，例如 `delay_high_seed20260524_rep07`。
- [ ] 完成标准：至少完成 `baseline`、`delay_high`、`crash_one_validator` 三个主场景各 10 次，完整论文版完成全部 6 个场景各 10 次。

## 阶段 6：证据采集与指标抽取

- [ ] 新建 `tools/collect_evidence.py`，采集每次 run 的：
  - 每个 validator stdout/stderr。
  - Docker inspect。
  - Docker events。
  - RPC probe JSONL。
  - workload JSONL。
  - fault timeline。
  - Compose config 展开结果。
  - Sui version。
  - host/Docker snapshot。
- [ ] 新建 `tools/extract_consensus_metrics.py`，输出 `data/derived/<run_id>/metrics.json` 和 `metrics.csv`。
- [ ] 指标字段至少包含：

```json
{
  "run_id": "",
  "scenario": "",
  "repeat_index": 1,
  "validator_count": 7,
  "fault_tolerance_f": 2,
  "successful_transactions": null,
  "failed_transactions": null,
  "checkpoint_count": null,
  "checkpoint_interval_ms_p50": null,
  "checkpoint_interval_ms_p95": null,
  "rpc_latency_ms_p50": null,
  "rpc_latency_ms_p95": null,
  "recovery_time_ms": null,
  "availability_ratio": null,
  "primary_evidence_layer": "independent_containers",
  "unsupported_fields": []
}
```

- [ ] 解析器必须保留 `unsupported_fields`，说明字段为何为 `null`。
- [ ] 新建 fixture 覆盖 baseline、netem、crash、缺失日志、容器失败五类情况。

## 阶段 7：Stage 6 仿真校准

- [ ] 新建 `tools/calibrate_stage6_from_real.py`，读取真实 N=7 指标，生成：
  - `data/derived/stage6_calibration_patch.json`
  - `reports/calibration_report.md`
- [ ] 校准参数必须标注来源：

```json
{
  "parameter": "network_delay_ms",
  "before": 100,
  "after": 143.2,
  "source": "independent_containers.delay_low.rpc_latency_ms",
  "confidence": "measured_distribution_p50_p95",
  "notes": "Derived from N=7 Docker experiment, not assumed."
}
```

- [ ] 报告中必须保留校准前后差异和对 Stage 6 结论的影响。
- [ ] 若 Stage 6 当前接口无法直接接收 patch，则生成适配说明和最小 wrapper，但不手改最终论文。

## 阶段 8：统计汇总、图表与论文证据包

- [ ] 新建 `tools/summarize_runs.py`，输出：
  - `data/derived/summary_by_scenario.csv`
  - `data/derived/summary_by_scenario.json`
  - `reports/multivalidator_findings.md`
  - `reports/validity_audit.md`
- [ ] 汇总统计至少包含 median、IQR、p95、min、max、n、failed_runs、null_fields。
- [ ] 置信区间使用 bootstrap 或明确的非参数区间；样本量不足时写明限制。
- [ ] 图表只基于 `data/derived`，不直接读散落日志。
- [ ] 报告结构：

```markdown
# N=7/f=2 多验证者实验发现

## 实验设置
## 原始证据与可复现性
## Baseline 结果
## 网络延迟扰动结果
## 丢包扰动结果
## 单验证者故障结果
## 双验证者压力结果
## Stage 6 校准影响
## 有效性威胁
## 可进入论文的结论
## 不能进入论文的结论
```

## 阶段 9：Manifest 与留存清单

- [ ] 新建 `tools/validate_manifest.py`，校验所有 run artifact：
  - 文件存在。
  - SHA-256 正确。
  - run id 唯一。
  - scenario/repeat/seed 完整。
  - primary evidence layer 正确。
  - `unsupported_fields` 不为空时报告原因。
- [ ] 每个 run 生成 `data/manifests/<run_id>.json`。
- [ ] 全部实验生成 `data/manifests/multivalidator_manifest.json`。
- [ ] 生成中文留存清单 `data/manifests/多验证者实验_留存清单.md`。
- [ ] 留存清单至少包含：文件、用途、来源、哈希、是否主证据、是否可复现、备注。

## 阶段 10：防误写与完成前验证

- [ ] 新建 `tools/verify_no_paper_mutation.py`，确认本计划执行期间未修改：
  - `final/final_paper.md`
  - `stage8_paper_integration/`
- [ ] 完成前运行：

```powershell
python -m py_compile .\stage7_deployment\multivalidator\tools\generate_validator_configs.py
python -m py_compile .\stage7_deployment\multivalidator\tools\run_workload.py
python -m py_compile .\stage7_deployment\multivalidator\tools\rpc_probe.py
python -m py_compile .\stage7_deployment\multivalidator\tools\collect_evidence.py
python -m py_compile .\stage7_deployment\multivalidator\tools\extract_consensus_metrics.py
python -m py_compile .\stage7_deployment\multivalidator\tools\summarize_runs.py
python -m py_compile .\stage7_deployment\multivalidator\tools\calibrate_stage6_from_real.py
python -m py_compile .\stage7_deployment\multivalidator\tools\validate_manifest.py
python -m unittest discover -s .\stage7_deployment\multivalidator\tests -p "test_*.py"
docker compose -f .\stage7_deployment\multivalidator\compose\compose.multivalidator.yaml config
python .\stage7_deployment\multivalidator\tools\validate_manifest.py --manifest .\stage7_deployment\multivalidator\data\manifests\multivalidator_manifest.json
python .\stage7_deployment\multivalidator\tools\verify_no_paper_mutation.py
```

- [ ] 如果任何验证失败，先进入诊断流程，保留失败证据，不覆盖 run 目录。

## 最小验收标准

- [ ] `baseline`、`delay_high`、`crash_one_validator` 三个主场景各 10 次重复实验完成。
- [ ] 每次 run 都来自 7 个独立 validator 容器。
- [ ] 每次 run 都有完整 manifest、原始日志、RPC probe、workload、Docker inspect、fault timeline。
- [ ] 指标抽取器不制造无证据延迟，无法支持的字段为 `null` 并列入 `unsupported_fields`。
- [ ] Stage 6 校准报告明确区分真实测量参数与仿真推断。
- [ ] `reports/multivalidator_findings.md` 明确列出可进入论文的结论和不可进入论文的结论。

## 完整论文级验收标准

- [ ] 6 个场景全部完成，每个场景 10 次重复，共 60 次 run。
- [ ] 每个场景都有 median、IQR、p95、failed_runs、null_fields。
- [ ] 任何失败 run 均有失败原因与原始证据哈希。
- [ ] 论文报告能追溯每个图表、每个表格、每条结论到 manifest 和原始证据。
- [ ] 有效性威胁章节覆盖：单机 Docker 限制、资源竞争、Sui 本地网络与公网差异、容器时钟、工作负载代表性、样本量、故障模型边界。

## 预计工作量与代码量

| 模块 | 估计代码量 | 主要风险 |
|---|---:|---|
| 多验证者配置生成 | 300-600 行 | Sui 当前 commit 的官方配置入口需要实测确认 |
| Compose 编排与脚本 | 250-500 行 | 7 容器内存和端口稳定性 |
| 工作负载与 RPC 探针 | 400-800 行 | 交易构造和最终性证据抽取 |
| 故障注入与场景控制 | 300-600 行 | Windows + Docker Desktop 下 netem 权限和容器能力 |
| 指标抽取与统计 | 600-1000 行 | 日志格式不稳定，字段必须可追溯 |
| Manifest 与真实性审计 | 300-600 行 | 证据链完整性 |
| Stage 6 校准桥接 | 250-500 行 | 仿真接口适配 |
| 测试与 fixtures | 500-900 行 | 覆盖失败 run 和缺失字段 |

总计约 2900-5500 行。若 Sui 多验证者 genesis/config 入口需要额外适配，可能增加 1000-2000 行。

## 执行顺序

1. 完成阶段 0、1，确认 Sui 当前 commit 的本地多节点入口和日志/RPC 格式。
2. 完成阶段 2、3，先跑通 N=7 smoke，不注入故障。
3. 完成阶段 4、6、9 的最小闭环：workload -> evidence -> metrics -> manifest。
4. 完成阶段 5 的三个主场景，达到最小验收标准。
5. 完成阶段 7、8、10，形成可审计报告。
6. 扩展到全部 6 个场景，达到完整论文级验收标准。

## 关键决策记录

- 选择 N=7/f=2 是为了满足 Byzantine fault tolerance 中 `N >= 3f + 1` 的经典规模边界。
- Docker Desktop 可分配 12GB，但实验串行运行，避免多场景并行造成资源竞争。
- 不把内部 swarm/test-cluster 作为论文主证据，只作为预校准与排障辅助。
- 不限制代码量，优先保证证据链、可复现性和结论边界。
- 不用 toy consensus 或自写共识模拟替代 Sui 真实协议路径。

