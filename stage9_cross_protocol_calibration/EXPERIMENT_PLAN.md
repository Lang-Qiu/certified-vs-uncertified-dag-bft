# Code Experiment Plan

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: plan
- Origin Date: 2026-05-30
- Verification Status: UNVERIFIED
- Version Label: code_plan_v1

## Experiment Overview

- **Title**: 含 certified 对照臂的跨协议受控部署实证（Cross-protocol controlled deployment with a certified control arm）
- **Objective**: 在真实 Sui/Mysticeti 部署上**隔离「认证强度」这一单一变量**，定量标定 §7.2 成本模型参数 Δ_save / Δ_recover / ρ，检验闭式模型「净优势 ≈ Δ_save − ρ·Δ_recover」，并把 §7.6 的**定性**条件化结论提升为**定量的 (ρ, Δ_recover) 区域划分**。这是 `final/final_paper.md` §9/§10 现明确标注的最高优先级未来工作。
- **Type**: simulation / generic（分布式系统受控部署 benchmark）

### 预注册假设（falsifiable，防 p-hacking）

| # | 假设 | 证伪/检验方式 |
|---|---|---|
| H1 (Δ_save) | ρ=0 良好情形下,cert OFF 的 p50/p95 延迟低于 cert ON,差值 Δ_save > 0 且跨种子稳定 | 双臂良好情形对照,效应量 + CI |
| H2 (模型拟合) | 净优势随 ρ 线性下降,斜率 ≈ −Δ_recover,存在翻转点 ρ*,且实测 ρ* 与解析 Δ_save/Δ_recover 在 95% CI 内一致 | 回归 + bootstrap CI;比较实测 ρ* 与独立测量推出的解析 ρ* |
| H3 (耦合/可发表的否定结果) | 若净优势曲线显著偏离线性(ρ 与 Δ_recover 耦合,§7.4 拥塞反馈),则 §7.2 独立性假设被证伪/需修正 | 残差结构分析;**偏离本身即有价值的结论** |
| H4 (外部效度) | 数据扣留敌手能把**涌现 ρ** 推到 ρ* 以上的危险区,确认翻转在真实敌手下可达 | Phase B 敌手实验,测涌现 ρ vs ρ* |

## Design & Variables

### 识别策略（已定）—— 真 minimal-pair

同一 Sui/Mysticeti binary,认证为**可开关的 certificate-gate**:
- **cert ON**（certified 臂）：区块被其他区块引用前,须先收集 2f+1 投票形成 certificate（在 Mysticeti DAG 路径里插入这一 gate）。
- **cert OFF**（uncertified 臂）：原生 Mysticeti,直接引用 header。

其余维度（提交规则、leader 调度、流水线化、网络模型、负载）**全等** → 唯一 IV = 认证强度。这正是论文 §3.3 受控 minimal-pair 的操作化,直接回避 SubRQ0 批评的混淆比较。

⚠️ **不可**用历史 Narwhal/Bullshark 当 certified 臂——那是另一套引擎,会重新引入混淆、破坏 minimal-pair。

### 变量

| 角色 | 变量 | 取值 |
|---|---|---|
| IV 主 | certification | {ON, OFF} |
| IV 次(Phase A 旋钮) | ρ 恢复触发频率 | {0, .025, .05, .1, .2, .4, .6, .8}（8 档） |
| IV 次 | Δ_recover 单次恢复成本旋钮 | {低, 中, 高}（batch size / 恢复带宽限制,3 档） |
| IV 次 | 规模 n | {4, 7, 10}（f = 1, 2, 3） |
| DV 主 | 共识 cadence p50/p95 真值 | **log 解析**（禁用 rpc-probe——RP-3 教训） |
| DV 派生 | Δ_save | lat(ON, ρ=0) − lat(OFF, ρ=0) |
| DV 派生 | Δ_recover | 每次 reconciliation 的额外延迟 |
| DV 派生 | 净优势(ρ) | lat(ON) − lat(OFF),按 ρ |

### 混淆控制
- 同 binary 同配置 → 消除 SubRQ0 的十余维混淆;
- 每 cell **≥3 独立种子**（发表级;v3 单种子假阳性教训,不可谈判）;
- baseline 在每种子内共享,比值对 baseline 漂移稳健;
- **随机化运行顺序** + 种子内归一,缓解 Docker daemon/机器负载漂移（v3 见 baseline 偏高）。

## Setup

- **Language/Framework**: Rust（Sui/Mysticeti consensus 改造）+ PowerShell/Python 编排（复用 stage7）
- **Entry Command（示意）**: `powershell -ExecutionPolicy Bypass -File scripts/run_calibration_matrix.ps1 -CertMode {on|off} -Rho <r> -RecoverCost {low|mid|high} -N <n> -Seed <s> -Reps 20 -StartCompose`
- **Working Directory**: `stage9_cross_protocol_calibration/`（复用 `stage7_deployment/multivalidator/` 的 compose、netem、log 解析、manifest 校验、资源预算）
- **Dependencies**: docker-compose（注意 `docker compose` 不可用）、改造后的 sui 节点镜像、Python（pandas/numpy/scipy/matplotlib）
- **Environment**: stage7 资源预算（16GB host / 12GB Docker / 一次一个场景）。**n=10 可能超内存预算 → 须先验内存可行性**（见 Risk 2）。

## Inputs

| Input | Path | Description |
|---|---|---|
| 改造后 sui 共识 | (待建) `stage9_.../sui-fork/` | 含 cert-gate 开关 + reconciliation 旋钮 + 扣留 fault hook |
| 编排脚本 | 复用 `stage7_deployment/multivalidator/scripts/`（qdiscfix 版） | compose / netem / 日志采集 |
| 解析器 | `stage7_.../tools/extract_ckpt_metrics_from_logs.py` | true-cadence log 解析（含 early_logs 回退） |
| 资源预算/快照 | `stage7_.../config/resource_budget.yaml`, `data/manifests/` | 环境基线与 manifest 校验 |

## Expected Outputs

| Output | Path | Format | Success Criterion |
|---|---|---|---|
| 逐 run 指标 | `stage9_.../data/runs/<cond>/metrics/consensus_metrics_true.json` | JSON | 文件存在且含 p50/p95;**不覆盖 stage7 的 consensus_metrics.json** |
| 标定汇总 | `stage9_.../reports/calibration_summary.csv` | CSV | 每 cell 的 Δ_save/Δ_recover/净优势 + CI |
| 模型拟合 | `stage9_.../reports/model_fit.json` | JSON | 斜率/截距/实测 ρ* + bootstrap CI + R² |
| 区域图 | `stage9_.../figures/region_map.png` | PNG | (ρ, Δ_recover) 平面 + 实测 ρ* 边界 |

## Monitoring Configuration

- **Timeout**: 每 run 软超时（按 WorkloadDuration + 启停余量,如 10 min）;硬超时才自动 kill（安全规则 3）。
- **Monitor files**: 各 run 的 fullnode 日志 + `consensus_metrics_true.json` 生成。
- **Experiment type override**: generic（分布式部署,非 ML training）。
- **Anomaly**: compose 秒崩 / 节点未达成共识 / ckpt_count 异常低 → ADVISORY 通知,不自动重试（安全规则 2）。

## Analysis Plan

- **Primary metric**: 净优势(ρ) = lat(cert ON) − lat(cert OFF)。
- **模型检验**: 线性回归 净优势 ~ ρ → 截距=Δ_save、斜率=−Δ_recover、ρ*=截距/斜率,bootstrap 95% CI;**比较实测 ρ* 与「独立测量 Δ_save、Δ_recover」推出的解析 ρ\***（H2）。残差结构检验独立性假设;系统性偏离 → 报告耦合（H3）。
- **统计严格度**: 跨 8×3×3 cells 做多重比较校正;报告效应量 + CI（不只看 p);逐 rep CV;预注册 H1–H4。
- **Power**: 用 Phase-1 pilot 方差做正式 power 分析,报告 20 reps×3 种子达到的最小可检测效应（MDE）（保守估计,安全规则 8）。
- **Comparison/baseline**: 解析模型预测（§7.2);阶段二 v3 强度轴发现作为 cert-OFF 侧已知行为锚点。

## Phased Execution

| 阶段 | 内容 | 关键产物 |
|---|---|---|
| **Phase 0（工程）** | 在 Mysticeti DAG 路径插 certificate-gate 开关 + reconciliation 旋钮 + 数据扣留 fault hook;**正确性自证**：ON 模式语义 == 真实 certified（区块被引用前确有 2f+1 证书）、OFF == 原 Mysticeti、安全性/活性不破 | 改造 binary + 语义等价测试 |
| **Phase 1（pilot/smoke）** | 精简网格验证三钩子跑通 + Δ_save 可测 + 取方差 | pilot 方差 → 喂 power 分析 |
| **Phase 2（Phase A 全标定）** | 旋钮扫描全网格 n×ρ×Δ_recover×cert×20reps×3seeds | calibration_summary + model_fit |
| **Phase 3（Phase B 外部效度）** | 数据扣留敌手,测涌现 ρ 是否 ≥ ρ* | adversary_emergence 报告 |
| **Phase 4（分析+图+回填准备）** | 拟合、ρ* CI、区域图;整理可回填 §7.2/§7.6/§9/§10 的材料 | region_map + 呈递材料 |

## Risks

1. **工程风险（Phase 0 后由「最高」下调为「中」）**：Phase 0 源码核对（`PHASE0_SPIKE.md` §1.5）确认 cert-gate 可复用 Sui 已有的 `accepted_quorum_rounds`（RoundTracker），**无需从零重建 RBC**；插入点 = `proposer.rs::smart_ancestors_to_propose`（祖先资格谓词，protocol_config flag 控制）；commit 安全规则（`base_committer`）独立于提案时引用，**cert ON/OFF 不破坏 commit 安全**。残余风险：(a) cert ON 须验证不会因 gate 过严损活性；(b)「quorum-accepted」是认证的延迟/可用性代理、非密码学证书——Δ_save 与等价测试须如实表述。recovery 旋钮落点 `block_manager::try_accept_one_block` + `synchronizer::fetch_blocks_from_peer`；数据扣留钩子 `authority_service::handle_fetch_blocks`。
2. **n=10 内存**：可能超 stage7 的 16GB 预算 → 先验内存可行性,不行则换机或降 workload。
3. **合成 ρ 的忠实度**：旋钮触发的 reconciliation 是否忠实于真实恢复路径 → 用 Phase B 敌手交叉验证（已设计）。
4. **工期/稳定性**：几千 runs + Docker daemon 漂移（v3 已见）→ 随机化顺序 + 种子内归一 + 自动 manifest 校验。
5. **Δ_save 外推限定**：我们是在 Mysticeti 上加 gate,非跑真 Bullshark;测得的 Δ_save 是「同引擎加/去证书」的成本,需在论文里如实限定为该操作化下的值。

## 回填衔接（门禁）

结果回填论文仍须经 `[[paper-integration-approval-gate]]`。预期触及：§7.2（模型从定性→标定）、§7.6（定量区域图替换/补充图 7-3）、§9/§10（把"含 certified 臂的跨协议受控实证"从未来工作标记为已完成）。权威衔接见 `stage8_paper_integration/STAGE3_ROUND1_COMPLETE.md` 的"后续可选工作"。
