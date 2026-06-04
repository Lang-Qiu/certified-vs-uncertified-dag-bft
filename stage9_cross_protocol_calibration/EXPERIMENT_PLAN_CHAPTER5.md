# Experiment Plan — 第 5 章 ①②③ 归类的部署检验

**Date:** 2026-06-01 · **Status:** plan(待用户批准后进入 run 模式) · **Motivation:** 把论文最核心的归纳性主张从定性推理升级为实验验证。

## 1. 动机

论文第 5 章的核心声称是:去认证后,三个不变量的 enforcement 分别落入:

| 不变量 | 归类 | 代价特征 |
|--------|------|----------|
| 非等价性(non-equivocation) | ① 平移 | 固定开销,不随故障变化 |
| 因果历史完整性(causal-history) | ① 平移 | 固定开销,不随故障变化 |
| 数据可用性(availability) | ② 削弱+补偿 | 或有负债,良好情形≈0,故障下集中爆发 |

这个声称**目前完全是归纳的**(对 Cordial Miners / Mysticeti / Mahi-Mahi 的设计分析),未经受控实验检验。本实验的目标是:**沿故障强度轴扫描,测量三条 enforcement 路径各自的 per-commit 开销,检验"非等价性与因果历史≈平坦,可用性≈良性零/故障爆发"这一可证伪预测。**

如果预测成立:第 5 章从归纳升级为"部署验证的定量发现"。
如果预测被证伪(比如非等价性在 5% 丢包下也暴增):第 5 章归类需要重写——这也比永远不测更诚实。

## 2. Hypothesis(可证伪形式)

**H1(非等价性固定开销):** 非等价性 enforcement 路径的 per-commit 调用次数与累计延迟,在 0%→10% 丢包范围内与故障强度无关(r≈0,斜率≈0)。

**H2(因果历史固定开销):** 因果历史完整性检查(leader 决策时的祖先引文核查)的 per-commit 延迟,在 0%→10% 丢包范围内与故障强度无关(r≈0,斜率≈0)。

**H3(可用性或负债):** 可用性 reconciliation 的 per-commit 触发次数,在 0% 丢包时≈0,在 ≥5% 丢包时显著 >0,且随故障强度单调上升(r>0)。已有 STAGE9_RECOVERY instrumentation 预证了方向;本实验把它从 binary(on/off-path)扩展到 quantitative(每级故障强度的 ρ)。

**H4(结构性不对称):** 综合 H1–H3:可用性路径对故障的弹性(elasticity)严格大于另外两条路径。操作化:可用性路径的 Δ_cost/Δ_loss_rate ÷ (非等价性路径的 Δ_cost/Δ_loss_rate) > 10。

## 3. 三条 enforcement 路径的源码插桩点

基于 stage9 sui-src @ commit `62ee6ada`,已精确定位:

### Path A — 非等价性 enforcement

**文件:** `consensus/core/src/dag_state.rs`
**函数:** `accept_block`(line 291)
**关键检查:** lines 320–336

```rust
// line 320-336
if block_ref.author == self.context.own_index {
    let existing_blocks = self.get_uncommitted_blocks_at_slot(block_ref.into());
    if !self.context.parameters.internal.skip_equivocation_validation {
        assert!(
            existing_blocks.is_empty(),
            "Block Rejected! Attempted to add block {block:#?} to own slot ..."
        );
    }
}
```

**语义:** 验证者不能在自己的 (author, round) 槽位提交第二个区块——这是 **事前预防**(等价被阻止在进入 DAG 之前)。对于其他验证者的等价:不做主动检测,仅在 `get_last_cached_block_per_authority`(line 707)返回等价区块列表供 commit 规则选择(事后中和)。

**插桩方案:** 紧接 `assert!` 之后(或之后正好,因 assert 永不触发——正常路径下 `existing_blocks` 为空),加计数器 + 计时器:

```rust
// instrumentation:
let start = Instant::now();
// (existing check already happens above)
self.context.metrics.node_metrics
    .with_label_values(&["non_equivocation"])
    .inc(); // counter
equivoc_check_latency_us.observe(start.elapsed().as_micros() as f64); // latency
```

**内存/性能开销:** ~2 次 hashmap 查找(`get_uncommitted_blocks_at_slot`),O(1)。

### Path B — 因果历史完整性 enforcement

**文件:** `consensus/core/src/base_committer.rs`
**函数:** `decide_leader_from_anchor`(line 284)
**关键检查:** lines 300–319

```rust
// line 300-319
let potential_certificates = self.dag_state.read()
    .ancestors_at_round(anchor, decision_round);

let mut certified_leader_blocks: Vec<_> = leader_blocks
    .into_iter()
    .filter(|leader_block| {
        let mut all_votes = HashMap::new();
        potential_certificates.iter().any(|potential_certificate| {
            self.is_certificate(potential_certificate, leader_block, &mut all_votes)
        })
    })
    .collect();
```

**语义:** 一个 leader 只有被 ≥2f+1 stake 的 decision-round 区块(reference)所"认证"(即那些区块通过祖先引用了该 leader),才能被 commit。这就是"因果历史完整性"的 enforcement:你必须证明你的祖先链包含该 leader,你的 vote 才被计数。**关键:** 这是纯 DAG 结构操作(读 `dag_state` 的 `ancestors_at_round`,遍历引用),不涉及网络 I/O——如果有 ancestor 不在本地,不是在这里等,而是**commit 根本不触发**(synchronizer 必须先 fetches missing blocks,这是 Path C 的领域)。

**插桩方案:** 在 `decide_leader_from_anchor` 入口和 exit(成功 commit 或 skip)各打时间戳并增加计数器:

```rust
// instrumentation at function entry:
let start = Instant::now();
// ... existing logic ...
// at each commit (certified_leader_block found):
causal_history_commit_count.inc(); // counter per successful commit
causal_history_latency_us.observe(start.elapsed().as_micros() as f64);
```

**内存/性能开销:** `ancestors_at_round` 是 BTree 范围查询 + filter O(k) where k = decision-round block count。每 commit 调用一次。

### Path C — 可用性 reconciliation(PULL fetch)

**已在 stage9 植入,无需新插桩。**

两个已埋点:
- `synchronizer.rs:554-584` (`process_fetched_blocks`:live missing-ancestor fetch) — STAGE9_RECOVERY log + recovery_extra_delay_ms sleep
- `commit_syncer.rs:546-571` (`fetch_once`:batch catch-up fetch) — 同上

**语义:** 当块处理器发现祖先缺失时(如新区块的祖先未被签收),发起对等方的 PULL 获取。这**是**网络 I/O,并且延迟随数据大小和网络条件缩放——物理型不变量 enforce 的代价载体。

### 三条路径的性质对比

| 维度 | Path A(非等价性) | Path B(因果历史) | Path C(可用性) |
|------|:---:|:---:|:---:|
| 操作类型 | 本地 DAG 查询 | 本地 DAG 遍历 | 网络 fetch |
| 代价是否随数据大小缩放 | 否(只看引用/元数据) | 否(只看引用/元数据) | **是**(拉取真实区块内容) |
| 代价是否随故障缩放 | 否(自己的槽位永远唯一) | 否(leader 决策只看已有的引用) | **是**(越多缺失越重拉取) |
| §5 归类预计 | ① 平移 | ① 平移 | ② 削弱+补偿 |

## 4. 实验设计

### 4.1 自变量

| 变量 | 水平 | 理由 |
|------|------|------|
| **故障强度**(loss_rate) | 0%, 2%, 5%, 10% | 0%=benchmark 对照;2%=温和(测"良性零"断言);5%=已知推入超可加(§7.6.1);10%=极端(测 H3 的单调性是否保持) |
| **委员会规模** | n=7 (f=2), n=4 (f=1) | 跨规模复现 |

### 4.2 因变量(per 级别,每 10s 采样窗)

| 量 | 路径 | 含义 |
|---|---|---|
| equivoc_checks | A | 非等价性检查次数 |
| equivoc_latency_us_p50/p95 | A | 每次检查的延迟(微秒) |
| causal_commits | B | commit 决策次数(≈ checkpoint 数) |
| causal_latency_us_p50/p95 | B | 每次 leader 决策的延迟 |
| recovery_fetches | C | STAGE9_RECOVERY 计数(= ρ) |
| recovery_fetch_latency_ms_p50/p95 | C | 每次 fetch 的端到端延迟 |
| cadence_ckpt_s | — | 标准控制可观测:共识 cadence |

### 4.3 故障注入

固定为**跨验证者独立丢包**(已由 §7.6.1 确认在 2% 下呈可加性)——每条对等链路单向施加 netem `loss X%`。

每个 (n, loss_rate) cell 取 **N=5 reps**,每 rep 90s 稳态采样 + 30s baseline warmup。

**总计:** 2(committee size) × 4(loss levels) × 5(reps) = **40 runs**  
**预计墙钟:** ~6h(含 compose teardown/re-up,每 5-run batch ~45min)

### 4.4 分析策略

每条路径在每个故障强度下:

- 先画 scatter plot(per-rep 每路径的 cost vs loss_rate)
- `equivoc_checks` / `causal_commits` :期待恒定的 Y-intercept(无趋势),OLS slope≈0
- `recovery_fetches` :期待在 0% / 2% 时 ≈0,在 ≥5% 时单调正相关
- H4: elasticity ratio = (recovery_fetch_slope / equivoc_slope);如果 equivoc slope ≈0,在分母加小 epsilon 时该比在统计上不可区分于无穷——那就报告"可用性路径有非零弹性,另两条路径弹性与零无统计差异"。

## 5. 证伪判据(事前锚定)

| # | 具体预测 | 确认 §5 成立,如果… | 推翻 §5,如果… |
|---|---------|-------------------|---------------|
| 1 | equivoc checks 与 loss_rate 无关 | slope ≈0, r≈0 | slope >0 且显著 — 非等价性 enforcement 确实随故障增强 |
| 2 | equivoc latency 不随 loss_rate 缩放 | p50/p95 ~ flat across levels | 延迟显著增长 — 非等价性检查可能有间接排队效应 |
| 3 | causal commit 次数 ≈ cadence(正比于 sys throughput,不归因于故障强度) | causal_commits/loss_rate slope≈0 | causal commits 随 loss_rate 显著下降或上升 — leader 决策逻辑对故障敏感 |
| 4 | causal latency ~ flat | slope≈0 | 显著增长 — causal history 遍历可能随 DAG 深度/宽度改变而变慢 |
| 5 | recovery fetches = 0 at 0% loss; >0 & monotonic at 5%+ | 0% level mean≈0;5%/10% levels mean>0 with monotone trend | 0% 时已经显著 >0(则"良好情形≈0"是错的)或 5%/10% level 均值不上升或下降 |
| 6 | recovery fetch slope >> equivoc slope | elasticity ratio >10 或等价陈述(equivoc slope 与零无差异) | equivoc slope 与 recovery slope 量级接近 — 那么①②③的二元区分不成立 |

**如果多项同时推翻:** 第 5 章的归类需要从"①②③三分类"重写为更窄的主张(比如"全部三个维度都有一定故障弹性,但可用性维度最强")。这本身就是一个可发表的诚实修正。

## 6. 工作量和阶段

| 阶段 | 工作 | 预计时间 |
|------|------|---------|
| **Phase 0** | 部署前确认:插桩代码审查 (dag_state.rs + base_committer.rs) | 0.5h |
| **Phase 0b** | Path A + Path B 计数器/计时器插入, Path C 已有√ | 1h |
| **Phase 0c** | `cargo check -p consensus-core` confirm 编译绿 | 10min(已有 deps 镜像) |
| **Phase 0d** | release 构建 (`CARGO_BUILD_JOBS=1`,host 16GB) | ~40min |
| **Phase 0e** | 镜像重建 + boot 冒烟(ckpt 稳增,检查 metrics endpoint 三条 counter 都在) | 15min |
| **Phase 1** | n=7 扫描:4 loss levels × 5 reps | ~3h |
| **Phase 2** | n=4 扫描:4 loss levels × 5 reps | ~3h |
| **Phase 3** | 独立分析:提取 metrics,计算斜率/r/elasticity ratio | 1h |
| **Phase 3b** | (可选) n=10 单点验证(仅 0%/5%/10%,2 reps) | ~2h |
| **总计** | | **~11h wall clock** |

## 7. 诚实边界

1. **Path C 已在之前实验中量测,Path A/B 是本实验的全新技术路径。** 我们的 H4 结论将来自同一部署上三条路径的**相对弹性**,而非绝对开销——这控制了机器/镜像/编排的批次效应。
2. **插桩开销本身计入测量:** P ath A/B 的 instrumentation(Instant::now()+atomic inc)本身 ~10-50ns,远低于被测量的检查(μs 级),不影响定性结论。
3. **"良性情形≈0"对 Path C 的操作化边界**:Mysticeti 使用 PUSH(广播)先于 PULL(fetch),所以 0% 丢包时的 "STAGE9_RECOVERY = 0" 这个预测实际上已在之前的 smoke tests 中观测到(5% 丢包 → 0 fetches,因为 PUSH 窗口未溢出)。2% 丢包也可能为 0——这对"或有负债仅故障下爆发"论点其实是**加强**而非削弱(它甚至比 2% 更早开始就为零)。
4. **因果历史路径的测量范围**:`decide_leader_from_anchor` 捕获的是 leader 决策时的因果历史核查——但因果历史完整性也部分在 `linearize_sub_dag`(line 156)进行(遍历祖先图、检查祖先都在 dag_state 内)。后者 cost 按 commit 分摊——如果 Path B 的 `decide_leader_from_anchor` 是平的,但整体因果历史开销能通过 `scope_processing_time` 的 `Linearizer::collect_sub_dag_and_commit` 标签(已存在)来验证。本实验默认用 `decide_leader_from_anchor`;如果需要,追加 `Linearizer::collect_sub_dag_and_commit` 的 latency 分布作为补充测量。

## 8. 预期论文产出映射

| 实验结果 | 论文插入位置 | 插入方式 |
|---------|------------|---------|
| H1+H2 确认(两路径 flat) | §5.2 / §5.3 各加一段 | "这一归类得到了部署实测的定量支持:非等价性 enforcement 的 per-commit 开销在 0%–10% 丢包范围内保持平坦(图 5-X)..." |
| H3 确认(可用性故障爆发) | §5.4 加一段 | 并入已有的 §7.6.1 超可加证据,形成"两个透镜同一结论" |
| H4 确认(结构性不对称) | §5.6 隐性代价台账 | 把台账从定性表升级为 +定量 elasticity ratio 表 |
| 如果某项被推翻 | §5 开头加诚实标注 + §9 扩写 | "部署实测对 ①②③ 分类提供了部分支持(…)但在(…)维度上观察到了偏离,将其完整刻画留作未来工作" |
