# 阶段二真实部署 Findings 摘要

## 执行范围

阶段二在 `stage7_deployment/` 下完成了一个本地真实协议部署 harness，用于运行 Sui 当前代码路径、采集真实协议日志、执行 RPC/fullnode/faucet smoke、注入 netem 网络扰动、执行 process restart smoke，并把结果接入 Stage 1/Stage 2 calibration plumbing。

当前执行范围是单容器 `sui start --with-faucet --force-regenesis` local validator/fullnode/faucet smoke。它验证的是真实协议运行、日志覆盖、故障/网络扰动采集和校准数据通路，不是多验证者共识实验。

## 目标仓库结论

- 主目标仓库：`MystenLabs/sui`
- 当前 Sui commit：`62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a`
- 选择理由：Narwhal 独立仓库已经归档，当前 Narwhal/Bullshark/Mysticeti 相关开发路径迁移到 Sui 仓库；因此 Sui 是更贴近当前真实协议层面的目标。
- 当前结论：该 commit 可用于本地 `sui start --with-faucet --force-regenesis` smoke；没有在本阶段形成稳定的 Docker Compose 多验证者入口。

## 已获得产物

| 产物 | 路径 | 性质 |
|---|---|---|
| 目标仓库评估 | `stage7_deployment/targets/target_repos.md` | 目标选择与 multi-validator 决策记录 |
| 本地部署配置 | `stage7_deployment/compose/compose.yaml` | Docker Compose 单容器 smoke harness |
| 原始日志目录 | `stage7_deployment/data/raw/` | 真实部署原始证据 |
| Primary baseline log | `stage7_deployment/data/raw/baseline_20260523_141516.log` | 单容器 baseline smoke 原始日志 |
| Fault restart log | `stage7_deployment/data/raw/fault_restart_smoke.log` | netem/process restart smoke 原始日志 |
| 事件 JSONL | `stage7_deployment/data/derived/baseline_events.jsonl` | 从 primary baseline log 派生的事件表面 |
| 延迟摘要 | `stage7_deployment/data/derived/baseline_latency_summary.json` | 日志覆盖与 latency extraction readiness 摘要 |
| Stage 1/2 calibration | `stage7_deployment/data/derived/stage1_stage2_calibration.json` | Stage 6 simulation 与 Stage 2 evidence 的边界对照 |
| Manifest | `stage7_deployment/data/manifest.json` | artifact 注册清单 |
| 留存清单 | `stage7_deployment/data/留存清单.md` | 人类可读留存索引 |

## 关键观测

- `baseline_events.jsonl` 提供了真实协议日志覆盖，可观察到 consensus/checkpoint/warning 等日志表面。
- `baseline_latency_summary.json` 中 `latency_ms.samples` intentionally empty；当前日志没有可靠的 per-event commit/checkpoint duration 字段，因此没有计算 mean/median/p95 latency。
- transaction-token warnings 是日志表面证据，不是 committed throughput。它们只能说明部分日志文本含有 transaction 相关 token，不能替代链上提交量或吞吐结论。
- `fault_restart_smoke.log` 只支持单容器 process restart/netem 注入 smoke 观察，不能外推为多验证者恢复或共识容错结论。
- Stage 2 不隔离 certification variable。真实部署证据是混合协议效应，可用于校准和佐证，但 uncertified/certified minimal pair 的因果隔离仍属于 Stage 1/Stage 6 仿真职责。

## 论文映射

| 论文位置 | 阶段二材料可支持的内容 |
|---|---|
| 第 7.1-7.2 节 | 作为参数校准和真实协议锚点的审批材料，而不是直接回填文本 |
| 第 10 节 | 作为 cross-protocol controlled empirical evidence 的前置证据包，但需阶段三审批 |
| 第 9 节或限制讨论 | 支持诚实边界：真实部署不能单独隔离 certification variable |

## 诚实边界

当前不是多验证者共识结论。阶段二当前只覆盖单容器 Sui local validator/fullnode/faucet smoke、真实协议日志采集、netem 注入、process restart、以及 Stage 1/Stage 2 calibration plumbing。

这些 findings 不能写成“已可回填论文”的最终材料。它们是阶段三审批材料：只有在用户明确批准后，才能决定是否把其中的边界化结论转化为论文段落、表格或附录描述。

## 进入阶段三前审批材料

阶段三启动前建议审批以下材料：

- `stage7_deployment/targets/target_repos.md`
- `stage7_deployment/compose/compose.yaml`
- `stage7_deployment/data/raw/baseline_20260523_141516.log`
- `stage7_deployment/data/raw/fault_restart_smoke.log`
- `stage7_deployment/data/derived/baseline_events.jsonl`
- `stage7_deployment/data/derived/baseline_latency_summary.json`
- `stage7_deployment/data/derived/stage1_stage2_calibration.json`
- `stage7_deployment/data/manifest.json`
- `stage7_deployment/data/留存清单.md`
