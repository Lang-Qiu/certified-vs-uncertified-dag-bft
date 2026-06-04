# P0-1 断开网格（Partition Grid）结果 — §5.4 或然负债边界

**日期:** 2026-06-02 · **运行:** 18 runs（3 断开时长 × 3 Δ_recover × 2 reps），全部 `status=ok`
**数据:** `stage7_deployment/multivalidator/data/runs/partition_grid_summary.csv`
**分析:** `stage9_cross_protocol_calibration/scripts/analyze_partition_grid.py`
**Harness:** `partition_grid_scan.ps1`（基于 `phaseA_criticalpath_partition.ps1` 的关键路径轮转故障）

---

## 0. 数据完整性事件（必读，供 Stage 4.5 复现审计）

**第一轮 18 runs 的 `v1/v2_fetches` 列全为 0，是测量伪迹，不是发现。** 根因：`Get-FetchCount` 中
`& timeout 10 docker logs` 在 PowerShell 下解析为 Windows `timeout.exe`（非 GNU coreutils），
在非交互 shell 中立即报错 `Invalid syntax. Default option is not allowed more than '1' time(s)`，
`docker logs` 从未执行 → `STAGE9_RECOVERY` 零匹配 → fetch 计数恒为 0。

- **侦破线索:** 同一轮 `t_resume` 已随 Δ_recover 单调上升——而 Δ_recover 是**只注入恢复/PULL 路径**
  的延迟。若 PULL 从不触发，`t_resume` 不可能随之缩放。`fetches=0` 与 `t_resume` 的 Δ_recover 响应
  自相矛盾。
- **铁证:** Phase A 的同款轮转 harness（gap=90s，唯一差异是 `docker logs` 不带 `timeout` 包装）
  记录到数百次 fetch（907/320 … 84/93）。
- **修复:** `Get-FetchCount` 改回裸 `docker logs`（Phase A 已验证正确的形式），并在脚本内注释固化该陷阱。
- **重跑:** 全 18 cell 重跑，fetch 计数现真实非零（min=104，max=1412），且与 Phase A 同量级、同方向。
- **存档:** 受污染数据保留为 `partition_grid_summary.ARTIFACT_fetches_broken.csv` / `partition_grid_run.ARTIFACT.log`。

> 这正是 Stage 4.5 数据完整性纪律要防的失败模式：把 `fetches=0` 当作"PULL 从不触发"上报，
> 会把 §5.4 的核心结论**反向**。

---

## 1. Sanity check（重跑后的干净数据）

| 检查项 | 结果 |
|--------|------|
| 18 runs 全 `ok` | ✅ |
| PULL 在每个断开时长都触发（recFetch>0） | ✅ min=104 / max=1412，对照 Chapter-5 丢包扫描 40 runs **全 0** |
| `t_resume` 随 Δ_recover 单调上升（每个 gap） | ✅ 30s: 22.6→36.1→46.7s；60s: 15.1→19.6→25.6s；90s: 24.1→36.1→49.7s |
| fetch 计数随 Δ_recover 单调下降 | ✅ 每个 gap r≈−0.87~−0.89（更慢的 RPC → 窗内发出更少） |
| 与 Phase A 交叉复现（gap=90） | ✅ ms=0: 本网格 1236 vs Phase A 1227~1722；ms=1000: 199 vs ~90~205；t_resume 同样 ~24s→~50s |
| 控制变量 eqChk/causDec 不被故障门控 | ✅ 仅随提交数（停顿越长提交越少）下降，路径本身从不关闭 |

**回归（OLS）:**
- `t_resume` vs Δ_recover：池化 **+20.0 s / +1000ms**，r=+0.705；分 gap R²=0.80~0.99（gap=90 最干净，R²=0.992）。
- `fetch` vs Δ_recover：池化 **−723 次 / +1000ms**，r=−0.711。

**诚实标注:** 断开**时长**轴（30/60/90s）对 `t_resume` 非单调（gap=60 反而最快）。这是仅 2 reps 下的
噪声 + 轮转重接时机主导，而非时长主导。稳健的定量信号是 **Δ_recover 剂量响应**（高 R²），断开时长仅作
次级佐证（更长断开 → 更多 missed ckpts，但 t_resume 由 Δ_recover 与 fetch RPC 节奏主导）。

---

## 2. 可放入论文 §5.4 的结果摘要（草稿，待批准回填）

> 为定量刻画可用性不变量作为**或然负债**（②"削弱+补偿"路径）的边界，我们在 n=7 部署上以关键路径
> 轮转故障扫描断开时长（30/60/90 s）与补偿延迟 Δ_recover（0/500/1000 ms）的二维网格（每格 2 次重复，
> 共 18 次运行）。轮转故障先切断 {v₁,v₂} 打开真实空洞，再在愈合二者的同时切断 {v₃,v₄}，使网络降至
> 子法定人数，从而把恢复路径**强制置于级联关键路径**上：唯有当 v₁,v₂ 完成 PULL 追赶并重新入组，
> cadence 方能恢复，其墙钟耗时 `t_resume` 即为恢复代价的直接观测量。
>
> 结果将或然负债的**实体化边界精确定位在"断连"而非"丢包"**。在 0–10% 独立丢包的全部 40 次运行中
> （第 5 章丢包扫描）PULL 恢复计数器 recFetch 恒为 0——PUSH 广播足以吸收独立丢包；而在本网格中，
> **即便 30 s 的网络分区也会立即触发 PULL**（recFetch 每次运行 104–1412 次，全 18 次运行无一为零）。
> 这把 §5.3 中"安全地带"的右边界钉死：代价为零的前提是数据可用性未被破坏，一旦发生分区
> （可用性丧失），②路径的或然负债即实体化。
>
> 实体化之后，该负债随补偿延迟 Δ_recover **剂量式缩放**。`t_resume` 对 Δ_recover 的池化回归斜率为
> +20.0 s / 1000 ms（分断开时长 R²=0.80–0.99，gap=90 s 时 R²=0.992），例如 gap=90 s 下
> `t_resume` 由 Δ_recover=0 的 24.1 s 升至 1000 ms 的 49.7 s。与此对偶，fetch **次数**随 Δ_recover
> 下降（−723 次 / 1000 ms）：更大的每次取数延迟意味着固定追赶窗内发出的 RPC 更少——代价以**延迟**
> （t_resume 上升）而非 RPC **数量**的形式兑现。该逆向关系独立复现了 Phase A 标定（gap=90 s 下
> fetch 由 ms=0 的约 1.2k 次降至 ms=1000 的约 0.2k 次）。
>
> 作为对照，两条①"固定开销"路径（非等价检查 eqChk、因果历史决策 causDec）的计数器在整个网格中
> 仅随提交数变化（停顿更久则提交更少），从不被故障门控关闭——印证 §5.2 的分类:非等价与因果历史
> 是**与故障无关的逐提交固定开销**，而可用性是**仅在数据可用性被破坏时实体化、且随补偿延迟缩放的
> 或然负债**。至此 §5.4 的定量图景完整:安全地带（0–10% 丢包，零代价）+ 断崖（≥30 s 分区触发 PULL）
> + 实体化后的剂量响应（Δ_recover 线性放大 t_resume）。

---

## 3. 论文落点映射

| 论文位置 | 本实验贡献 |
|---------|-----------|
| §5.3 安全地带右边界 | 钉死边界 = "数据可用性未破坏"；丢包(0)→分区(触发) 的对照 |
| §5.4 或然负债定量 | recFetch 断崖 + Δ_recover 剂量响应（t_resume 斜率 + fetch 逆向）|
| §5.2 ①②③ 分类 | eqChk/causDec 控制变量证实①固定开销；recFetch 证实②或然负债 |
| §5.6 台账 | 或然负债项可标价:每 1000ms Δ_recover ≈ +20s 恢复停顿 |
| §9 诚实边界 | 断开时长轴非单调（2 reps 噪声）；边界刻画依赖 Δ_recover 轴 |
