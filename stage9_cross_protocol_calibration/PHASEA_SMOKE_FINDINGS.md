# Phase A 冒烟发现（2026-05-31）

## 冒烟目的
确认 Δ_recover 旋钮（`SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS`）在多验证者部署中接通且能影响可观测 cadence。机制检查，非测量（真 Phase A = 3 种子 × 20 reps × (ρ,Δ_recover) 网格）。

## 已验证 ✅（主要目标：build→image→deploy→measure 全管线打通）
- stage9-sui-certgate:local 镜像在**完整 stage7 多验证者编排**下工作：genesis prep + 8 容器 + 共识 + 故障注入 + cadence 提取 + manifest 校验全绿。
- 修改版二进制确认在跑（日志头 `1.74.0-62ee6ada958c-dirty`）。
- stage7 base compose 的向后兼容 env 注入（`environment: SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS=${...:-0}`）生效，旋钮经 host env → compose → 容器传入。
- 对照运行（同种子 20260530、同 loss5_v1 场景，仅旋钮不同）：

| metric | baseline (0ms) | knob (1000ms) |
|---|---:|---:|
| checkpoint_count | 660 | 661 |
| interval p50 (ms) | 222 | 223 |
| interval p95 (ms) | 226 | 227 |
| successful_txns | 60 | 60 |

## 关键发现 ⚠️（非 bug，是实验设计问题）
**5% 丢包 → 7 个验证者全部 `Synced ... missing blocks` = 0 次**（grep 验证）。即该故障**未触发任何 reconciliation fetch**，`process_fetched_blocks` 从未执行，旋钮**正确地保持惰性**。故 cadence 不变不是接线 bug，而是**这个故障太温和，没产生恢复事件**。

机理：Mysticeti 对 5% 丢包鲁棒——6 个健康验证者轻松成 quorum（需 2f+1=5），被丢的块经正常路径稍晚到达，从不触发「缺失祖先 → 挂起 → fetch」路径。

## 深层实验设计含义（影响 Phase A 正篇）
**Δ_recover 只在「恢复处于共识关键路径」时影响可观测 cadence。** 单个验证者的恢复延迟在 Mysticeti 里是**离关键路径**的——共识用其余 quorum 继续推进，不等落后节点。论文模型 `net ≈ Δ_save − ρ·Δ_recover` 隐含 Δ_recover 进入可观测延迟，这只在以下情形成立：
- 落后/catch-up 时，被提交的 **leader/anchor 块**必须先 fetch 才能 linearize（`commit_syncer` 关键路径）；
- 或健康验证者数 < quorum，系统必须等恢复才能成 quorum。

这与论文 v3 「或有负债只在故障下爆发、且强度驱动」自洽，并**进一步精化**为：或有负债只在故障**严重到迫使关键路径恢复**时进入 cadence。

→ **Phase A 的故障模型需重设计**，让 reconciliation 落在关键路径。候选：
1. **pause_container 故障**（脚本已支持，`docker pause` N 秒后 unpause）：暂停 validator-1 ~20-30s → resume 后必须 fetch 所有错过的块 → 保证 `process_fetched_blocks` 大量触发。**直接信号** = 旋钮 on/off 下 v1 catch-up 耗时（fault_timeline 的 recovery_time_ms），即使 fullnode cadence 不变也能证明旋钮 fire。
2. **降健康集到 quorum 边缘**：n=7 同时降 ≥3 个验证者（但 >f 会破活性，须谨慎）；或聚焦 leader 块缺失。
3. **改测量信号**：除 fullnode checkpoint cadence 外，加测「落后节点 catch-up 时间」作为 Δ_recover 的直接观测量。

## 产物
- 对照数据：`data/runs/PHASEA_smoke_baseline_recover0/`（保留）+ `loss5_v1_recover_probe_seed20260530_rep01/`（knob-on，已覆盖原 baseline 位）。
- 矩阵：`config/phaseA_smoke_matrix.yaml`。
- compose 改动：stage7 `compose.multivalidator.yaml` 加向后兼容 env（旋钮 + cert_gate）。

## 更新（2026-05-31）：pause 冒烟已跑 → 第二个更深发现
跑了 pause_container（暂停 validator-1 ~70s 后 unpause）baseline（RECOVER_MS=0）：
- cadence **确实变了**：p95 226→**337**，count 660→788（暂停期网络放缓 + v1 重新加入）→ **部署天然存在 Δ_recover 样的恢复代价**。
- 但 v1 `Synced ... missing blocks` 仍 = **0**。grep v1 日志确认：**v1 的 catch-up 走的是 `commit_syncer`（批量 commit 同步），不是 `synchronizer::process_fetched_blocks`（旋钮所在）**。

**根因（两次冒烟，两种不同原因，旋钮都没 fire）**：
- 5% 丢包：太温和，无 live missing-ancestor fetch。
- 70s pause：太严重，v1 落后太多 → 走 `commit_syncer` 批量同步（`schedule_loop→fetch_loop→fetch_once`，commit_syncer.rs:162/456/546），**不经旋钮所在的 synchronizer**。

→ **旋钮位置不完整**。Mysticeti 有**两个独立恢复子系统**：
1. `synchronizer::process_fetched_blocks` — 正常运行期 live 缺失祖先 fetch（已埋旋钮）。
2. `commit_syncer::fetch_once` — 落后节点批量 commit 同步（**未埋**，但这才是「故障→落后→恢复」现实场景的主路径）。

论文 Δ_recover（reconciliation 代价）在现实故障下**主要由 commit_syncer 承担**。

## 提议的修复
在 `commit_syncer::fetch_once`（commit_syncer.rs:546，`sleep`/`Duration` 已导入）加同样的 `recovery_extra_delay_ms` sleep（每次 commit-range fetch 一次）。这样旋钮**覆盖两个恢复子系统**，完整代表 Δ_recover。代价：重建（~增量 20-40min，consensus-core 改动触发下游 sui-node 重编）。

## 更新 2（2026-05-31）：旋钮已扩到 commit_syncer + 重建 + 重跑 → 根本机制查清

扩展旋钮到 `commit_syncer::fetch_once`（commit_syncer.rs:546）、重建（18m34s 增量）、重跑 pause 冒烟（RECOVER_MS 0 vs 1000）。结果：

| | baseline(0) | knob(1000) |
|---|---:|---:|
| checkpoint count | 788 | 727 |
| p95 (ms) | 337 | 289 |
| v1 max synced_commit_index | 607 | 878 |
| v1 **highest_scheduled_index** | **0** | **0** |

**决定性发现：`highest_scheduled_index=0` 两个 run 都是 0 → `commit_syncer::fetch_once` 从未被调用。** 加上首轮 `synchronizer "Synced missing blocks"=0` → **两个 fetch 路径都没被触发**。v1（607/878）向网络高度（v2=965）推进**纯靠正常区块广播**。

### 根本机制（重要）
**Mysticeti 短暂离线节点靠 PUSH（持续区块广播 backlog）catch-up，不靠 PULL（fetch）。** 两个 fetch 路径（synchronizer 缺失祖先、commit_syncer 批量）**只在 push 失败时**才激活——即需要的块已被 peer GC、或网络分区使节点彻底错过广播、或离线久到超出 DAG cache/GC 窗口。

→ **Δ_recover（或有负债）只在 push 失败、被迫 pull 时才materialize**——比假设的窄得多。温和丢包（push 仍达）和中等 pause（重连后 push backlog）都不触发。cadence 那点变化（baseline 自身 337）是 push backlog 处理的自然放缓，**不经旋钮**，且 1-rep 噪声大（knob 289<baseline 337，方向都反，纯噪声）。

### 已确证 vs 未确证
- ✅ 全管线（build→image→deploy→measure）、镜像 drop-in、旋钮 env 接通、两 fetch 路径都已埋旋钮、编译/boot 全绿。
- ❌ **未能触发任一 fetch 路径** → 旋钮 fire 未经直接证明（两种故障都被 Mysticeti 的 push catch-up 绕过）。

## 更新 3（2026-05-31）：✅ 旋钮 fire 已 DEFINITIVELY 证实（网络分区故障）

加了 STAGE9_RECOVERY instrumentation（synchronizer + commit_syncer 每次 fetch 都 log，兼 ρ 计数器），重建（19m56s），写了 `scripts/partition_pull_test.ps1`（`docker network disconnect` v1 80s → reconnect，复用 stage7 prepare/stop + base compose），RECOVER_MS=1000 跑。

**结果（决定性成功）**：
- checkpoint 310（分区前）→ 653（分区中，网络无 v1 推进）→ 926（愈合后）。
- **STAGE9_RECOVERY hits：v1=46，其余 0-6。** 分区把 v1 逼上 pull 路径。
- 全部 46 条 = `path=synchronizer blocks=N delay_ms=1000`（**值正确**；早先「100」是 grep 截断假象）。
- **延迟确实生效**：愈合后连续 fetch 时间戳 17:44:07.360→08.362→09.364，**间隔 ~1002ms** = 1000ms 旋钮直接可见。

**确证清单**：① 旋钮 fire（46 次）② 值正确（1000）③ 延迟真应用（间隔 ~1s）④ 触发故障 = **网络分区**（disconnect/reconnect，非 loss 非 pause）⑤ 走 **synchronizer** 路径（非 commit_syncer——分区重连是 live 缺失祖先 fetch）⑥ **ρ instrumentation 可用**（46 = 恢复事件直接计数，正是 Phase A 要的 ρ）。

### 关键机制总结（三种故障，三种结局）
| 故障 | v1 恢复机制 | 旋钮 fire? |
|---|---|---|
| 5% 丢包 | push 仍达，无 fetch | ✗ |
| 70s pause（SIGSTOP） | TCP 保持，peer 重放 backlog = push | ✗ |
| **网络分区（disconnect）** | **连接切断，重连后必须 fetch gap = pull** | **✓ 46 次** |

→ Mysticeti 的 Δ_recover（或有负债）**只在连接真正切断、被迫 pull 时 materialize**。这与论文 v3「或有负债强度驱动、仅故障下爆发」一致并精化为可操作的故障判据。

### 仍未测：Δ_recover 对**可观测 cadence** 的影响
旋钮 fire 了，但单节点 v1 的恢复**离共识关键路径**（其余 6 节点成 quorum 继续）。要测 Δ_recover 进入 fullnode cadence，需让恢复落在关键路径（分区 ≥ n-quorum+1 个节点，或测「落后节点 catch-up 时间」作直接观测量）。这是 Phase A 正篇的测量设计问题，机制本身已通。

## Phase 0 + 旋钮验证：完成 ✅
build→image→deploy→旋钮 fire 全链路打通且证实。

## 更新 4（2026-05-31）：Δ_recover 扫描 — 机制通，但**测量尚不可复现**
跑了 3 点扫描 {0,500,1000}（`scripts/partition_pull_test.ps1` 缩短到 60/70/50s × 3）。STAGE9_RECOVERY 计数：**ms0=32, ms500=0, ms1000=2 —— 非干净曲线**。

诊断（两个 harness 缺陷）：
- **ms0=32**：RECOVER_MS=0 → v1 快速 catch-up → 所有 fetch 落在 50s watch 窗内 → captured。
- **ms1000=2**：延迟 1000ms → catch-up 慢 → teardown 前只完成 2 次 fetch（**watch 窗太短，截断了慢恢复**）。
- **ms500=0**：该 run 分区未触发 fetch —— 很可能 **60s warmup 太短**，commit 产出未稳定，gap 小到被 push 桥接。
- 对照：能出 46 hits 的 standalone run 用的是更长的 **75/80/60s**。

**结论**：旋钮机制已证（standalone 46 hits + 1000ms 间隔），但作为**定量校准**，分区恢复对**时序敏感、当前 harness 不够稳健**——需要 (a) 更长 warmup 确保稳定 commit 产出 + 可复现 gap；(b) watch 窗足够长以容纳高 RECOVER_MS 的慢恢复（或动态等到 v1 追平网络高度再 teardown）；(c) 每 cell 多 reps（v3 单种子教训）。

→ **Phase A 定量校准需要一次「稳健故障 harness」工程投入**，非再多跑几次 ad-hoc 扫描能解决。这是清晰的下一块工作。

## 当前可交付的干净结果（无需更多跑批）
1. **三故障分类法**（loss/pause/partition）+ Δ_recover 只在真分区下 materialize —— 对论文 v3「或有负债仅故障下、强度驱动」的可操作精化。
2. **旋钮机制 + ρ instrumentation 已证可用**（standalone partition：46 hits, delay_ms=1000, 间隔~1002ms）。
3. 全可复现工件：改造 Sui 镜像、两路径旋钮、STAGE9_RECOVERY ρ 计数、partition 测试脚本。

## 下一步决策（待用户）
A. **投入稳健故障 harness**：改 partition 脚本——长 warmup（等 RPC checkpoint 稳定增长）、动态 watch（轮询直到 v1 追平或超时）、每 cell ≥3 reps、扫 RECOVER_MS 网格。然后出干净 Δ_recover 校准曲线 + 测 ρ–Δ_recover 耦合。工程量中等，是 Phase A 正篇主体。
B. **就此收尾 stage9 实证**：以「机制证实 + 三故障分类法 + Δ_recover 只在分区下 materialize」作为对论文的实证细化产出回填（走批准门禁），定量网格留作未来工作。
C. 暂停复盘。
