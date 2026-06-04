# 阶段三呈递材料(待批准)

---

## ⚠️ v3 状态更新(2026-05-30) —— 请先读本块

下方 §内容总览 及 RP-1/RP-2 描述为 **v1/v2 历史快照**,已被以下决策与复测**部分覆盖**:

1. **重定位深度已选定 = Option A「实证支撑的理论论文」**:理论仍为主轴,实证作定向验证;不新增章节、不新增贡献 D、标题基本不动。
2. **RP-1 已升级为 v3**(`RP1_v3_scale_ablation_evidence.md`):独立种子复测(种子 20260526)**推翻**了 v2 的「n=4 跨 BFT 边界即 super-additive(1.16)」——该 cell 复测为 **additive(0.97)**,原为**单种子假阳性**。结论收窄为「**仅故障强度轴驱动超可加;BFT 边界轴无独立效应**」。v2 的「两轴非线性叠加」论点**作废**。
3. **RP-2(§8.4)本轮弃用**:其 v2 框架(把「两轴非线性叠加」作为深层轴可证伪预测)已被复测推翻;修正后的「强度驱动」发现与 availability-enforcement 轴仅为类比、非直接证据。§8.4 现有 conjecture 保持纯理论。
4. **RP-3 v2**(`RP3_v2_methodology_footnote.md`)已与 v3 对齐,直接复用(含 qdisc bug 披露 + 独立种子复现表 + n=4 假阳性自我修正)。
5. **数据可用性声明(§致谢,第 444 行)必改**:现状「本文为理论分析型研究,不涉及实验数据集」「图均非真实协议实测」在阶段二完成后已**为假**。

权威数据源:`reports/stress_test_combined_conclusion_v3_20260526.md`。
逐点最小 diff(供二次确认)见:`stage8_paper_integration/revision_diffs.md`。

---

> **状态**:草稿,**未获批准**。
>
> 严格遵守 `[[paper-integration-approval-gate]]` 用户规则:
> - 本目录不直接出现在 `stage8_paper_integration/`(后者未创建);
> - 不修改 `final/final_paper.md`;
> - 仅准备「候选修订点 + 证据片段 + 修订文本提案」,供用户批准后再实际改稿。
>
> 用户批准任一/全部候选点后,下一步才是创建 `stage8_paper_integration/<候选点编号>_revision.md`、对照原文做最小变动 diff、并提交终稿。

## 内容总览

本目录囊括 ≤3 个候选回填点。三者按相互独立性排序——每一项均可被单独批准或单独拒绝,互不绑定。

| 编号 | 候选回填点 | 触及章节 | 证据来源 | 建议形态 |
|---|---|---|---|---|
| RP-1 | 「条件化结论」从纯理论模型升级为「理论 + 部署实证」双轨 | §7.6 表格 / §7.7 判定程序 / 摘要末段 | `reports/stress_test_combined_conclusion_20260525.md` §1.4 + 本目录 `RP1_scale_ablation_evidence.md` | 在 §7.6 表格下方追加一小节「§7.6.1 跨规模部署实证」+ 一张表 + 一张图,并在摘要末尾把「定性条件化结论」改述为「条件化结论,并由 n=4/n=7 跨规模部署实证支持」 |
| RP-2 | 把「故障可加性边界」作为深层轴的可证伪预测之一引入 §8.4 | §8.4「深层轴的解释力」 | `reports/fault_decoupling_extreme_conclusion_20260525.md` §1.3 (Test 2 超可加) + 本目录 `RP2_additivity_boundary_claim.md` | 在 §8.4 末尾追加一段「可证伪预测:故障可加性的二维边界」,引用本目录 §2 的两轴稳定性图作为 framing |
| RP-3 | §9 局限节增列「实证仪器局限」一行,把 qdisc 编排 bug 与 rpc 探测器方差污染作为透明披露 | §9「局限、误用声明与威胁有效性」 | `reports/fault_decoupling_extreme_conclusion_20260525.md` §1.2 + 已知 rpc-probe 方差污染笔记 + 本目录 `RP3_methodology_footnote.md` | 新增一段「实证仪器局限」,~150 字,披露两项已识别的方法学限制及其对结论的影响范围 |

## 一项必要的「批准前自检」(给用户)

在批准任一候选点前,建议先核对以下三件事:

1. **n=4 ablation 样本量**:每场景 10 reps,种子单一(20260525)。Claim B (跨规模超可加) 若要进入正文,理想是至少 1 个独立种子复测——「Test 2 (5% 丢包,n=7) 也是单种子」同此问题。可批准「先用单种子结果先入正文,后续补独立种子」,也可决定「补完独立种子再回填」。
2. **qdisc bug 的影响范围**:bug 只影响「同一容器叠加多个 netem 故障」这一类场景。canonical 60 + decoupling 20 + n=4 ablation 40 全部为「一个容器一个故障」,**不受 bug 影响**。仅 Test 1 (`delay_loss_same_v1`) 在原编排下有效性受疑;修复后的 10 rep 数据(G2,本会话进行中)将单独报告。
3. **回填文本的语气与位置**:本目录所提供的修订文本目前为「最小侵入草案」——仅追加,不删除原文判断;若用户希望「重写而非追加」,需在批准时明示。

## 同级文件

- `RP1_scale_ablation_evidence.md` — 候选 RP-1 的完整证据片段 + 待插入的表格 + 文本提案
- `RP2_additivity_boundary_claim.md` — 候选 RP-2 的可证伪预测段提案
- `RP3_methodology_footnote.md` — 候选 RP-3 的局限节追加段
- `decision_form.md` — 简化的批准表(用户勾选 RP-1/2/3 中任意子集)

---

生成时间:2026-05-25
作者声明:全部草稿由 Claude Code (claude-opus-4-7) 在用户监督下生成,已避开 `final/` 与 `stage8_paper_integration/` 两个目录。
