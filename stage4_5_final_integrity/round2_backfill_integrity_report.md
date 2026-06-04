# Stage 4.5 FINAL INTEGRITY — Round 2(回填实证内容终核)

| 项目 | 值 |
|------|-----|
| 触发 | 路 1:三轮部署实证回填(§7.6.1/7.6.2/7.6.3 + 图 7-3/7-4/7-5)绕过了下游门禁,须从零重核 |
| 核查日期 | 2026-05-31 |
| 核查对象 | `final/final_paper.md`(回填后,106,703 字符,579 行) |
| 模式 | Mode 2 final-check,5 阶段(A–E)+ 7-mode AI 研究失败检查表(阻断式) |
| **裁决** | **✅ PASS**(0 处 SERIOUS/MEDIUM;2 处 LOW 转 Stage 5;7 模式全 CLEAR) |

---

## 0. 预备:文件完整性(纠正一次自身假阳性)

核查初期一度误报"定稿被回填骨架覆盖、全文丢失"。该警报**作废**——经实证证伪:
- `final/final_paper.md` = 106,703 字符 / 579 行,**大于** draft_v3(88,381),增量恰为新三节;
- 第 1–10 章 + 双语摘要 + 参考文献 `[1]`–`[62]`(连续,结尾干净)全在位;
- 字面 `\n\n` 转义损坏 = 0;"stub markers" 为中文常用字正则假阳性;
- 9 张图全在(figure_1/2/3 + figure_7_3/7_4/7_5)。

**教训记入 Mode 2**:结构性故障须先证据化再断言——这正是本门要防的失败模式。

---

## 1. Phase A — 实证数据溯源(每个数字 → 源工件)

方法:不信任报告自带的汇总数字,直接从 **per-rep 原始 CSV 行**用独立 PowerShell 脚本重算 OLS、Pearson r、R²、均值。所有 CSV 位于 `stage7_deployment/multivalidator/data/runs/`。

### §7.6.1 表 7-1(源:`stress_test_combined_conclusion_v3_20260526.md`)
| 配置 | 论文比值 | v3 报告 | 对账 |
|---|---:|---:|:--:|
| Test 0 canonical(n=7,2%,跨验证者) | 1.03 | 1.03 | ✅ |
| Test 1(qdisc 修复,同验证者) | 1.00 | 1.00 | ✅ |
| n=4 ablation(2%,>f) | 0.97 | 0.97(replica,推翻原 1.16) | ✅ |
| Test 2(5%) | 1.08 | 1.08(replica) | ✅ |
| n=4 + 5% | 1.12 | 1.12(replica) | ✅ |
- "290+ 次重复" = v3 报告记 290(190 v2 + 100 replication seed),轻量 smoke runs 可作余量。✅

### §7.6.2(源:`phaseA_criticalpath_summary.csv` n=7 / `phaseA_criticalpath_n4_summary.csv` n=4)
独立 OLS 重算 vs 论文声明:

| 量 | 论文 | 重算 | 对账 |
|---|---:|---:|:--:|
| n=7 t_resume 均值(ms 0/250/500/1000) | 29.1/35.1/38.1/44.2 | 29.10/35.13/38.13/44.17 | ✅ |
| n=7 OLS slope(/1000ms) | 14.5 s | 14.46 s | ✅ |
| n=7 OLS intercept | 30.3 | 30.31 | ✅ |
| n=7 Pearson r | +0.85 | +0.854 | ✅ |
| n=4 t_resume 均值(ms 0/250/500/1000) | 22.1/30.1/32.1/42.2 | 22.10/30.10/32.10/42.17 | ✅ |
| n=4 OLS slope(/1000ms) | 19.0 s | 19.04 s | ✅ |
| n=4 OLS intercept | 23.3 | 23.29 | ✅ |
| n=4 Pearson r | +0.94 | +0.935 | ✅ |
| n=4 R² | 0.875 | 0.875 | ✅ |

### §7.6.3(源:`phase1b_dsave_calibration_summary.csv`、`phase2_recovery_asymmetry_summary.csv`、`phase2c_excess_sweep_summary.csv`、`phase2b_net_advantage_summary.csv`)
| 量 | 论文 | 重算 | 对账 |
|---|---:|---:|:--:|
| Δ_save(prober 75ms) | 4.58→2.99 ckpt/s, 0.116 s/commit | OFF 4.583/ON 2.989, Δ=116.4ms | ✅ |
| 恢复不对称 OFF t_resume/fetch | 48.2 / 196 | 48.20 / 196.5→196 | ✅ |
| 恢复不对称 ON t_resume/fetch | 37.7 / 123 | 37.65 / 123.5→123 | ✅ |
| ρ\* band | 0.013–0.038(1/26–78 commit) | 0.0129–0.0382(1/26–78) | ✅ |
| excess(Δr) OLS slope | +0.00121 | +0.00121 | ✅ |
| excess OLS R² | ≈0.49 | 0.494 | ✅ |
| amortized net_adv OLS R² | ≈0.02(non-monotonic) | 0.022(+/−/−/+) | ✅ |

**Δ_save 数字来源确认**:论文使用 phase1b 的 2-rep 结果(4.58/2.99/0.116),未混用 phase1 pilot 的 1-rep 值(4.63/3.14/102ms)。✅

**Phase A 裁决:PASS。** 所有数字可逐行溯源至 per-rep 原始 CSV,独立重算全吻合——数据捏造(Mode 3)被最强证据排除。

---

## 2. Phase B — 引用语境核查

回填三节(§7.6.1/7.6.2/7.6.3)**零新增 `[NN]` 外部文献引用**——仅引用内部小节号(§7.2/7.3/7.4/7.5/§9/§10)与文件路径。§7.3/7.4 沿用既有 [38]/[45]/[49],语境未变。参考文献表保持 `[1]`–`[62]`,0 新增孤儿。→ **PASS**。

---

## 3. Phase C — 数据/统计核查

见 Phase A 独立重算。OLS/Pearson r/R²/ρ\* 全部独立复算一致;统计措辞("近似线性""超可加由强度轴驱动""amortized 非单调""excess 随 Δr 增长")与数据方向一致。**ρ\* band(0.013–0.038)在 §7.2(l.311)、§7.6.3(l.390)、§9(l.478)、§10(l.492)四处表述一致**,无内部冲突。→ **PASS**。

---

## 4. Phase D — 原创性核查

回填文字为团队自有实验的技术描述,具体、可溯源,非样板/拼接;无抄袭风险。AI 使用已在声明覆盖。→ **PASS**。

---

## 5. Phase E — 论断核查(构念效度限定)

每条实证主张均(a)有工件支撑、(b)在正文显式标注限定:
- §7.6.1(l.366):"在单一 uncertified 协议上展开,没有 certified 对照臂" ✅
- §7.6.2(l.378):"Δ_recover 为注入式仿真旋钮,非对 certified 协议真实恢复开销的测量;单一 uncertified 协议、无 certified 对照臂" ✅
- §7.6.3(l.392):"可用性证书(2f+1 接受)非密码学签名聚合;单引擎;Δ_recover 注入式;ρ\* 为 band 可信量级非精确值" ✅
- §9(l.464–478):新增"实证仪器局限""独立种子复现性""注入式旋钮构念效度"三节,与上述限定同源一致 ✅
- §7.2(l.311):"§7.6.2 为独立性简化提供旁证;§7.6.3 首次定量定位 ρ\* 并诚实标出偏离" ✅
- §10(l.490–492):结论改述,未来工作含"真 RBC 签名开销、跨两套独立引擎的受控 benchmark" ✅

→ **PASS**。诚实边界是本轮最强项:论文主动收窄而非夸大。

---

## 6. 7-mode AI 研究失败检查表(MANDATORY / BLOCKING)

| # | 模式 | 裁定 | 证据 |
|---|------|------|------|
| 1 | 引用幻觉 | **CLEAR** | 回填无新引用;原 62 篇 Stage 2.5 已全 Web 核验 |
| 2 | 实现 bug 充作结果 | **CLEAR** | 已知 harness bug(tc qdisc 覆盖、rpc-probe 干涉)均在 §9(l.464–466)透明披露并重跑受影响 cell;旋钮 fire 经 STAGE9_RECOVERY 仪器 + 分区测试独立证实(见 memory-logs) |
| 3 | 幻觉结果/数据捏造 | **CLEAR** | per-rep 原始 CSV 独立 OLS 重算逐位吻合(本报告 Phase A) |
| 4 | 捷径依赖 | **CLEAR** | 主动选 Route A1 忠实 ack 通道(非纯 emulation);残留 emulation(Δ_recover)如实标注——无 shortcut 冒充 |
| 5 | bug 当洞见 | **CLEAR** | "恢复须在关键路径"由机制(PUSH/PULL 路由)+ 干净剂量响应(r=0.85/0.94)+ n=4 跨规模复现三重支撑,非对非 fire 旋钮的事后合理化 |
| 6 | 方法论造假 | **CLEAR** | 轮转(churn)故障法有脚本(`phaseA_criticalpath_partition*.ps1`)、可复现、文档完整(PHASEA_RESULTS.md + PHASE0_SPIKE.md) |
| 7 | pipeline frame-lock | **CLEAR** | 工作反复自我推翻(n=4 ablation 假阳性纠正、amortized 镜头错→分解法、静态分区错→轮转)——强证无锁框;PHASEA_SMOKE_FINDINGS.md 记录了三故障三结局的迭代发现过程 |

**7 模式全 CLEAR,不触发阻断。** Modes 1/3/5/6 均有充分证据(非 INSUFFICIENT EVIDENCE)。

---

## 7. 裁决与转交

| 阶段 | 裁决 |
|------|------|
| Phase A(数据溯源) | PASS |
| Phase B(引用语境) | PASS |
| Phase C(数据/统计) | PASS |
| Phase D(原创性) | PASS |
| Phase E(论断·限定) | PASS |
| 7-mode checklist | 全 CLEAR |
| **总裁决** | **✅ PASS** |

### 转 Stage 5 的 LOW 项(非阻断)

- **LOW-1(路径微歧)**:§7.6.2 正文(l.378)和 §7.6.3(l.392)写逐 rep CSV 在 `stage9_cross_protocol_calibration/`,但 CSV 实存于 `stage7_deployment/multivalidator/data/runs/`(stage9 的 PHASEA_RESULTS.md "Artifacts" 节亦指向 stage7)。数据可用性声明(l.498)§7.6.1 路径正确、§7.6.2/7.6.3 路径同样微歧。**建议 Stage 5 统一路径为 `stage7_.../data/runs/`。**
- **LOW-2(页脚过期)**:第 579 行页脚仍为旧流水线描述("Stage 1 socratic→…→Stage 4.5 终核(PASS)定稿"),**未含三轮回填**。Stage 5 重定稿时更新。

**下一步:** Stage 3' RE-REVIEW(对含 §7.6 实证的扩展稿再评审)→ Stage 5 FINALIZE 重定稿(含 LOW-1/2 + 重出 DOCX/PDF)。
