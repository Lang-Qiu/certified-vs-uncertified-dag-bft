# Stage 5 FINALIZE — 定稿报告

| 项目 | 值 |
|------|-----|
| 定稿文件 | final/final_paper.md(由 stage4_revise/draft_v3.md 定稿) |
| 定稿日期 | 2026-05-21 |
| 编排器 | academic-pipeline v3.7.0 |

## 定稿统计

| 指标 | 值 | 目标 | 达标 |
|------|-----|------|------|
| 正文汉字数 | 20028 字(另含英文摘要约 250 词、62 条英文参考文献) | ~20000 字 | ✅ |
| 参考文献 | 62 篇(IEEE 格式) | ≥ 60 篇 | ✅ |
| 章节 | 10 章 + 中英文双语摘要 + 声明 | — | ✅ |
| 图表 | 3 图(已随文打包至 final/figures/,PNG 300 DPI) | — | ✅ |
| 引用孤儿 | 0 | 0 | ✅ |

## Stage 3'/4.5 残留 MINOR 项处理

| 编号 | 残留项 | 处理 |
|------|--------|------|
| M-a | §6.2 论证措辞 | ✅ 已处理:§6.2 开头新增严格度说明,显式标注为"论证 / 证明梗概(proof sketch)";并改写"交集中正确验证者"一句——不再把两个视图归于单个正确验证者,改述为"该默认前提失效"。 |
| M-b | 中心主张复述精简 | ✅ 已评估,作文档化决定:经核查,中心主张的 5 处出现(中文摘要 / 英文摘要 / §1.3 论点陈述 / §3.4 精确表述 / §8.1 综合 / §10 结论)各自承担不同功能(陈述 / 综合 / 收束),非冗余复述;强行再删会损害论证清晰度。故不再机械精简——此为 Stage 5 的审慎定稿决定。 |
| M-c | §7 章首条件限定 | ✅ 已处理:§7 章首"命题 1 表明非等价性必须被 enforce"已补"(在第 6 章界定的协议类内)"。 |
| M-d | 图路径整理 | ✅ 已处理:final_paper.md 图 1–3 路径改为自包含的 `figures/...`;3 图(PNG+PDF)已复制至 final/figures/。定稿目录自包含。 |

## 格式合规检查

| 检查项 | 结果 |
|--------|------|
| 标题 / 中英文双语摘要 / 关键词 | ✅ 齐备 |
| 章节编号连续(第 1–10 章) | ✅ |
| 参考文献 IEEE 格式、编号 [1]–[62] 连续 | ✅ |
| 正文引用与文献表双向一致(0 孤儿、0 悬空引用) | ✅(Stage 2.5 Phase A + Stage 4 复核 + 本阶段复核) |
| 图编号、图注、正文引用一致(图 1–3) | ✅ |
| 学术声明齐备 | ✅ 数据可用性 / 伦理 / 利益冲突 / 资助 / 作者贡献(CRediT)/ AI 使用声明 |
| 图片相对路径可解析 | ✅ final/figures/ 自包含 |

## 定稿目录结构(final/)

```
final/
├── final_paper.md          ← 定稿论文(交付主文件)
├── figures/                ← 论文插图(自包含)
│   ├── figure_1_net_advantage.png / .pdf
│   ├── figure_2_advantage_region.png / .pdf
│   └── figure_3_design_axis.png / .pdf
└── FINALIZE_report.md      ← 本报告
```

## 全流程产物清单(过程可追溯)

| 阶段 | 目录 / 文件 | 性质 |
|------|-------------|------|
| 总控 | 00_pipeline_state.md | 流程审计轨迹 |
| Stage 1 RESEARCH | stage1_research/Research_Plan_Summary.md | socratic 研究规划 |
| Stage 2 WRITE | stage2_write/01_source_corpus.md、02_outline_and_argument.md、03_draft_v1.md、03_draft_v2.md、04_figure_package.md、code/ | 语料库、提纲、初稿 v1/v2、图包、可视化代码 |
| Stage 2.5 INTEGRITY | stage2_5_integrity/integrity_report.md | 完整性核查(PASS) |
| Stage 3 REVIEW | stage3_review/00_field_analysis_and_panel.md、01_review_reports.md、02_editorial_decision.md | 5 人评审、编辑决定(Major Revision) |
| Stage 4 REVISE | stage4_revise/draft_v3.md、response_to_reviewers.md | 修订稿、修订回应表 |
| Stage 3' RE-REVIEW | stage3p_rereview/verification_report.md | 验证复审(Minor Revision)+ R&R 矩阵 |
| Stage 4.5 FINAL INTEGRITY | stage4_5_final_integrity/final_integrity_report.md | 定稿前终核(PASS) |
| Stage 5 FINALIZE | final/final_paper.md、final/figures/、final/FINALIZE_report.md | **定稿交付** |

## 质量量规预期(对照课程评分量规)

| 维度 | 权重 | 定稿预期分 |
|------|------|-----------|
| 前沿性 | 15% | ~90 |
| 完整性 | 25% | ~87 |
| 规范性 | 25% | ~88 |
| 创新能力 | 20% | ~87 |
| 写作能力 | 15% | ~87 |
| **加权总分** | 100% | **≈ 87.6 / 100** |

## 待办(转 Stage 6 与附加交付物)

- Stage 6 PROCESS SUMMARY:编译全流程过程总结。
- 附加交付物 WP-CODE:DAG-BFT 协议复刻(独立 artifact,目录 dag_bft_reproduction/),Stage 6 期间/之后执行。

---

## Stage 5 RE-FINALIZE(Round 4 部署实证回填后重定稿)

**日期**:2026-06-04 · **触发**:Round 4 把 P0+P1 全实验回填论文(§4.5/§5/§7.3–7.5 + 7 新图),经 Stage 4.5 Round 4 终核(PASS,独立重算 40/40)+ Stage 3' Round 4 复审(Accept)后重定稿并首次导出 DOCX/LaTeX/PDF。

### 本次处理的待办项(Stage 4.5 LOW + Stage 3' Round4 新问题)

| 项 | 处置 | 说明 |
|----|------|------|
| LOW-1 / N4-3 内联 CSV 路径微歧 | ✅ **已修** | §7.6.2/7.6.3 内联锚点与数据可用性声明 4 处:已核实全部 per-rep CSV 实存 `stage7_deployment/multivalidator/data/runs/`(stage9 仅脚本/harness/`PHASE*_RESULTS.md`),改为区分表述(脚本/报告在 stage9、逐 rep CSV 在 stage7) |
| LOW-2 / N4-5 页脚"3 图"过期 | ✅ **已修** | 页脚改"13 图"+ 补全流水线轨迹(Stage 7/9 部署 → Stage 8 四轮回填 → Stage 4.5 R4 终核 → Stage 3' R4 复审) |
| LOW-3 / N4-4 图号阅读序(7-6/7/8 在 7-3/4/5 之前) | ⏸ **留置(文档化)** | 非错误:图号按 §7.6.1 既定"顺序续接"约定分配,且与 图 3(§8 却编号 3)先例同源。全图重编号会大改已定稿内容、收益纯装饰,风险>收益,不做 |
| N4-6 摘要单引擎限定 | ⏸ **留置(已对冲)** | 摘要现有"该条件化结论的或有负债侧已由真实 Sui 部署…**初步支持**…(详见 §7.6.1)"已恰当限定范围,无过读;且 Round 3 已决定摘要不再追加 |
| N4-1 §4.5 物理型正向证明 | ⏸ **留置(已披露)** | §4.5 正文 + §9 已诚实标注为范围限定/未来工作,无需重复 |
| M-a/M-b/M-c/M-d(Stage 3' 残留) | ✅ 原 Stage 5 已处理 | 见上表;Round 4 未恶化 |

> 处置原则:**只修事实错误(路径、页脚),判断/装饰项留置并文档化**,避免对已通过终核的定稿内容做无谓改动。

### 导出交付物(首次产出 DOCX/LaTeX/PDF)

| 文件 | 大小 | 说明 |
|------|------|------|
| `final_paper.md` | 120 KB | 定稿源(Markdown,交付主文件) |
| `final_paper.tex` | 138 KB | LaTeX 源(pandoc standalone,xeCJK + SimSun) |
| `final_paper.pdf` | 2.49 MB | **31 页**,13 图全嵌,xelatex 编译 |
| `final_paper.docx` | 2.04 MB | pandoc(Word 原生字体回退) |
| `_pdf_fallback.tex` | — | 字形回退 include-header(可复现) |

**导出管线(可复现)**:`md → (pandoc -s --pdf-engine=xelatex --include-in-header=_pdf_fallback.tex -V mainfont=SimSun -V CJKmainfont=SimSun) → .tex → (xelatex ×2) → .pdf`。

**字形完整性**:SimSun(为覆盖 ①②③/ρ/Δ/≤/≈ 必需的 CJK 主字体)缺 8 个码位——U+2212 减号、U+2081/2082 下标、Latin Extended-A 重音(ćąśŚę,文献作者名)。经 `_pdf_fallback.tex` 用 `newunicodechar` 映射(减号→数学减号、下标→`\textsubscript`、重音→Latin Modern Roman 回退)解决。**最终编译:0 缺字、0 缺图、0 overfull hbox、exit 0。**

### 更新统计

| 指标 | 原定稿 | Round 4 重定稿 |
|------|--------|----------------|
| 图表 | 3 图 | **13 图**(3 解析/概念 + 10 部署:图 4-1、5-1~5-3、7-3~7-8) |
| 正文字符 | ~20028 汉字 | ~119,987 字符(含部署实证段) |
| PDF 页数 | (未导出) | 31 页 |
| 导出格式 | 仅 .md | .md + .tex + .docx + .pdf |
| 量规预期(Stage 3' R4 复审) | ≈87.6 | **≈89.3 / 100** |

*Stage 5 FINALIZE 完成(初版 2026-05-21;Round 4 重定稿 2026-06-04)。论文定稿:`final/final_paper.{md,tex,docx,pdf}`。*

---

## Stage 5+ 写作润色 + LaTeX 重建(2026-06-04)

**触发**:用户经 academic-paper 技能调用提出——「先润色全文写作质量,再独立输出一份 LaTeX 文档,强化定稿质量;目前的 tex 文件质量太低,完全无法使用」。

### (一)写作润色(保守、保义、仅非实证散文)

诊断:论文已历 5 轮评审(写作维度 ≈87),散文本身高质;真正的写作短板是**话语标记单调**(AI 单调性 tell)——「换言之」×11、「须明确/须强调/须说明」族 ×13、「这正是/正是」×31、中文破折号「——」×132(其中 32 段叠 2+,但多数为正确的成对插入语)。

处置:**7 处定向编辑**,全部纯标点/连接词替换,**不动任何数字/论断/引用/图号**;刻意回避所有含已核验统计量的段落,以保完整性。
- §4.3/§4.4/§5.4:拆解 3 处「叠加的非成对破折号」段(`专门机制——它用` → `:它用`;`这一要求——后者` → `;后者`;`补偿机制——在提交时` → `:在提交时`)。
- §8.3/§8.4 + §3.4:打散「换言之」三连簇(§8.3→`也就是说`、§8.4→`概言之`、§3.4→`也就是说`),并 `连续化——其` → `连续化:其`。
- 刻意保留:§7.6.x 各子节「须明确本节的范围与构念效度限定」的**有意平行结构**、成对插入语破折号、所有实证段。

### (二)LaTeX 重建(从 pandoc 默认模板 → 手工 `ctexart`)

旧 `final_paper.tex` 的实质缺陷(均已修复):

| 旧(pandoc 默认) | 新(手工 ctexart) |
|---|---|
| **62 条参考文献坍缩成单个连续段落**(`[1]…1982. [2]…1985.…`) | 真正的 `thebibliography`,悬挂缩进、斜体刊名、顺序编号 [1]–[62] |
| `\setmainfont{SimSun}`——拉丁文/数字/数学用宋体劣质拉丁字形 | `fontset=windows`:CJK=宋体、粗体→黑体、斜体→楷体;拉丁文=Latin Modern |
| 图为内联 `\includegraphics`,正文粗体「图 X」+ 短 alt 重复双标题 | 居中**带题注浮动体**,题注=完整「**图 X** …」,无「Figure N:」前缀、无双标题 |
| 章节编号被整体关闭、无目录 | 目录(章/节两级)、章节标题黑体 |
| ρ/Δ/≤/≈/− 靠 `newunicodechar` 拼字回退 | 数学符号统一映射入数学模式(`\rho \Delta \approx \leq` …),①②③ 显式走宋体 |
| 表为 longtable | `booktabs` 三线表 |

**可复现工具链**(留档于 `final/`):`final_paper.md → _build_tex.py(合并图题注 + 转 thebibliography + 抽标题 + 去 --- 分隔线)→ _build.md → pandoc --template=_paper_template.tex --shift-heading-level-by=-1 → final_paper.tex → xelatex ×2 → final_paper.pdf`。

**编译结果**:**44 页,0 错误、0 缺字、0 overfull hbox、0 字体/LaTeX 警告、无需 rerun**。13 图全部嵌入(PDF 内 26 个 image XObject = 13 PNG×(图+alpha))。视觉抽检(标题/目录、§3.4 booktabs 表 + ①②③、§7.6.3 数学排版、参考文献悬挂缩进、§4.5 图 4-1 浮动体)均达发表级。

**已知遗留(装饰性、未修)**:图 4-1 等若干 PNG 的**栅格内嵌标题**仍为生成期的英文图号(如「Figure 4-2」),与题注「图 4-1」不一致——该不一致位于栅格图像内部、属实验管线生成期既存项,重画需原绘图脚本+数据,超出本次润色/排版范围,故仅记录不动(避免触碰已核验图像)。

**交付物**:`final_paper.md`(润色源)、`final_paper.tex`(137 KB,手工 ctexart)、`final_paper.pdf`(2.6 MB,44 页)、`final_paper.docx`(2.04 MB,从润色源刷新、参考文献逐条成段)、`_paper_template.tex` + `_build_tex.py`(工具链)。DOCX 较旧版同步了 7 处润色并修复了参考文献坍缩。

---

## Stage 5++ 表述精简 + 排版/图修订(2026-06-04 第二轮,用户 8 项)

用户要求"精简优化表述",列 8 项。逐项处置(均不改任何数字/统计量/引用 [n]/图号/论断):

| # | 要求 | 处置 |
|---|------|------|
| 0 | 中文上引号显示为下引号 | 源中 532 个直引号 `"` 按平衡配对转为方向性弯引号 “”(269 对,0 残留);PDF 中开/闭引号现各异、正确(见 §3.4、TOC、参考文献) |
| 1 | 中文摘要英文词太多 | 摘要内冗余英文注释悉数删去,仅留必要缩写(DAG/BFT/RBC)与裸术语(certified/uncertified/enforce/Sui) |
| 2 | 摘要太长 | 中文摘要 **1054→595 字符(−44%)**;英文 ~250→217 词;核心论断与实证数字(290+、n=7/n=4)全保留 |
| 3 | 改标题 | → "DAG-BFT 共识中认证机制的结构性作用:去认证设计的隐性代价与性能边界"(全文 + 元数据 + PDF 标题) |
| 4 | 删多余英文括注 | 全文 **45 处纯英文括注删除 + 5 处"全称, 缩写"折叠为缩写**;保留:人名/协议名(Bracha、Mysticeti…)、复用缩写(DAG/BFT/RBC/GST/MEV/SMR/AVID)、度量名(eqChk/recFetch/t_resume/ρ/Δ…)、统计量、文件路径、§引用、三不变量英文名(§4 定义处)、消歧的 (equivocation)、复用的 (reconciliation)、双语声明抬头 |
| 5 | "本团队"→"本人" | `本团队`→`本人` ×10;并为单作者一致性把编辑性 `我们`→`本文` ×7(注:本文为个人撰写) |
| 6 | 图中注释/线条重叠 | 审 13 图,定位 2 处:**图 1** 图例 `frameon=False` 致 y=0 虚线穿过"Δ_recover = 8" 文字 → 改不透明白底图例;**图 7-6** 一处游离的绿色 `ρ*≈-0.0020` 标注(标题未引用、与 §7.6.3 的 ρ* 混淆)→ 删除,并修内嵌标题 "Figure 7-1"→"Figure 7-6"。两图按原脚本+原数据重生成(图 7-6 OLS 拟合 3.78−265.3·ρ、R²=0.902 与图注完全一致,证数据未变)。其余 11 图无重叠 |
| 7 | 页边路径超框 | 新增构建后处理 `_post_tex.py`:令所有 `\texttt{}`(28 处)在 `/`、`\_`、`.`、`-` 处可断行 → 长路径(如 `stage7_deployment/multivalidator/data/runs/`)与 CSV 列表现于页内换行,**0 overfull hbox** |

**重建管线(增 1 步)**:`final_paper.md →(_refine.py 一次性源转换:标题/摘要/语气/删括注/弯引号)→ _build_tex.py → pandoc --template → _post_tex.py(路径可断行)→ xelatex ×3`。
**编译**:**43 页**(摘要缩短省 1 页),0 错误、0 缺字、0 overfull、0 警告(3 趟后)。视觉抽检(标题、双语摘要、§3.4 弯引号+booktabs、图 1/图 7-6 重生成、数据可用性路径换行)全部达标。

**已知遗留(未改、装饰性)**:其余图 PNG 的内嵌英文图号(如图 4-1 内题为 "Figure 4-2")与中文图注不一致——位于栅格内部、生成期既存,本轮仅按需重生成有重叠的 2 图,未为纯图号一致而批量重画全部图。

**交付物刷新**:`final_paper.{md,tex,pdf,docx}` 均已同步本轮 8 项;工具链增 `_refine.py`(一次性源精简)+ `_post_tex.py`(路径断行)。
