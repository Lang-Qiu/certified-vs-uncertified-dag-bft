# Stage 4.5 FINAL INTEGRITY — Round 4(P0+P1 全实验回填终核)

| 项目 | 值 |
|------|-----|
| 触发 | Round 4 把 P0+P1 全部实验(136 runs)回填 `final/final_paper.md`（10 编辑 + 7 新图,§4.5/§5.2–5.4/§7.3–7.5 + §7.6 表/§9/§10/数据可用性),绕过下游门禁,须从零重核 |
| 核查日期 | 2026-06-04 |
| 核查对象 | `final/final_paper.md`(回填后,**119,987 字符 / 623 行**) |
| 模式 | Mode 2 final-check,Phase 0 + A–E + 7-mode AI 研究失败检查表(阻断式) |
| 独立重算脚本 | `stage4_5_final_integrity/verify_round4.py`(不复用 `analyze_*.py`,自实现 mean/stdev/OLS/Pearson/R²,直读 per-rep CSV) |
| **裁决** | **✅ PASS**(0 SERIOUS / 0 MEDIUM;3 处 LOW 转 Stage 5;7 模式全 CLEAR) |

---

## 0. Phase 0 — 文件完整性

- 字符 119,987 / 行 623,**大于** Round 3 后的 106,703 / 579,增量恰为 7 个实测锚点段 + 图注 + 图引用。✅
- 第 1–10 章(`## 第 N 章` ×10)+ 双语摘要 + 致谢声明 + 参考文献全在位。✅
- **转义换行损坏 = 0**:`grep -E '\n\n'` 报 11 行系**正则假阳性**(GNU grep 正则 `\n` 匹配字面 'n' → 命中参考文献作者名 Ka**nn**an / So**nn**ino 等);权威的 `grep -F '\n\n'` = 0、`grep -F '\n'` = 0,确证无字面转义损坏。(与 Round 2 同项的假阳性结论独立吻合。)✅
- 13 张图全在且引用全解析(13/13 `figures/figure_*.png` 落盘,0 BROKEN,0 孤儿,标签↔引用一一配对;见回填完整性校验)。✅

---

## 1. Phase A — 实证数据溯源(每个数字 → per-rep CSV,独立重算)

方法:`verify_round4.py` 独立实现统计量,直读 `stage7_deployment/multivalidator/data/runs/` 的 7 个 per-rep 汇总 CSV,**40/40 项全部对账一致**。

| 章节 | 量 | 论文 | 独立重算 | 对账 |
|---|---|---:|---:|:--:|
| §4.5 | eqChk/commit vs payload R² | 0.01 | 0.0114 | ✅ |
| §4.5 | causDec/commit vs payload R² | 0.04 | 0.0413 | ✅ |
| §4.5 | t_resume vs payload R² | 0.25 | 0.2479 | ✅ |
| §5.2–5.4 | chapter5 ok 行数 | 40 | 40 | ✅ |
| §5.2–5.4 | recovery_fetches_total 全 0 | 全 0 | max=0 | ✅ |
| §5.2–5.4 | cadence 区间 | 4.0–4.7 | 4.0 / 4.7 | ✅ |
| §5.4 | partition recFetch min / max | 104 / 1412 | 104 / 1412 | ✅ |
| §5.4 | t_resume vs Δr 斜率(s/1000ms) | +20.0 | +20.05 | ✅ |
| §5.4 | t_resume vs Δr 合并 r | +0.71 | +0.7047 | ✅ |
| §5.4 | gap=90 R² / gap=30 R² | 0.99 / 0.92 | 0.9919 / 0.9222 | ✅ |
| §7.3 | cadence vs ρ 斜率 / 截距 | −265 / 3.78 | −265.3 / 3.782 | ✅ |
| §7.3 | cadence vs ρ  r / R² | −0.95 / 0.90 | −0.950 / 0.9024 | ✅ |
| §7.3 | ρ 四档均值 | .0077/.0057/.0037/.0022 | .00769/.00567/.00370/.00223 | ✅ |
| §7.3 | per-fault recFetch / t_resume(spacing) | 143 / 37.9s | 142.8 / 37.91s | ✅ |
| §7.3 | N0 cadence / any-fault cadence(scan) | 4.32 / ~1.6 | 4.322 / 1.605 | ✅ |
| §7.3 | per-fault recFetch / t_resume(scan) | 164 / 40.8s | 163.7 / 40.76s | ✅ |
| §7.4 | cadence vs period R² | 0.09 | 0.0912 | ✅ |
| §7.4 | cadence 区间 | 4.14–4.38 | 4.141 / 4.384 | ✅ |
| §7.5 | cert OFF / ON cadence | 1.06 / 1.96 | 1.056 / 1.964 | ✅ |
| §7.5 | cadence Δ% | +86 | +85.9 | ✅ |
| §7.5 | cert OFF / ON t_resume | 44.4 / 26.1s | 44.40 / 26.07s | ✅ |
| §7.5 | t_resume Δ% | −41 | −41.3 | ✅ |
| §7.5 | cert OFF / ON recFetch | 188 / 97 | 187.7 / 97 | ✅ |
| §7.5 | recFetch Δ% | −48 | −48.3 | ✅ |
| §7.5 | cert OFF cadence stdev | 0.84 | 0.838 | ✅ |

**Phase A 裁决:PASS。** 40/40 项独立重算逐位吻合,数据捏造(Mode 3)被最强证据排除。

---

## 2. Phase B — 引用语境核查

- 全文最高 `[NN]` = **62**,参考文献表 `[1]`–`[62]` 连续、结尾干净(`[62]` Red Belly)、计数 62,**0 新增**。
- Round 4 的 6 个新锚点段(含 `本团队` 的句子)**零 `[NN]` 外部引用**,仅引内部小节号(§7.2/7.4/7.6.x/§9)与 CSV 文件名。→ **PASS**。

---

## 3. Phase C — 数据/统计一致性

- 统计措辞与数据方向一致("逻辑型平直 R²≤0.04""分区 recFetch 处处>0""cadence 随 ρ 线性退化""sub-critical 抖动近基线 R²=0.09""非对称下 cert ON 更优")。
- **跨区制一致性(非矛盾)**:§7.6.3 良好情形 cert ON 更慢(Δ_save,4.58→2.99)与 §7.5 非对称+故障下 cert ON 更快(1.96 vs 1.06)是**论文核心论点的实证交叉**——认证良好情形付费、逆境回报,二者区制不同(满带宽无故障 vs 1Mbps+故障),非内部冲突。两段文本均正确标注区制。
- ρ\* band(0.013–0.038)未被 Round 4 改动,§7.2/7.6.3/§9/§10 四处仍一致;§7.3 新锚点正确指向 §7.6.3 为净优势翻转点来源。
- 图号唯一(13 标签 `uniq -d` 空)、章节编号连续。→ **PASS**。

---

## 4. Phase D — 原创性

回填文字为团队自有实验的技术描述(具体参数、可溯源数字、方法细节),非样板/拼接;AI 使用已在 §10 声明覆盖。→ **PASS(ORIGINAL)**。

---

## 5. Phase E — 论断核查(构念效度限定)

每条新实证主张均(a)有 CSV 工件支撑(Phase A)、(b)正文显式标注限定:
- 7/7 新图注全部携带 `注:` 限定句(单引擎 / 可用性证书非签名 / 注入旋钮 / 块大小限制 / 诚实阴性 / 离群点)。
- 正文限定关键词密集:`单一 uncertified 协议` ×13、`注入式` ×14、`非密码学` ×6、`诚实阴性` ×3。
- §4.5 物理型一半诚实标限(RPC 主导、字节量在 ≤10KB 未分离、>10KB 触发块上限 6 runs 失败);§7.4 诚实阴性(sub-critical 信号弱)+ 强度门槛精化;§7.5 cert-OFF 离群点(±0.84,可信方向与量级非精确百分比)。
- §9 新增"三翻转轴部署锚点共享限定"段,与各锚点同源一致。
→ **PASS**。诚实边界是本轮最强项:论文主动收窄而非夸大。

---

## 6. 7-mode AI 研究失败检查表(MANDATORY / BLOCKING)

| # | 模式 | 裁定 | 证据 |
|---|------|------|------|
| 1 | 引用幻觉 | **CLEAR** | 回填 0 新引用;Phase B |
| 2 | 实现 bug 充作结果 | **CLEAR** | **P0-1 `timeout.exe` 致 recFetch=0 伪迹在实验中被交叉检验抓出(t_resume 随 Δr 升而 fetch=0 自相矛盾)→ 修复重跑、污染数据存档**;恢复仪器(STAGE9_RECOVERY 计数)经"丢包 recFetch=0 vs 分区 recFetch>0"对照独立证实;两事件已写入论文数据可用性声明 |
| 3 | 幻觉结果/数据捏造 | **CLEAR** | `verify_round4.py` per-rep 独立重算 40/40 逐位吻合(Phase A) |
| 4 | 捷径依赖 | **CLEAR** | §7.5 复用 Route A1 忠实可用性证书 gate（非纯 emulation);Δ_recover 注入如实标注 |
| 5 | bug 当洞见 | **CLEAR** | §7.4 阴性如实报为阴性(R²=0.09),"强度门槛"解释由 §7.6.1/7.6.2 独立的关键路径发现支撑,非事后合理化;§4.5 物理限制如实报为范围限定 |
| 6 | 方法论造假 | **CLEAR** | 5 实验全有脚本(`partition_grid_scan.ps1`/`rho_spacing_sweep.ps1`/`payload_size_scan.ps1`/`net_asymmetry_scan.ps1`/`gst_jitter_scan.ps1`),可复现,EXPERIMENTAL_COVERAGE.md 文档完整 |
| 7 | pipeline frame-lock | **CLEAR** | **两次自我推翻**:P0-1 timeout 伪迹纠正、P0-2 ρ~恒定设计缺陷→间距扫描修正,均诚实写入论文数据可用性声明——强证无锁框 |

**7 模式全 CLEAR,不触发阻断。** Modes 1/3/5/6 均有充分证据(非 INSUFFICIENT EVIDENCE)。

---

## 7. 裁决与转交

| Phase | 裁决 |
|------|------|
| 0 文件完整性 | PASS |
| A 数据溯源(40/40 独立重算) | PASS |
| B 引用语境 | PASS |
| C 数据/统计一致 | PASS |
| D 原创性 | PASS(ORIGINAL) |
| E 论断·限定 | PASS |
| 7-mode checklist | 全 CLEAR |
| **总裁决** | **✅ PASS** |

### 转 Stage 5 的 LOW 项（非阻断)

- **LOW-1(路径微歧,承自 Round 2 LOW-1)**:§4.5/§5/§7.3/7.4/7.5 内联锚点写"详见 `stage9_cross_protocol_calibration/`(`xxx.csv`)",但汇总 CSV 实存于 `stage7_deployment/multivalidator/data/runs/`(脚本/图在 stage9)。数据可用性声明(R4-9)已正确并列两地。与 Round 1–3 的 §7.6.2/7.6.3 锚点同型——建议 Stage 5 一次性统一全部内联路径,避免只改 Round 4 造成不一致。
- **LOW-2(页脚过期,承自 Round 2 LOW-2)**:第 623 行页脚仍写"3 图"(实际 13),且未含 Round 1–4 回填。Stage 5 重定稿更新。
- **LOW-3(图号阅读序,装饰性)**:图 7-6/7-7/7-8(§7.3–7.5)在阅读流中先于 图 7-3/7-4/7-5(§7.6.x),因图号按"顺序续接"约定分配。与既有 图 3(§8 却编号 3,出现在 图 7-5 之后)同源,可接受。若需严格阅读序,可在一次专门的全图重编号 pass 中解决(非本轮,避免大改已定稿内容)。

**结论**:Round 4 回填通过 Stage 4.5 强制完整性终核。论文 = 理论 + 8/8 可实验章节 100% 部署锚定,所有实证主张数字可独立溯源、构念效度限定齐备、两起数据完整性事件透明披露。

**下一步**:Stage 3' RE-REVIEW(对含 §4.5/§5/§7.3–7.5 扩展锚点的稿再评审)→ Stage 5 FINALIZE 重定稿(批量处理 LOW-1/2/3 + 重出 DOCX/PDF)。
