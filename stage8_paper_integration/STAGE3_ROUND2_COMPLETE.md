# 阶段三 Round 2 完成记录 —— Phase A 关键路径 Δ_recover 标定回填

**完成时间**: 2026-05-31
**数据源**: `stage9_cross_protocol_calibration/PHASEA_RESULTS.md`（n=7 + n=4 关键路径轮转标定）
**门禁**: 计划逐点最小 diff 提案（`revision_diffs_round2.md`）→ 用户「全部批准，执行」→ 编辑 `final/final_paper.md`。

## 已落地的 7 处编辑（`final/final_paper.md`）

| EDIT | 章节 | 操作 | 状态 |
|---|---|---|---|
| R2-1 | §7.6.2（新增，图 7-3 之后） | 恢复侧 Δ_recover 受控旋钮标定子节（方法=旋钮+轮转故障；三判断=剂量响应/可操作边界/委员会结构依赖）+ 图 7-4 | ✅ |
| R2-2 | §7.4 末 | 追加一句：区分 ρ↔Δ_recover 协变 vs Δ_recover 轴线性；xref §7.6.2 | ✅ |
| R2-3 | §7.2（独立性假设处） | 追加半句：部署旁证支持 ρ⊥Δ_recover 可分离 | ✅ |
| R2-4 | §9 | 新增「注入式旋钮的构念效度」一段（emulation 非真实开销；关键路径要求本身是发现） | ✅ |
| R2-5 | §10 未来工作方向二 | 改述：恢复侧探查含 §7.6.2 剂量响应；仍待 certified 臂 | ✅ |
| R2-6 | 数据可用性声明 | 追加一句：Phase A 工件存档于 `stage9_cross_protocol_calibration/` | ✅ |
| R2-7 | figures | `phaseA_recover_calibration.png` → `final/figures/figure_7_4_recover_calibration.png` | ✅ |

## 核心实证主张（Round 2 新增，附构念效度限定）

- **剂量响应（近似线性）**：关键路径上 t_resume 随 Δ_recover 单调近线性上升——n=7 斜率≈14.5 s、r=+0.85；n=4≈19.0 s、r=+0.94。无超线性 → 固定故障强度下或有负债沿 Δ_recover 轴线性。
- **两轴可分离**：旋钮增大时恢复事件计数反降而总 cadence 代价仍升 → 代价由「每事件时延」而非「事件次数」承载。支持 §7.2 的 ρ⊥Δ_recover 简化。
- **可操作边界**：或有负债仅在恢复落入共识关键路径时 materialize（单节点恢复被推送式补块绕过，r=+0.43 非单调）→ 精化 §7.3「故障情形」为可操作判据。
- **委员会结构依赖**：n=4 基线更低但斜率更陡 → 或有负债随委员会收缩而加剧。
- **限定（强于 §7.6.1）**：Δ_recover 是注入式仿真旋钮（非真实 certified 协议开销）；单 uncertified 协议、无 certified 臂；标定的是或有负债沿 Δ_recover 轴的形状与触发边界，**非** §7.2 的 Δ_save/ρ\* 数值，**非** certified/uncertified 比较。

## 完整性校验（已过）

- 数字对账：§7.6.2 的 14.5 s / 19.0 s / r=+0.85 / r=+0.94 / r=+0.43 与 `phaseA_criticalpath*_summary.csv` 派生统计一致。
- 交叉引用闭合：§7.2→§7.6.2、§7.4→§7.6.2、§9→§7.6.2、§10→§7.6.2、数据可用性→§7.6.2；§7.6.2 内部 →§7.6.1/§7.2/§7.3。
- 图 7-4 资产就位（140 KB），引用路径正确；§7.6.2 唯一（无重复）；图号 表 7-1→图 7-3→图 7-4 连续。
- 受保护文件 `consensus_metrics.json` 未被今日修改（hash chain 未动）。

## 排除项（与 Round 1 一致）

- 摘要不再追加；§1.3/§1.5 不再改；§8.4/RP-2 仍不写入；标题、章节编号、贡献结构不变。

## 续作（仍待）

- 含 **certified 对照臂**的跨协议受控实证（§7.2 的 Δ_save/ρ\* 数值标定）——深 consensus 子项目（Mysticeti 无独立确认轮，须重建投票/ack 通道；详见 `stage9_.../PHASE0_SPIKE.md` §2）。
- 可选：更多 reps / 更密 Δ_recover 网格 / n=10（需新 compose）。
