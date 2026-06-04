# P0-2 ρ 轴扫描 — 第一轮结果与设计诊断

**日期:** 2026-06-03 · **运行:** 15 runs（N∈{0,1,2,4,8}×3 reps），全部 `status=ok`
**数据:** `stage7_deployment/multivalidator/data/runs/rho_scan_summary.csv`
**分析:** `stage9_cross_protocol_calibration/scripts/analyze_rho_scan.py`

---

## 0. 设计诊断：ρ 未真正扫描

**根因：** 本轮采用"顺序注入 N 次故障，固定 settleSeconds=6s"设计。因每次故障也附带 ~110 次提交的恢复期，
`commits` 随 N 同步增长 → `ρ = N/commits` 仅有两个聚类值：

| N | ρ (mean of 3 reps) |
|---|---------------------|
| 0 | 0.00000 |
| 1 | 0.00868 |
| 2 | 0.00904 |
| 4 | 0.00898 |
| 8 | 0.00925 |

N≥1 的所有运行 ρ≈**0.009**（每 commit ~0.009 次故障，即每 111 次提交 1 次故障）。这是一个密度**上限**
（在单次故障恢复期内发出的最大提交数 ≈ 每个故障最多触发的进度），不是密度梯度。

因此 `cadence_eff vs ρ` 的 OLS（R²=0.984）实质上是**两点间的弦**（ρ=0 ⇄ ρ=0.009），而非扫过的剂量响应曲线。

**这与 P0-1 第一轮 fetch=0 是同一类错误：** 在 R² 漂亮时比在 R² 差时更需要溯源。

---

## 1. 本轮实际产出（仍可复用）

### 1.1 故障恢复的固定边际成本（支撑 §7.2 成本模型）

| 指标 | 斜率 vs N | 解释 |
|------|----------|------|
| recFetch | +147 次/fault | 每追加一个故障，恢复 RPC 增加 ~147 次 |
| Σt_resume | +37 s/fault | 每追加一个故障，恢复暂停 增加 ~37 s |

这是**固定线性量子**——恰好是 §7.2 成本模型 `cost = base + ρ·recovery` 中假设的结构。

### 1.2 故障-自由基线 cadence

λ₀ = **4.32 ckpt/s**（±0.16，3 reps）。这是 n=7, cert=OFF 下无故障的持续吞吐。

### 1.3 有故障下 cadence 的骤降

一旦注入故障（N≥1），cadence 从 4.32 骤降至 ~1.6 ckpt/s（−62%），且在 N=1..8 范围内**平坦**。
这不是"更多故障时 cadence 退化得更厉害"——而是"**任何故障**打出一个巨大的减速洞（约 37s 停顿），
在故障恢复期内整个委员会被拖慢"。N 增加只是拉长减速洞（每加一次故障加 ~37s），而不进一步降低速率。

这与第 5 章的断连断崖一致：**只要发生一次断连/分区，PULL 恢复就将 cadence 踩在它的时间表上**。

### 1.4 eqChk/causDec 的控制

per-commit 比率在 N=0 时约为 31/22，N≥1 后变化（因故障期提交流量模式改变），但路径本身从不被门控关闭——
与 P0-1 的发现一致。

---

## 2. 闭合 §7.3 所需的设计修正：Spacing Sweep

要真的扫 ρ（而非固定在饱和密度），需要**固定 N，扫 settled 长度**（fault-free progress between faults）：

```
Fix N=2（两次轮转故障），Δ_recover=1000ms，cert=OFF
扫 settleSeconds ∈ {20, 40, 80, 160} → 4 个密度级别 → real ρ range
× 3 reps = 12 runs
```

为什么这能扫 ρ：
- longer settleSeconds → more fault-free commits between the two faults → lower ρ
- N=2 fixed → the per-fault cost is measured, not confounded
- cadence_eff over the whole window captures: (fault-free progress) / (fault-free time + recovery stall time)
- → as settleSeconds ➚, recovery stalls are a smaller fraction → cadence_eff ➚ → the real degradation curve

预计 ρ range：约 0.0025（160s settle）到 0.012（20s settle）——涵盖 §7.6.3 推导的 ρ* band。
