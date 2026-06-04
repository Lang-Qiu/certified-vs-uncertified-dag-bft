# Phase 0 — Route A1 设计稿（忠实 certified 臂：prober-as-ack-channel）

> 用户已选 **Route A1（忠实 ack/投票通道）**。深读 `proposer.rs` / `base_committer.rs` /
> `universal_committer.rs` / `linearizer.rs` / `round_tracker.rs` / `round_prober.rs` /
> `network/mod.rs` 后，本稿给出**一个比"从零加新消息类型"远更可行、且仍然忠实**的实现：
> **复用 Sui 已有的 RoundProber 作为独立确认通道**，把引用资格 gate 在"探测得到的 quorum 接受"上。
> 受 `[[paper-integration-approval-gate]]` 约束：回填论文须二次确认；Δ_save 须如实表述。

---

## 1. 核心洞察（为何不必从零建 RBC）

certified-DAG 与 uncertified-DAG 的差别在**引用资格**：certified 中区块 B 须先集齐 2f+1 ack（一个
独立确认轮）才可被引用；Mysticeti 去掉该轮，块一经 accept 即可被引用。**那个独立确认轮的延迟 = Δ_save。**

Sui 其实**已经有一个独立确认通道**：`RoundProber`（`round_prober.rs:108 probe()`）周期性向每个 peer
发 `get_latest_rounds` RPC（`network/mod.rs:172`），问"你从各 author 接受到的最高轮次"。结果经
`update_from_probe` 存入 `round_tracker.rs::probed_accepted_rounds`（:48，与引用派生的
`block_accepted_rounds` :46 **分开存**），再由 `compute_accepted_quorum_rounds`（:203）按 stake
求 quorum 下界 `(low, high)`。**`probed_accepted_rounds` 派生的 low 界 = "一个 2f+1 stake quorum
已接受 author 到该轮" = 一张可用性证书**，且因为它来自"peer 收到块即接受"（块流推送），**独立于
任何后续轮的提案** → 非循环。

> 这正是 §"关键阻塞发现"里循环死锁的破解：死锁源于"认证信号仅来自后轮引用"。改用 prober 的直接接受
> 探测，认证不再依赖未来提案 → 无死锁。spike 当初把"加速 prober"列为 Route 3 并以"hacky/网络负载"
> 否决，但**对受控实验（n=4/7）这点负载可接受，且它是真·独立通道，不是逐字节 stock**——它就是忠实
> A1 的最小实现。

---

## 2. 架构（cert ON / OFF 语义）

| | cert OFF（默认，= stock Mysticeti） | cert ON（certified 臂） |
|---|---|---|
| 引用资格 | 块一经 accept 即可被引用（原生） | 父轮祖先 B 仅当 **probe-quorum 已接受 B**（`probed_accepted_quorum_rounds[B.author].0 >= B.round()`）才可纳入提案 |
| RoundProber | stock 间隔（prod 默认） | **快速间隔**（如 50–100ms），作为 ack 通道 |
| Δ_save | 0 | 每轮等"2f+1 父块被 quorum 接受"的认证往返延迟 |
| 代码路径 | gate 全包在 `if certificate_gate`，逐字节同 stock | 仅多一个祖先资格谓词 + 快 prober |

**Δ_save 来源**：round r 提案需 2f+1 个 round r-1 父块通过 gate（已被 quorum 接受）。块产生→广播→2f+1
peer 接受→下次 prober 探测到（≤ 一个 prober 间隔）→certified。故每轮 +≈(块传播 + prober 间隔)的
延迟 = 认证往返 = Δ_save。OFF 无此等待。

---

## 3. 精确插入点（against `62ee6ada`）

### 3.1 `consensus/config/src/parameters.rs`（已有 `certificate_gate: bool`）
- 复用 `certificate_gate`（:117）作总开关。
- **新增** `certificate_prober_interval_ms: u64`（默认 0 = 不改 prober；>0 时覆盖
  `round_prober_interval_ms` 为该快值）。env `SUI_CONSENSUS_CERTIFICATE_PROBER_INTERVAL_MS`。
  > 或：cert ON 时直接把 `round_prober_interval_ms` 设小。但用独立字段更显式、不污染 OFF 路径。
- prober loop（`round_prober.rs:85`）读 `round_prober_interval_ms`；在 `Parameters` 构造后，
  若 `certificate_gate && certificate_prober_interval_ms>0` 则令 `round_prober_interval_ms =
  certificate_prober_interval_ms`（在 parameters 反序列化后 normalize，或在 prober new 时取 min）。

### 3.2 `consensus/core/src/round_tracker.rs`（加 probe-only quorum 方法）
- **新增** `compute_probed_accepted_quorum_rounds(&self) -> Vec<QuorumRound>`：镜像
  `compute_accepted_quorum_rounds`（:203），但**只用 `probed_accepted_rounds`**（不 max 进
  `block_accepted_rounds`）→ 纯独立通道证书，Δ_save 语义最干净（= prober 介导的认证延迟）。
- 复用现成 `compute_quorum_round`（:263）。

### 3.3 `consensus/core/src/proposer.rs::smart_ancestors_to_propose`（gate 谓词）
- 在 `included_ancestors` 构造（:171-203），cert ON 时对 **quorum_round（父轮）** 的祖先额外要求
  `probed_aqr[ancestor.author()].0 >= ancestor.round()`；不满足 → 不纳入（视同 defer，落入
  `score_and_pending_excluded_ancestors` 或直接跳过）。
- 不满足 2f+1 certified 父块时，现有 smart_select 等待路径（:215 `return (vec![], _)`）优雅等待 →
  轮进自然推迟到 certified → **无死锁**。
- **force 路径（leader timeout）抉择**：:215 的早返仅在 `smart_select` 为真时触发；force（smart_select
  =false）会绕过等待直奔末尾 assert（:333）。**默认令 force 绕过 cert-gate**（force 是稀有活性逃生阀，
  绕过仅微量污染 Δ_save，保活性最稳）；另设 `certificate_gate_strict` 变体让 force 也等待（须 guard
  :333 assert，留作敏感性测试）。本轮先实现"force 绕过"。
- OFF：整个谓词包在 `if self.context.parameters.certificate_gate { ... }`，false 时**逐字节同 stock**。

---

## 4. 正确性论证（minimal-pair 成立前提）

- **OFF ≡ stock**：所有 gate 逻辑在 `if certificate_gate` 内；`certificate_gate=false`（默认）时
  proposer/round_tracker/prober 行为与 `62ee6ada` 逐字节一致。验证：同 genesis/种子/负载下 OFF vs
  原镜像，commit 序列 + checkpoint hash 一致。
- **ON 安全（commit safety 不破）**：gate 只改"哪些已 accept 的块被**引用**"，**不动**
  `base_committer` 的 leader 决策（is_vote/is_certificate/enough_leader_support）与 `linearizer`
  的 DFS。提交规则作用于已存在的 DAG，与提案时引用策略无关（PHASE0_SPIKE §1.5 commit 安全已核）→
  ON 不引入双提交/重排。ON 与 OFF 的**最终提交全序应一致，仅延迟不同**（gate 只延后块进入 DAG 的时机，
  不改因果序）。
- **ON 活性**：只要同步（块能传播），prober 在 ≤1 间隔内把 2f+1 接受探测到 → certified → 轮进。
  force 绕过作为兜底。须 pilot 验证不卡轮（cert ON 的稳态轮速应 ≈ stock 轮速 + Δ_save/轮，而非塌到
  prober 兜底的退化值）。
- **Δ_save > 0 且可测**：ON 的 p50/p95 cadence 应高于 OFF，差值随 prober 间隔/网络 RTT 缩放。

## 5. 语义等价测试（Phase 0 出口）
1. **单测**：`round_tracker` 新方法（probe-only quorum）正确性（仿 `test_compute_accepted_quorum_round`）。
2. **单测/行为**：proposer 在 cert ON 下，certified 不足时返回 empty（等待）、足时正常提案；OFF 路径不变。
3. **集成（pilot）**：fault-free，cert ON vs OFF 同输入 → 提交全序一致（安全）、ON cadence > OFF（Δ_save）、
   两者均不退化到 prober 兜底（活性）。
4. 既有 consensus 测试全过（`SUI_SKIP_SIMTESTS=1 cargo nextest run -p consensus-core`）。

## 6. Build / verify 增量（容器编译，host 缺 clang/cmake）
- **基线**（进行中）：`cargo check -p consensus-core`，预热 `stage9_cargo_registry`/`stage9_target` 卷。
- **增量 1**：parameters.rs 新字段 + round_tracker 新方法 → `cargo check`（应快，缓存已暖）。
- **增量 2**：proposer gate 谓词 → `cargo check` → `cargo nextest -p consensus-core`（新单测 + 回归）。
- **增量 3**：改 `docker/sui/Dockerfile` 由本地 `sui-src` COPY 出实验镜像 `stage9-sui-certgate:local`
  （已有，重建含 gate）→ Phase 1 pilot。
- 迭代提速：可一次性 `docker commit` 一个含 apt 依赖的 `stage9-rustdeps:local`，免每次 apt-get。

## 7. Phase 1+ （Phase 0 绿后）
- pilot 取方差 → power 分析 → Phase A 全标定（cert × ρ × Δ_recover × n × seeds，复用 stage7 编排 +
  已落地的 `SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS` ρ/Δ_recover 旋钮）。
- 直达 §7.2 闭式 `net_advantage ≈ Δ_save − ρ·Δ_recover` 的部署验证（H1–H4，见 EXPERIMENT_PLAN）。

## 8. 风险 + 论文诚实限定（回填受门禁）
- **R-prober 负载**：快 prober 增网络/CPU；n=4/7 实验可接受，但须在 manifest 记录 prober 间隔，且
  cadence 对照须同 prober 间隔（否则 prober 开销混入 Δ_save）。**对策**：OFF 臂也跑同样快 prober（让
  prober 开销在两臂抵消，Δ_save 只剩"引用 gate"的净效应）。← 重要：否则 Δ_save 含 prober 开销偏置。
- **R-force 污染**：force 绕过使强制轮不计认证成本；记录 force 触发率，cadence 主要取稳态非 force 轮。
- **R-probe 时效**：`probed_accepted_rounds` 仅 prober tick 时更新，间隔内陈旧；快 prober 缓解。
- **诚实限定（必入论文，强于 §7.6.2）**：本臂的"证书"是**可用性证书**（2f+1 已接受），**非密码学 2f+1
  签名聚合**；Δ_save 是"等 quorum 接受再引用"这一独立确认轮的延迟，经真实 RoundProber 通道度量——
  **比注入式 sleep 忠实**（真用了独立网络确认），但仍**非**真跑 Bullshark/Narwhal 的 RBC 签名开销。
  实验仍单引擎（Mysticeti 加/去引用 gate），Δ_save 须如实限定为该操作化下的值。

## 9. TODO（本子项目，跨会话）
- [x] 基线 `cargo check -p consensus-core` 绿（2026-05-31，`CARGO_EXIT=0`，3m19s；建了复用 deps 镜像 `stage9-rustdeps:local`）
- [x] **增量 1**：`parameters.rs` 新字段 `certificate_prober_interval_ms`(+env `SUI_CONSENSUS_CERTIFICATE_PROBER_INTERVAL_MS`)+`effective_round_prober_interval_ms()`；`round_tracker.rs` 新 `compute_probed_accepted_quorum_rounds()`(probe-only)；`round_prober.rs` 用 effective interval。`cargo check` 绿（4m21s，仅 dead_code 警告）。
- [x] **增量 2**：`proposer.rs::smart_ancestors_to_propose` cert-gate 谓词（`certificate_gate && smart_select && ancestor.round()==quorum_round && probed_aqr[author].0 < round` → defer）；force 路径绕过（保 :333 assert + 活性）；own block 不 gate（仅 peer 父轮）。`cargo check` 绿（3m04s，警告清除）。
- [x] 单测 `test_compute_probed_accepted_quorum_round`（验证 probe-only 忽略 block 派生信号）已加。
- [x] **lib 测试回归**：`cargo test -p consensus-core --lib -- round_tracker proposer`（SUI_SKIP_SIMTESTS=1）→ **6 passed, 0 failed**（含新单测）。
- [x] **重建实验镜像** `stage9-sui-certgate:local`（含 gate，id afe825da667f）：release 构建 `CARGO_BUILD_JOBS=1`（43m53s，BUILD_EXIT=0）→ extract → `Dockerfile.runtime`。
- [x] **compose 注入**：`compose.multivalidator.yaml` 的 `x-validator-common` 加 `SUI_CONSENSUS_CERTIFICATE_PROBER_INTERVAL_MS`（+ 已有 CERT_GATE/RECOVER_MS）。
- [x] **Phase 1 pilot** ✅（`PHASE1_RESULTS.md`）：n=7 两臂同 prober(75ms)，cert ON 3.14 vs OFF 4.63 ckpt/s → **Δ_save 真实(+102ms/commit,−32%) + 活性无死锁**。`scripts/phase1_certgate_pilot.ps1`。
- [~] **Δ_save 剂量响应标定**（进行中）：`scripts/phase1b_dsave_calibration.ps1` 扫 prober 间隔 {75,250,500}ms × {ON,OFF} × 2reps（**`certificate_prober_interval_ms` = Δ_save magnitude 旋钮**）。
- [x] **Δ_save 标定**（`PHASE1_RESULTS §1b`）：prober 间隔=gate-fidelity 旋钮（非 Δ_save 量级）；faithful Δ_save≈116ms（快 prober）。OFF≈stock（~4.58 ckpt/s 稳）。
- [x] **Phase 2 恢复不对称确证**（`PHASE2_RESULTS`）：同故障+同 Δr=1000，cert ON 恢复便宜（t_resume 37.7 vs 48.2s、fetch 123 vs 196）→ §7.2 crossover 机制真实。
- [x] **联合 net-advantage amortized 扫描**（phase2b）：**非单调、R²=0.02**——amortized-window 是错误观测量（稀释一次性恢复成本 + 高 Δr gate 排斥 recovering 节点的竞争效应）。分解法初算 ρ*≈0.011（Δr=1000）。
- [~] **干净分解式 ρ*(Δr) 映射**（进行中，`phase2c_excess_sweep.ps1`）：扫 Δr×cert 测 t_resume → excess(Δr) → ρ*(Δr)=Δ_save_rate/excess。分析 `analyze_excess_rho_star.py` 就绪。
- [ ] **OFF≡stock 等价**：cert OFF + 慢 prober 的 commit 序/cadence == stage7-sui:local 基线（待对账）。
- [ ] 拟合 ρ*(Δr) → 整理 §7.2 实证材料 →（门禁后）回填 §7.2/§7.6/§9/§10。
