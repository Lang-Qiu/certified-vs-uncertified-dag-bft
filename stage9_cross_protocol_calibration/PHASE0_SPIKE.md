# Phase 0 Spike — cert-gate 在 Sui/Mysticeti 的可行性

> 目的：确认「在同一 Sui binary 上把认证做成可开关的 certificate-gate」是否可行，并定位插入点 + 设计语义等价测试。
> 状态（2026-05-30，已更新）：源码已拉取（sparse `consensus/` @ `62ee6ada`，位于 `stage9_.../sui-src`）；cert-gate 插入点**已定位并验证**（见 §1.5）。**关键结论：工程风险较原估计大幅下降**——Sui 已经在算「区块是否被法定多数接受」，cert-gate 可复用该机制，无需从零重建 RBC。

---

## 1. 已确证事实（读自 stage7 Dockerfile / compose —— 可靠）

| 项 | 值 | 来源 |
|---|---|---|
| 固定 commit | `62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a` | `docker/sui/Dockerfile:3`, `compose/compose.yaml:8` |
| 上游 | `https://github.com/MystenLabs/sui.git`（`--depth 1`，构建时 clone 后丢弃） | `Dockerfile:17-21` |
| 构建 | `cargo build --locked --release --bin sui --bin sui-node`，Rust 1.92 | `Dockerfile:24-25` |
| 镜像 | `stage7-sui:local` | `compose*.yaml` |
| 运行 | `sui start --force-regenesis ...`（单进程本地网） | `Dockerfile:44` |
| **本地源码** | **无**（构建时临时 clone）→ cert-gate 须先建持久可改的 checkout | — |

**结论**：fork 必须基于 `62ee6ada` 这一精确 commit（保持与阶段二 290+ rep 数据同源、可复现）。

---

## 1.5 VERIFIED — cert-gate 插入点已定位（2026-05-30，against `62ee6ada`）

### 提案路径（已读源码确认）
`core.rs::try_propose`（:560）→ `proposer.rs::ValidatorProposer::try_new_block`（:349）→ **`smart_ancestors_to_propose`（proposer.rs:131-345）** 选祖先。

### 关键事实
1. **确认 uncertified（无 per-block 证书）**：round-(r-1) 区块一旦被 *accept* 进 DAG、且本地凑齐父轮**法定多数**（`parent_round_quorum: StakeAggregator<QuorumThreshold>`，proposer.rs:205-222），即可被 round-r 提案直接引用。**没有等待 B 自身集齐 2f+1 签名/证书的步骤**——这正是论文所述被移除的认证步。
2. **Sui 已在算"证书信息"**：`RoundTracker` 产出 `accepted_quorum_rounds[author]` = 「一个**法定多数**已 accept 该 author 区块所达到的轮次」（proposer.rs:155 取用；:253-331 已用于 excluded-ancestor 路径，注释见 :256「A quorum of validators reported to have accepted blocks ... up to the low quorum round」）。这等价于"该区块已被法定多数持有"——即认证的**延迟/可用性内核**。
3. `protocol_config` 开关是现成机制（代码已用 `enable_v3()`、`transaction_voting_enabled()`、`bad_nodes_stake_threshold()`）→ cert-gate 用一个新 protocol_config flag 控制即可。

### cert-gate 操作化（已据源码定型，风险大降）
在 `smart_ancestors_to_propose` 的父轮祖先纳入处（proposer.rs:171-222）加一个**祖先资格谓词**，复用已算好的 `accepted_quorum_rounds`（:155）：

- **cert ON（certified 臂）**：父轮祖先 B 仅当 `B.round() <= accepted_quorum_rounds[B.author()].0`（即一个法定多数已 accept B）时才可被引用 → 强制"被法定多数持有后才引用"，**多花一个认证轮** = Δ_save 的来源。
- **cert OFF（stock Mysticeti）**：保持现行为，直接引用已 accept 的最新父轮区块。

**→ 不必从零重建 RBC**：复用 `RoundTracker` / `accepted_quorum_rounds` / `StakeAggregator`。EXPERIMENT_PLAN 的 Risk 1（最高风险）由此**大幅下降**。

### ⚠️ 诚实性修正（必入论文）
该操作化捕获的是认证的**延迟/可用性成本**（"被引用 ⟹ 法定多数已持有"），**不是**密码学意义的 2f+1 签名证书。这与论文的 availability-enforcement 框架一致（论文关心的就是可用性强制时机，非加密形式），但 Δ_save 须如实表述为"等待法定多数持有再引用"这一轮的成本，而非"RBC 签名聚合"的成本。§4 的语义等价测试相应改为验证不变量「cert ON 下被引用的祖先必已被法定多数 accept」。

### 已核 — recovery 路径 + commit 安全（2026-05-30，against `62ee6ada`）

**reconciliation / 恢复机制（= 论文 Δ_recover/ρ 的真实对应物，已确认）**
- `block_manager.rs::try_accept_one_block`（:279）：收到的区块若引用了本地没有的祖先，则被**挂起(suspend)**，缺失祖先记入 `missing_ancestors`（:281-374）；祖先补到后 `try_unsuspend_children_blocks` 解挂（:383）。
- `synchronizer.rs`：两条拉取路径（doc :227-240）——(1) 收到区块时拉其缺失祖先（`fetch_blocks` :188；server 端入口 `authority_service.rs::handle_fetch_blocks` :411）；(2) 周期任务 `start_fetch_missing_blocks_task`（:925）每 200ms 拉 `get_missing_blocks()`。
- **→「数据缺失 → 挂起 → 拉取恢复」正是论文或有负债的机制本体。**

**Phase A 旋钮落点（合成 ρ / 调 Δ_recover）**
- ρ：在 `block_manager::try_accept_one_block` 以概率 ρ 把本应在场的祖先当作 missing → 触发 suspend + synchronizer 拉取。
- Δ_recover：在 `synchronizer::fetch_blocks_from_peer`（:489）注入可配置延迟 / 限并发带宽。

**Phase B 数据扣留钩子落点**
- `authority_service.rs::handle_fetch_blocks`（:411，server 端）：Byzantine 节点对自己（或全部）区块的 fetch 请求拒绝/返回空 → 迫使诚实节点恢复失败、重试 → 涌现 ρ↑。

**round_prober 与 cert-gate 的耦合（设计须知）**
- `round_prober.rs::probe`（:108）周期向 peer 问「最高 accepted/received 轮次」，`update_from_probe`（:203）喂给 RoundTracker → 产出 §1.5 cert-gate 依赖的 `accepted_quorum_rounds`。**数据扣留会经此压低 withholder 的 accepted 轮次 → 同时影响 cert ON 的祖先资格与 ρ**。这是真实耦合（与 §7.4 ρ–Δ_recover 耦合呼应），Phase B 须监控。

**commit 安全（cert-gate 不破坏，已确认）**
- `base_committer.rs` 的提交规则自带 certificate 概念：`is_vote`（r+1 引用 leader，:219）、`is_certificate`（r+2 引用 2f+1 voters，:231）、`enough_leader_support`（2f+1 证书直接提交，:370），外加 anchor 间接规则。
- 这套 3 轮决策规则作用于**已存在的 DAG**，**与提案时祖先如何被引用无关**。
- **→ cert ON/OFF 只改 DAG 的时延/形状，不动 commit 安全前提**（无两个冲突 leader 被提交的不变量来自决策规则本身）。§4 等价测试相应改为：**fault-free 下 cert ON 与 OFF 的已提交交易顺序应一致（一致性/安全），仅 cadence（时延）不同**。

### Phase 0 结论（feasibility 已坐实）
cert-gate 可行、安全保持、recovery 旋钮与扣留钩子落点明确。**无需从零重建 RBC**。

---

## 2. Phase 0 实现方案（编码中，2026-05-30）

### 构建环境（已确认）
- crate = `consensus-core`（edition 2024）;host Rust = **1.92.0**（与 Dockerfile `rust:1.92` 一致，rustup 按 repo pin 自动同步）;E: 余 392 GB。
- **Windows 长路径坑**：`external-crates/move/crates/move-compiler` 的 IR 测试 fixture 路径超 260 字符 → 首次 `sparse-checkout disable` 失败。该 crate **已被 root workspace `exclude`**（`Cargo.toml:33`），构建 `consensus-core` 不需要它。修复 = `git config core.longpaths true` 后 `git reset --hard` 完成 materialize（那些文件成为无害冗余）。
- dev 反馈环：`cargo check -p consensus-core`（首次需经代理 7897 拉 crate 依赖,设 `CARGO_HTTP_PROXY`/`https_proxy`）。
- 最终实验镜像：改 `docker/sui/Dockerfile` 由本地 `sui-src` `COPY` 构建（替代 `git clone`），保证用的是带 cert-gate 的 binary。

### 改动点（最小）
1. **toggle** — `consensus/config/src/parameters.rs::Parameters` 加字段:
   ```rust
   #[serde(default = "Parameters::default_certificate_gate")]
   pub certificate_gate: bool,
   ```
   `default_certificate_gate()` 读环境变量 `SUI_CONSENSUS_CERTIFICATE_GATE`（"1"/"true"→true，否则 false）→ 既保持 stock 默认 OFF，又能由 docker-compose 逐容器 env 翻转，无需改 `sui start` CLI。
2. **gate** — `consensus/core/src/proposer.rs::smart_ancestors_to_propose`:父轮祖先纳入处（:171-222）加谓词:当 `self.context.parameters.certificate_gate` 为真时,仅当 `ancestor.round() <= accepted_quorum_rounds[ancestor.author()].0`（已被法定多数 accept）才纳入;否则不纳入(待下一轮再引用)。`accepted_quorum_rounds` 已在 :155 算出，直接复用。

### 语义等价测试（minimal-pair 成立的前提）
- **OFF ≡ stock**:`certificate_gate=false` 时 `smart_ancestors_to_propose` 逻辑与原版逐字节一致（谓词包在 `if certificate_gate` 内）。
- **ON 正确性**:fault-free、同 genesis/种子/负载下,cert ON vs OFF 的**已提交交易顺序必须一致**（一致性/安全,由 `base_committer` 决策规则保证,与引用无关）;仅 **cadence（时延）不同** = Δ_save 的来源。
- **活性**:cert ON 须确认不会因 gate 过严停滞（gate 只把引用推迟到法定多数 accept,正常网络下次轮即满足;须在 pilot 验证不卡轮）。

### 本轮范围
仅 cert-gate flag + gate + 等价测试。Δ_recover/ρ 旋钮（`block_manager`/`synchronizer`）与数据扣留钩子（`authority_service`）属 Phase A/B,后续迭代。

### 实现进展（2026-05-30 续）
- ✅ **toggle 已落地** `parameters.rs`：`Parameters::certificate_gate`（默认 false；env `SUI_CONSENSUS_CERTIFICATE_GATE` 可翻）+ `default_certificate_gate()` + 手写 `Default` impl 项。
- ✅ **时序确认**（读 `round_tracker.rs`）：`accepted_quorum_rounds` 由 `block_accepted_rounds` **每轮随区块流更新**（非仅 5s 探测）→「被法定多数 accept」约在区块产生后 **~1 轮**成立 → cert-gate 恰好加一个认证轮 = Δ_save，**不会 5s 卡顿**。
- ✅ **构建环境**：host 有 protoc、缺 clang/cmake → 不在 Windows 本机编译；改用 `rust:1.92-bookworm` 容器（镜像 Dockerfile 的 apt 依赖）跑 `cargo check`，经 7897 代理。
- ⚠️ **设计抉择（gate 放哪）—— 待定**：`proposer.rs:333` 有 `assert(parent_round_quorum reached)`。cert-gate 只允许引用 quorum-accepted 父轮祖先，在 `force`（leader timeout）路径下可能触发该 assert。两条实现路线：
  - **D1 提案侧门（proposer）**：在 `smart_ancestors_to_propose` 限制祖先；quorum-accept 未达则 `return empty`（等待），force 下亦等待（须 guard 那个 assert）。侵入小；改变 force/leader-timeout 语义；须 pilot 验证不卡活性；模拟的是"引用门"。
  - **D2 轮进门（threshold-clock）**：把**轮推进**本身 gate 在「前一轮已被 2f+1 quorum-accepted」→ 提案时父轮天然 certified，proposer/assert 不动。最忠实于 certified-DAG（轮=证书轮）；更侵入（改 threshold-clock/round-advance），注入点待核。

### ⚠️ 关键阻塞发现（2026-05-30，用户选 D2 后深挖）— 修正先前 de-risk

**朴素的 D2（及 D1）会退化/死锁，根因是循环依赖：**
- Mysticeti **没有独立的投票/证书消息**。「区块被法定多数 accept」(`accepted_quorum_rounds`) 这个信号**本身来自后续轮的提案引用**（`round_tracker::update_from_verified_block`：X 的 round-r 块引用 r-1 → 记录"X accept 了 r-1"）。
- 若把「round r 提案」gate 在「r-1 已 2f+1 quorum-accept」：所有节点到 r 都被 gate → 无人提 r → 没有 round-r 块去引用 r-1 → r-1 永不被 quorum-accept（仅靠 `round_prober_interval`(prod 5s) 探测兜底）→ **轮速退化到 ~5s/轮**，Δ_save 测量被毁。
- D1（gate 引用 + `smart_ancestors_to_propose` 需 `parent_round_quorum` 在 r-1）同理循环。

**根因**：certified-DAG 的证书是一个**独立于"下一轮提案"的确认轮**（RBC/投票）；Mysticeti 去掉了它，用"后续轮引用"隐式替代。**忠实重建认证 = 必须把那个独立确认轮加回来**（轻量投票/ack 通道），而非复用 `accepted_quorum_rounds`。→ **先前「无需重建 RBC」的 de-risk 过于乐观，工程 Risk 回升。** `Parameters::certificate_gate` toggle 已落地但默认 off、暂无生效逻辑（无害）。

**修正后的候选路线（待用户定向）**：
1. **加轻量证书/投票层**（忠实，高工作量）：每区块加 2f+1 ack 独立通道，引用 gate 在证书上 ≈ 重建 certified-DAG 认证轮。
2. **"证书前沿"引用、不 gate 轮推进**（中-高；语义可辩护、非逐字节）：保持每轮提案（后续轮即"投票"），但被引用祖先限制为已 2f+1 被引用的"证书"块（≈2 轮前），重排 proposer quorum 逻辑用证书前沿；须确认不破 `base_committer` 轮算术。
3. **加速 round_prober 当 ack 通道**（hacky，改动小）：prober 间隔降到 ~轮时延，用"探测到 2f+1 已 accept"当证书信号 gate 轮推进；耦合脆弱、增网络负载。
4. **重审 certified 臂来源**：查 62ee6ada 是否仍保留可选 Narwhal/Bullshark certified 路径 →**已确认移除**（仅剩 `ConsensusChoice::Narwhal` enum 残桩，无 narwhal crate）。route 4 出局。

### Route 2 设计现状 + 战略评估（2026-05-30，读 linearizer/commit 后）

- 提交链：`core.try_commit` → `committer.try_decide`（`base_committer`：leader@r、votes@r+1、certs@r+2、`wave_length=3`，leader 提交时已要求 2f+1 证书）→ `linearizer.handle_commit`。
- **Route 2 两种实现都与 commit wave 结构纠缠**：
  - 引用重排（reference r−2 证书）→ 改 DAG 基本引用轮 → `base_committer` wave/decision-round 轮算术大概率受影响，须重证安全/活性。
  - commit-gating（延迟 leader 提交至因果史 certified）→ 与"leader 已需 2f+1 证书"重叠，要额外"每逻辑步 +1 轮"须深入 `universal_committer` wave 逻辑。
- **结论**：忠实 Δ_save（认证）emulation 是一个**需对 committer wave 逻辑仔细设计 + 安全/活性重证 + 行为测试**的多阶段子项目，非 Phase 0 小改；本会话无法完成并验证（首次 cargo build ~30min+）。

### ⭐ 战略再排序建议
论文**中心主张是或有负债（ρ·Δ_recover，§7.3/§7.4）**；其钩子（`block_manager` suspend + `synchronizer` fetch + `authority_service` 扣留）**干净、无循环依赖、可独立 instrument**。反而 Δ_save（认证）侧的忠实 emulation 最难。
→ 建议**先做 ρ·Δ_recover 侧（Phase A 旋钮 + Phase B 扣留敌手）**——论文核心 + 技术干净；Δ_save 侧改为 (a) 暂用文献/单轮 RBC 成本作量级锚，或 (b) 后续单独立项做忠实 cert-gate。如此实验的主要科学价值（条件化结论的或有负债定量化）不被 Δ_save 工程难点卡住。`Parameters::certificate_gate` toggle 已就位，留作后续 cert-gate 子项目的接口。

### 实现进展 2（2026-05-30 续）— Δ_recover 旋钮已落地
- ✅ `Parameters::recovery_extra_delay_ms`（默认 0；env `SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS`）+ default fn + `Default` impl（parameters.rs）。
- ✅ 注入点 `synchronizer.rs::process_fetched_blocks`（恢复 chokepoint，两条 fetch 路径都经此）：每次 reconciliation fetch 前 `sleep(recovery_extra_delay_ms)` → 直接为每次恢复加 Δ_recover。复用已有 `Duration`/`sleep` 导入。
- ⏸️ `Parameters::certificate_gate` toggle 在位但无生效逻辑（Δ_save 侧待 cert-gate 子项目）。

### 构建验证状态 — ⛔ 阻塞于 Docker Desktop 未启动
- consensus 编辑（cert_gate toggle + recovery 旋钮）**尚未编译验证**：host 缺 clang/cmake/MSVC → 须容器编译；本次 `docker version` 报 Linux Engine pipe 未找到 = **Docker Desktop 未运行**。
- **可恢复的容器 cargo check**（Docker Desktop 启动 + Clash「Allow LAN」让 `host.docker.internal:7897` 可达后）：
  ```bash
  MSYS_NO_PATHCONV=1 docker run --rm \
    -v "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage9_cross_protocol_calibration/sui-src:/src" \
    -v stage9_cargo_registry:/usr/local/cargo/registry -v stage9_target:/src/target \
    -e http_proxy=http://host.docker.internal:7897 -e https_proxy=http://host.docker.internal:7897 \
    -e CARGO_NET_GIT_FETCH_WITH_CLI=true rust:1.92-bookworm \
    bash -lc "apt-get update && apt-get install -y --no-install-recommends clang cmake protobuf-compiler libssl-dev pkg-config llvm git && git config --global http.proxy http://host.docker.internal:7897 && cd /src && cargo check -p consensus-core 2>&1 | tail -80"
  ```
- 绿后下一步：(1) 改 `docker/sui/Dockerfile` 由本地 `sui-src` COPY 构建实验镜像；(2) Phase A 用 `SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS` 扫 Δ_recover；(3) 合成 ρ 旋钮（`block_manager::try_accept_one_block` 概率性假缺失）+ Phase B 扣留钩子（`authority_service::handle_fetch_blocks`）。

---

## 2. Step A — 建立可修改的源码 checkout（工具恢复后执行）

**先读后建**：先用 blobless + sparse 只拉 `consensus/`（几 MB，供 Step B 核对），确认可行后再展开全树供构建。

```powershell
# 代理（Clash）：clone 前确认 127.0.0.1:7890 在听；下面用 -c 临时注入，不污染全局 config
$proxy = "http://127.0.0.1:7890"
$dst   = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage9_cross_protocol_calibration\sui-src"

git -c http.proxy=$proxy clone --filter=blob:none --no-checkout https://github.com/MystenLabs/sui.git $dst
Set-Location $dst
git sparse-checkout init --cone
git sparse-checkout set consensus            # 只拉 consensus crate（+ 顶层 workspace 文件）
git -c http.proxy=$proxy fetch --depth 1 origin 62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a
git checkout --detach 62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a
```

构建阶段（Phase 0 验证镜像时）再 `git sparse-checkout disable` 展开全树；blobless 会按需补 blob。
**备选**（工具仍不可用时，用户可手动跑上面的命令，或直接 `! git ...` 在会话里执行）。

---

## 3. Step B — cert-gate 插入点【假设，待核对】

> ⚠️ 以下基于对 Sui/Mysticeti 架构的既有知识，**Sui 迭代快，`62ee6ada` 的实际布局可能不同**。拉到源码后逐条核对（见 §6 清单）。所有 file/函数名标注【待核】。

### 3.1 认证在两类 DAG 里的差别（概念，稳）
- **certified DAG（Bullshark/Narwhal）**：区块被其他区块引用前，须先收集 2f+1 签名形成 **certificate**（一轮 RBC）。
- **uncertified DAG（Mysticeti）**：区块一旦被接收/接受即可被直接引用；"隐式认证"来自跨轮的 commit 规则，**显式 per-block RBC 证书被移除**。

### 3.2 预期相关模块 `consensus/core/src/`【待核】
| 文件【待核】 | 角色 | 与 cert-gate 关系 |
|---|---|---|
| `core.rs` | `Core::try_new_block` 提案、选祖先(ancestors)、threshold clock | **主插入点**：选哪些区块作新块祖先 |
| `block_manager.rs` | 挂起/接受区块、祖先可用性 | 候选：标记区块「可被引用」的闸门 |
| `dag_state.rs` | 内存 DAG、`accept_block`、recent blocks | 候选：祖先资格谓词 |
| `linearizer.rs` / `commit*.rs` | commit/线性化规则 | 不改（保持 commit 语义不变） |
| `synchronizer.rs` / `authority_service.rs` | 拉取缺失区块 | **reconciliation/恢复路径** → ρ/Δ_recover 旋钮 + 扣留钩子在此 |
| `block_verifier.rs` | 区块校验 | 可能承载「证书已满足」校验 |

### 3.3 cert-gate 的最小语义【设计假设】
新增一个**祖先资格谓词** `is_referenceable(B)`：
- **cert ON**：`B` 仅当本地已观察到 ≥ 2f+1 个「投票」（即 round(B)+1 中引用 B 的区块，或对 B 的显式签名集）后才可被纳入新块祖先。等价于"等 B 形成证书"。
- **cert OFF（stock）**：`B` 一旦被 `accept` 即可被引用（原生 Mysticeti 行为）。

开关由 `protocol_config` / 启动参数注入（沿用 stage7 的 env/配置注入路径），便于实验编排逐 cell 切换。

---

## 4. Step C — 语义等价测试设计（minimal-pair 成立的前提）

cert-gate 若要可信，须证明两件事：

1. **OFF ≡ stock Mysticeti**：开关关闭时，行为与未改动的 `62ee6ada` 逐位/逐事件一致。
   - 测法：同 genesis、同种子、同输入负载，跑改造版(OFF) vs 原版，对比 commit 序列、checkpoint 内容哈希、cadence 分布 → 应无差异（允许调度抖动内的统计等价）。
2. **ON 真的实现了「证书后引用」**：开关打开时，任一被引用的区块在被引用时刻确已积累 ≥ 2f+1 引用/签名。
   - 测法：加不变量断言/日志，扫描整条执行，**反例数 = 0**；安全性（无 equivocation 提交）、活性（仍能推进 commit）不破。

两测皆过 → 唯一变量=认证强度，§3.3 minimal-pair 在部署层成立。任一不过 → minimal-pair 破裂，须回退到 EXPERIMENT_PLAN 的其它识别策略。

---

## 5. Step D — 恢复旋钮 + 数据扣留钩子【假设，待核】

- **reconciliation 旋钮（合成 ρ / 调 Δ_recover）**：在 `synchronizer` 的缺失区块拉取路径插入——以概率 ρ 强制把某些已可用祖先标记为「需恢复」触发 fetch；Δ_recover 用 fetch 批量大小 / 恢复带宽限制调。
- **数据扣留拜占庭钩子（Phase B）**：让指定 authority 广播区块头/引用但对 fetch 请求不返回 payload，迫使诚实节点走恢复路径，使 ρ 由敌手涌现。
- 两者均应由配置/env 开关控制，复用 stage7 编排注入。

---

## 6. 工具恢复后的核对清单（against `62ee6ada`）

- [ ] `consensus/core/src/` 实际文件列表 vs §3.2 预期
- [ ] `Core` 选祖先的确切函数与数据结构（祖先从哪来、何时算"可引用"）
- [ ] Mysticeti 是否已有 per-block 投票/签名聚合可复用（决定 cert ON 是"复用"还是"新建"机制）
- [ ] `protocol_config` 注入开关的现成机制（feature flag / protocol version gate）
- [ ] synchronizer 的缺失区块 fetch 入口（旋钮 + 扣留钩子落点）
- [ ] commit/linearizer 是否依赖"已认证"假设（改 ON/OFF 是否会动 commit 安全性证明前提）—— 这关系到 §4 测试 2 的安全性断言

---

## 7. 现存风险（更新自 EXPERIMENT_PLAN Risk 1）

- **最大未知**：Mysticeti 的 commit 规则本身可能隐式依赖"区块经足够引用才提交"，与显式 cert-gate 部分重叠 → cert ON 的 Δ_save 可能小于预期（"加证书"只增加一点引用前等待）。这反而是有意思的实证发现，但需在 §4 测试中量化 ON 究竟改变了什么。
- 全树展开 + `cargo build --locked` 在 Rust 1.92 下首次构建耗时与磁盘（Sui 工作区大）；先验磁盘（E: 余量）。
- 代理依赖：Clash 不开则 clone 失败（见 `[[theory-to-deployment-plan]]` 环境注记）。

---

## 8. 路由再裁定（2026-05-31，深读 proposer / base_committer / universal_committer / linearizer 后）

> 触发：用户选「启动 certified 对照臂」。本节据**实际源码**（非既有知识）重排候选路由，并定位一个**致命的 Δ_save≈0 陷阱**与一个**确证的死锁**，收敛到两条真正可行的路由。

### 8.1 实读确证的三个事实
1. **认证机制已存在，但只作用于 leader**：`base_committer.rs::is_vote`(:219)/`is_certificate`(:231)/`enough_leader_support`(:370) —— leader 须集齐 2f+1 votes（证书）才提交（`try_direct_decide` :86-117 返回 `Commit`/`Skip`/`Undecided`）。**非 leader 区块不单独认证**，靠 leader 的因果史被 `linearizer.rs::linearize_sub_dag`(:156) DFS 顺带提交（提交 gc_round 以上所有未提交祖先，带 set_committed 单调 + 双提交断言）。
2. **提交序 = 已决 leader 的最长前缀**：`universal_committer.rs::try_decide`(:94-106) —— 首个 `Undecided` 截断前缀。**出块/轮进不被 committer 门控**。→ 这是一个干净的「停顿」原语：把某 leader 置 Undecided 即停顿其后全部提交，轮时钟照常推进，证书补齐后下次 try_decide 自动续上 → **延迟提交、不改顺序**。
3. **proposer 的 2f+1 父轮断言**：`smart_ancestors_to_propose`(:205-222, 断言 :333) —— round r 须见 2f+1 个 round r-1 父块方能提案（threshold clock）。:215 的 smart_select 未达阈值时优雅 `return empty`（等待），非 panic。

### 8.2 被否决的路由（实读后排除）
- **commit-time 子 dag 认证门（曾以为最优）→ Δ_save≈0，否决**。稳态下 leader@r 在 r+2 拿到证书时,其因果史(round ≤ r)的非 leader 块**早已**被 2f+1 个后轮块引用 = 已认证。故「提交前要求整条子 dag 认证」几乎不增延迟。这正是 §7 Risk 1 的极端实现 —— Mysticeti 的 leader 认证已把近期历史拖到 certified 态。**用 §8.1.2 的停顿原语也救不了：没有可停顿的未认证块。**
- **reference-gate（gate 在「被引用前须 2f+1 认证」）→ 确证死锁**。与 §"关键阻塞发现"一致：Mysticeti 无独立 ack，「B 被 quorum accept」之信号本身来自后轮引用 → gate round-r 提案于「r-1 已认证」→ 无人提 r → r-1 永不认证 → 轮速塌到 prober 兜底(5s)。`proposer.rs:333` 的 2f+1 父轮断言亦因此无法满足。

### 8.3 收敛的两条可行路由（**待用户定向**）
- **Route D —— 引用成熟延迟（emulation，推荐）**：cert_gate ON 时,在 proposer 选祖先处（`smart_ancestors_to_propose` 的 included_ancestors 构造）**排除「创建未满 `cert_delay_ms`」的父块**,模拟认证轮往返 = 一个块「成熟可被引用」前的等待。所有节点对称成熟 → 满 cert_delay 后 2f+1 父块到位、轮进、smart_select 阈值满足 → **无死锁**(时间门,非引用门)。Δ_save = cadence(cert_delay>0) − cadence(0),与已落地的 Δ_recover 旋钮**方法学对称**(同为 `Parameters` 字段+env 注入式延迟)。
  - ✅ 可近期实现+容器编译+语义等价测试验证(OFF≡stock 逐字节；ON 仅延迟不改提交序)。✅ 让 Δ_save/Δ_recover/ρ 三旋钮**同 binary 共扫** → 直接在真实部署上检验 §7.2 闭式 `net_advantage≈Δ_save−ρ·Δ_recover`(H2)及其偏离(H3,§7.4 耦合)。
  - ⚠️ 诚实限定(强于 §7.6.2)：**latency emulation，非密码学 2f+1 证书**；测的是认证「成本结构/标度」,非签名聚合开销。`certificate_gate: bool` 拟扩为/补 `certificate_extra_delay_ms: u64`。
- **Route A1 —— 忠实 ack/投票通道（high effort）**：为每块加独立 2f+1 ack 通道(新消息类型),引用 gate 在真实证书上 = 真正重建 certified-DAG 认证轮。最忠实,但**多会话工程**:新网络消息 + 安全/活性重证 + 行为测试;首次 cargo build ~30min+。风险:本环境难以一会话内完成并可靠验证。

### 8.4 建议
推荐 **Route D**:与论文已采用并披露的 §7.6.2 注入式旋钮方法学一致、可近期交付、且直达 §7.2 模型验证(论文核心)。Route A1 的密码学忠实度超出论文所需(论文要的是**成本结构**,非签名开销),宜留作独立后续。**回填仍受 `[[paper-integration-approval-gate]]`**：Δ_save 须如实表述为「认证轮往返的注入式延迟 emulation」。
