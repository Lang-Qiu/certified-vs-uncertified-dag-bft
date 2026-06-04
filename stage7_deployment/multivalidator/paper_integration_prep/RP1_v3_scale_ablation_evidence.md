# RP-1 v3:跨规模/跨强度部署实证作为 §7.6 的实证支柱（独立种子复测修正版）

> v3 更新于 2026-05-30 —— 在 v2 基础上按独立种子复测（种子 20260526，权威报告
> `reports/stress_test_combined_conclusion_v3_20260526.md`）作两项**结论级修正**：
>
> 1. **删除** v2 的「两条压力轴非线性叠加 / 共享底层瓶颈」论点 —— 该论点建立在
>    「n=4 ablation @2% = super-additive (1.16)」之上，而该 cell 在独立种子下**未复现**
>    （复测 0.97，干净可加），原结论为**单种子假阳性**。
> 2. 核心结论从「两轴均破坏可加性」收窄为「**仅故障强度轴驱动超可加；BFT 边界轴在中强度下无独立效应**」。
>
> v1/v2 (`RP1_scale_ablation_evidence.md`, `RP1_v2_*`) 保留供对照。
> 论文重定位深度 = **Option A（实证支撑的理论论文）**，本 RP 为该方案的 §7.6.1 来源。

## 1. 触及章节（不变）

- §7.6「条件化结论」末尾（`final_paper.md` 第 349 行之后，新增 §7.6.1）
- §7.7「面向设计者的判定程序」第 4 点边界情形（可引用，不强制改）
- 摘要末段（中文第 7 行 / 英文第 15 行，各追加一句）

## 2. 证据来源（v3）

- `reports/stress_test_combined_conclusion_v3_20260526.md` §1–§2（**权威主参考**，含全部修正后数字）
- `reports/test1_qdiscfix_result_20260525.md`（Test 1 qdisc 修复后）
- `reports/summary_true_replica_20260526.md`（100 rep 独立种子复测 true-cadence）
- `reports/scale_ablation_n4_vs_n7_20260525105002.md`（跨规模对照）

## 3. 拟插入证据片段（v3）

### 3.1 拟插入表（§7.6.1 表 7-1，修正后 2×2，p95 true cadence）

| 配置 | n / f | 故障数 | 强度 | 故障放置 | 可加性 | p95 比值 | 备注 |
|---|---|---|---|---|---|---:|---|
| Test 0 canonical | 7 / 2 | 2 (= f) | 2% loss | 跨验证者 | **additive** | 1.03 | |
| Test 1（qdisc 修复后） | 7 / 2 | 2 (= f) | 2% loss | 同验证者 | **additive** | 1.00 | |
| n=4 ablation | 4 / 1 | 2 (> f) | 2% loss | 跨验证者 | **additive** | **0.97** | 原 1.16 为单种子假阳性，独立种子未复现 |
| Test 2 | 7 / 2 | 2 (= f) | 5% loss | 跨验证者 | **super-additive** | **1.08** | 原 1.35，含一个 max=13s 离群 rep |
| n=4 + 5% loss | 4 / 1 | 2 (> f) | 5% loss | 跨验证者 | **super-additive** | **1.12** | 原 1.17，量级一致 |

读法（v3）：
- 行 1 vs 行 2：同 n、同强度，仅故障放置不同（跨验证者 vs 同验证者）→ 可加性对放置不敏感；
- 行 1 vs 行 3：同强度跨规模（n=7→n=4，跨越 BFT 边界）→ **可加性不变**（均 additive）→ **BFT 边界轴无独立破坏效应**；
- 行 1 vs 行 4 / 行 3 vs 行 5：同 n 提高强度（2%→5%）→ 双双进入 super-additive → **强度轴是唯一驱动轴**。

### 3.2 拟插入文本（v3，中文，~300 字）

> **§7.6.1 跨规模与跨强度部署实证（Cross-scale, cross-intensity deployment evidence）**
>
> §7.6 的条件化结论可被一项受控部署实证**定向**支持。本团队在**真实 Sui 7-validator (n=7, f=2) 与 4-validator (n=4, f=1)** 部署上，沿两条独立压力轴展开:**故障数相对 BFT 容差 f**（within f vs at/above f）与**单故障强度**（2% vs 5% 丢包）。每个 cell 取 10–20 次受控重复（关键 cell 另以独立种子复测，共 290+ 次重复），故障注入采用最小成对设计:跨验证者（独立）或同验证者（叠加），测量共识 cadence 的 p95 真值。
>
> 实证给出两项判断。**其一**，在中强度（2% 丢包）下，跨验证者故障呈干净的可加性，且这一点**与委员会规模无关**——n=7（within f，ratio 1.00–1.03）与 n=4（at/above f，ratio 0.97）一致：跨越 BFT 容差边界 f 本身**不**破坏可加性。**其二**，把单故障强度提高到 5% 丢包，则在 n=7（ratio 1.08）与 n=4（ratio 1.12）上**双双**把 p95 推入超可加。换言之，§7.3 所述「或有负债在故障下集中爆发」在部署中表现为一笔**由故障强度驱动、且非线性（超可加）**的尾部代价，其触发门槛是把验证者挤出 fast-quorum 参与的**单故障强度**，而非形式化的 BFT 安全边界 f。
>
> 须明确这一实证的**范围**:它在**单一 uncertified 协议**（Sui，Mysticeti 家族）上展开，**没有 certified 对照臂**;因此它探查的是 uncertified 一侧**或有负债的形状**，**既非** §7.2 成本模型（Δ_save、ρ\*）的定量标定，**亦非** certified/uncertified 的净优势比较。它为 §7.6 表格的「翻转」语言提供了具体的部署锚点（或有负债确为真实、非线性、强度驱动），但完整的跨协议受控标定仍属未来工作（见 §9、§10）。一项工具学与复现性限定见 §9「实证仪器局限」。完整 2×2 与逐 rep 数据见 `multivalidator/reports/stress_test_combined_conclusion_v3_20260526.md`;稳定性映射见图 7-3。

### 3.3 拟插入图（图 7-3，v3 占位）

```
              中强度 (2% 丢包)               高强度 (5% 丢包)
within f      additive                       super-additive
(n=7, f=2)    Test 0: 1.03 / Test 1: 1.00    Test 2: 1.08
at/above f    additive                       super-additive
(n=4, f=1)    n=4 ablation: 0.97             n=4 + 5%: 1.12
              └ BFT 边界轴：无独立效应 ┘      └ 强度轴：唯一驱动 ┘
```

（图 7-3 为修正后完整 2×2 稳定性网格;批准并二次确认后由 matplotlib 生成至
`final/figures/figure_7_3_stability_grid.png`。）

### 3.4 摘要末段（v3 拟追加句）

> 中（接第 7 行末）:「……该条件化结论的**或有负债侧**已由真实 Sui n=7/n=4 部署的受控故障注入实测（290+ 重复，含独立种子复现）初步支持:故障诱发的延迟代价确为一笔非线性、由故障强度驱动的或有负债（详见 §7.6.1）。」
>
> 英（接第 15 行末）:"This conditional conclusion is preliminarily supported, on its contingent-liability side, by controlled fault-injection measurements on a real Sui n=7/n=4 deployment (290+ repetitions, including independent-seed replication): the fault-induced latency cost is empirically a non-linear, fault-intensity-driven contingent liability (see §7.6.1)."

## 4. 与既有论文论点的关系（v3）

- **强化 §7.3 / §7.4**:为「或有负债在故障下集中爆发」「ρ 与 Δ_recover 在拥塞下耦合/复合」提供部署证据（超可加 = 非线性复合）。
- **强化 §7.6 表格**:为「翻转」给出具体量级与门槛（强度轴），并修正了「BFT 边界即翻转」的早期猜测（实为否定结论:边界轴无独立效应）。
- **不冲突**:不修改 §7 任何原论断，只追加实证 + 一处范围限定。
- **明确不写入 §8.4（RP-2 弃用本轮）**:v2 曾拟把「两轴非线性叠加」作为深层轴的可证伪预测写入 §8.4;该框架已被复测推翻，且修正后的「强度驱动」发现与 availability-enforcement 轴仅为类比、非直接证据，故本轮不写入 §8.4。

## 5. 与 v2 的 diff 摘要

- 表格:n=4 ablation 行 super-additive(1.16) → **additive(0.97)**;Test 2 1.35 → 1.08;n=4+5% 1.17 → 1.12。
- 论点数:v2 2 个（条件化实证支持 + 两轴非线性叠加）→ v3 **1 个**（条件化实证支持，强度轴单驱动）。**两轴叠加论点删除。**
- 新增:构念效度范围限定句（单协议、无 certified 臂、非 §7.2 标定）。
- RP-2 状态:v2 推荐写入 §8.4 → **v3 弃用本轮**。
