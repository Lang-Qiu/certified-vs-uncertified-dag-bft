# Pipeline State — 区块链论文(DAG 型 BFT 共识协议)

| 项目 | 值 |
|------|-----|
| 启动日期 | 2026-05-20 |
| 编排器 | academic-pipeline v3.7.0 |
| 论文方向 | DAG 型 BFT 共识协议(理论+实证,实验驱动) |
| 语言 | 中文为主,术语保留英文 |
| 目标篇幅 | ~20000 字,参考文献 ≥ 60 篇 |
| 当前阶段 | Post-Finalize 实证回填(Round 1-3 已落地) + Chapter 5 enforcement-path 部署实验(进行中) |

## 评分量规映射
| 维度 | 权重 | 主责阶段 |
|------|------|----------|
| 前沿性 | 15% | Stage 1 |
| 完整性 | 25% | Stage 2 + Stage 3 |
| 规范性 | 25% | Stage 2.5 / 4.5 + Stage 5 |
| 创新能力 | 20% | Stage 1 socratic + Stage 3 DA |
| 写作能力 | 15% | Stage 2 + Stage 3 |

## 阶段进度
- [x] Stage 1 RESEARCH — socratic 引导 ✅ 完成(交付物:stage1_research/Research_Plan_Summary.md)
- [x] Stage 2 WRITE — full 模式 ✅ 完成(含 visualization_agent 产出)
  - Phase 0-4 完成;交付物:01_source_corpus.md(62 篇)、02_outline_and_argument.md、03_draft_v2.md(~21000 字,双语摘要内含,3 图已集成)
  - draft v1 因篇幅不足 + 22 处引用孤儿,已被 v2 取代修复
  - visualization/simulation:code/dag_bft_model.py(成本模型+Monte Carlo)、code/make_figures.py、code/figures/(Figure 1-3,PNG+PDF 300DPI)、04_figure_package.md
  - 仿真自检通过:解析值 vs Monte Carlo 仿真均值收敛(误差<0.5%);图表 VLM 核验 2 轮修正重叠
- [x] Stage 2.5 INTEGRITY — Mode 1 评审前核查 ✅ 完成(裁决 **PASS**,修正后)
  - 交付物:stage2_5_integrity/integrity_report.md
  - Phase A:62 篇文献全 Web 核验真实存在;修正 24 处瑕疵(1 SERIOUS [50] OmniLedger 作者首字母 H→E、1 MEDIUM [6] AVID 页码 191-201→191-202、22 LOW 移除未核实会议页码)→ 10 处 Edit 全成功,0 残留
  - Phase B 引用语境 / C 数据核查 / D 原创性(ORIGINAL)/ E 论断核查:全部 PASS
  - 七模式 AI 研究失败模式排查:全部 CLEAR
- [x] Stage 3 REVIEW — full 模式 5 人评审 ✅ 完成(决定 **Major Revision**)
  - 交付物:stage3_review/00_field_analysis_and_panel.md、01_review_reports.md(5 份)、02_editorial_decision.md
  - 加入课程评分量规校准层;当前初稿量规合议分 ≈ 81.3/100,大修后预期 ≈ 87–88
  - Devil's Advocate 未发现 CRITICAL;5/5 评审一致建议大修
  - 修订路线图 13 项:P0 ×4(R-1 命题1证明、R-2 因果历史定义矛盾、R-3 中心主张收窄、R-4 ρ*范围)、P1 ×5、P2 ×4
- [x] Stage 4 REVISE — academic-paper revision 模式 ✅ 完成
  - 用户选择"直接修订(just fix it)";R-3/R-8 采用保守方案(非平凡内核重定位为"可预测的不对称")
  - 交付物:stage4_revise/draft_v3.md(由 v2 修订)、response_to_reviewers.md
  - 13/13 修订项全落实:命题 1 证明改用 quorum 交集论证(§6 重写)、因果历史完整性重定义为纯结构性质、中心主张非平凡内核重定位、ρ\* 独立性假设声明、新增 §7.7 设计者判定程序、贡献 C 收窄并补 conjecture、§8.5 补 MEV 攻击草图、成本台账对称性、[29] 补引等
  - 核验:全 62 篇文献 0 孤儿;3 图路径已调整为 ../stage2_write/code/figures/
- [x] Stage 3' RE-REVIEW — re-review 验证模式 ✅ 完成(决定 **Minor Revision**)
  - 交付物:stage3p_rereview/verification_report.md(含 R&R 可追溯矩阵 Schema 11)
  - 13/13 修订项全部落实且与作者声明一致(11 项 fully、2 项 substantially addressed)
  - 4 项 MINOR 残留(M-a §6.2 论证措辞、M-b 复述、M-c §7 章首限定、M-d 图路径)→ 全部转 Stage 5 定稿处理
  - 未发现 MAJOR 新问题;修订后量规预期 ≈ 87.6/100
- [x] Stage 4' RE-REVISE — 不需要(Stage 3' 决定 Minor,无 MAJOR 残留)
- [x] Stage 4.5 FINAL INTEGRITY — Mode 2 定稿前终核 ✅ 完成(裁决 **PASS**)
  - 交付物:stage4_5_final_integrity/final_integrity_report.md
  - 聚焦 Stage 4 新增/重写内容(§6 重写、§7.7、§8.4–8.5、§3.4、§4.1/4.4、§9)
  - 发现并修正 1 处 MINOR:§6.2 quorum 交集算术(2f+1→n−f 的精确化,对全部 n≥3f+1 严格)
  - A-E 五阶段 + 七模式复核全部 PASS/CLEAR
- [x] Stage 5 FINALIZE ✅ 完成
  - 交付物:final/final_paper.md(定稿)、final/figures/(自包含,3 图 PNG+PDF)、final/FINALIZE_report.md
  - 4 项 MINOR 残留处理:M-a/M-c/M-d 已落实;M-b 经评估作文档化决定(5 处复述各有功能,不机械精简)
  - 定稿统计:正文 20028 汉字、62 篇文献(0 孤儿)、10 章、3 图、双语摘要、声明齐备
  - 格式合规检查全过;量规预期 ≈ 87.6/100
- [x] Stage 6 PROCESS SUMMARY ✅ 完成
  - 交付物:final/paper_creation_process.md(全流程记录 + AI 自我反思 + 协作质量评估)
  - 协作质量评分 83/100;AI 自我反思谄媚风险 MEDIUM(1 次健康警报,已化解)
  - 关键自省:初稿命题 1 证明在 f<n/3 下不成立,Stage 3 评审捕获——评审门有效性的实证

**🎉 academic-pipeline 10 阶段主流程全部完成。定稿:final/final_paper.md**

## 附加交付物(WP-CODE):DAG-BFT 协议复刻 → ⚠️ 已作废,被真实部署超越

~~**性质**:课程作业的支撑代码,独立 artifact;不冒充论文核心实验。~~
~~**执行时机**:论文主体经 Stage 3 评审 + Stage 4 修订定稿后、Stage 5 定稿期间并行/Stage 6 之前。~~
~~**范围(分阶段)**:~~
~~- 主流程(优先):DAG 构建 → 轮次推进 → 可靠广播(RBC)/认证 → anchor 提交规则 → 本地全序输出。~~
~~- 可选扩展:uncertified 变体对照、故障注入、与论文第 7 章成本模型呼应。~~
~~**目录**:E:\LQiu\lab_folder\Blockchain_final_pipeline\dag_bft_reproduction\~~

**作废原因(2026-06-01)**:论文的实证路线已完全超越"happy-path 复刻"的规模——改为在**真实 Sui/Mysticeti 源码**上做受控部署实验:
- Stage 7: 290+ 次受控故障注入(n=7/n=4,多验证者 Docker compose)
- Stage 9: cert-gate(Route A1,可用性证书) + Δ_recover 旋钮 + 关键路径轮转故障法
- Stage 9 Chapter 5: 三条 enforcement 路径 instrumentation(非等价性/因果历史/可用性 reconciliation)的故障强度扫描

WP-CODE 的"certified DAG happy-path 复刻"在贡献上已被上述真实部署实证完全覆盖与超越。

## Stage 1 socratic 进度
- Layer 1 PROBLEM FRAMING:✅ 完成
- Layer 2 METHODOLOGY REFLECTION:✅ 完成
- Layer 3 EVIDENCE DESIGN:✅ 完成。证据骨架 = E1+E2+E3 互补 + E4 作锚;证伪策略 = F1/F2/F3 + F4(必要性论证,用户决定执行)。
  - [HEALTH-CHECK] 第 2 轮检测到 Persistent Agreement → 注入 challenge 后用户恢复实质性论证(给出 F4 理由 + availability 推理)。
- Layer 4 CRITICAL SELF-EXAMINATION:✅ 完成。两记 DA 挑战 → 论文两处诚实声明(判据预先讲定 / 模型范围诚实标注)。
- Layer 5 SIGNIFICANCE & CONTRIBUTION:✅ 完成。用户决定"爬 C",主贡献 = 深层轴论证。

5 个 Layer 全部完成,S1-S5 收敛信号齐亮,Research Plan Summary 已编译。

## 收敛状态
4 个收敛信号全亮(S1 论点清晰 / S2 反论意识 / S3 方法论自觉 / S4 范围稳定)→ 研究问题已收敛。Layer 4-5 加速推进。

## 工作研究问题(Layer 1 已定型)
主 RQ:在何种网络与敌手条件下,uncertified DAG-BFT 相对 certified 设计的"低延迟优势"才真正成立?
- SubRQ0(潜框架,置于引言/背景):certified 与 uncertified 的比较对象是否公平?(混淆变量/内部效度)
- SubRQ1:认证(Reliable Broadcast)买到了哪些理论保证(非等价性/可用性/因果历史完整性)?
- SubRQ2:去掉认证后,这些保证被转移/重建到哪里,产生哪些隐性代价?
- SubRQ3:延迟优势在哪些条件下成立/被抵消/反转?

## INSIGHT 收集
- [INSIGHT 1] 选定 certified vs uncertified DAG 设计权衡为核心(理由:有研究价值且边界可控);偏好理论深度路线;视延迟(A)与排序公平/MEV(D)为相关利害。
- [INSIGHT 2] RQ 形状 = ③ 条件化结论(骨架)+ ① 隐性代价批判(灵魂);已能一句话陈述论点。
- [INSIGHT 3] 提出 SubRQ0:现有比较可能不公平,本质是混淆变量/内部效度问题;为全文确立方法论警觉。
- [INSIGHT 4] 方法论 = 模块化分解 + 受控 minimal-pair 比较:在相同协议背景下仅改变认证强度,观察保证迁移与代价变化。
- [INSIGHT 5] 核心发现(脊梁):认证不是可拆卸的性能优化模块,而是维持协议不变量的结构性机制 → 去认证 = 结构性替换(structural substitution),非做减法。
- [INSIGHT 6] 模块硬边界须按固定客观标准划定,防止混淆变量被藏入模块内部。
- [INSIGHT 7] 划界的客观标准 = 安全性/活性不变量;每模块 = 维持某一不变量的机制 → 分解去主观化,SubRQ0 闭环合上。
- [INSIGHT 8] 决定执行 F4 必要性论证(理由:论文需理论深度,接受规范性风险)。
- [INSIGHT 9] availability 最难重新安家:逻辑型不变量(non-equivocation、causal-history)可由规则约束;availability 是物理传播问题,规则推不出"数据真被持有" → 隐性代价集中于此,构成 SubRQ2 的分析脊梁。
- [INSIGHT 10] 判据 = C1-B 三分法(平移/削弱+补偿/消除)+ C1-C 成本-证明双判据;中心主张升级为"去认证只产生①②、从不产生③,隐性代价集中在②"。
- [INSIGHT 11] F4 模型 = C2-M3(纯异步严格证明 + 部分同步推广诚实讨论),C2-M4 作安全网写入讨论章。
- [INSIGHT 12] 三不变量的①②③归类是分析章产物,须写成"工作假设 H → C1-C 检验",不可动笔前预设(反同义反复)。

- [INSIGHT 13] 三层递进贡献框架:A=Benchmark-as-truth 批判;B=优势 fundamentality 批判;C=轴批判(深层轴 = availability-enforcement + reconciliation trigger)。
- [INSIGHT 14] C 的风险是 naming/framing 失败(可恢复),非 theory 构造失败 —— 因深层轴已在 INSIGHT 链上隐式跑通。
- [INSIGHT 15] C 结构性抗断章:claim 语法形态决定可滥用性,axis 型陈述无可提取比较句位。
- [INSIGHT 16] B 引用半衰期短,conditional 结论会被 unconditional 后续淹没 → 停 B 等于把 C 让给别人。
- 决策:主贡献定位 = 爬 C。

## 工作假设 H(待论文检验)
non-equivocation、causal-history integrity → 大概率①(逻辑型,可规则化平移);availability → 大概率②(物理型,削弱+补偿)。

## 待决:主贡献定位
爬 C(深层轴,创新天花板高,须构造性交付)vs 停 B(稳健,可能"没用尽")。

## 升级后的中心主张(✅ 用户已确认)
**引言版:** 在 DAG-based BFT 共识中,移除认证(de-certification)并非可分离的性能优化,而是结构性替换(structural substitution)——认证承载的安全性/活性不变量(non-equivocation、availability、causal-history integrity)被重新分配至协议其他组件;故 uncertified 的提交延迟优势是条件性的:当且仅当替代承接机制在目标网络/敌手模型下边际成本低于认证时方成立。
**摘要版:** 移除认证非删除开销,而是将不变量维护责任由广播层转移至共识层;延迟收益仅在替代机制成本低于认证成本的网络—敌手条件下成立。

## 实证路线图(Post-Finalize,2026-05-30 至今)

academic-pipeline 10 阶段主流程于 2026-05-21 全部完成(定稿 final/final_paper.md,纯理论)。此后论文性质经历了从"纯理论"到"理论+实证(实验驱动)"的系统性重定位。

### 三轮回填(已落地)
| Round | 日期 | 内容 | 论文落点 |
|-------|------|------|---------|
| Round 1 | 2026-05-30 | 故障强度轴超可加实证(290+ reps) | §7.6.1 + 表 7-1 + 图 7-3 |
| Round 2 | 2026-05-31 | Δ_recover 关键路径标定(轮转故障法,n=7/n=4) | §7.6.2 + 图 7-4 |
| Round 3 | 2026-05-31 | certified 对照臂(cert-gate)净优势翻转标定 | §7.6.3 + 图 7-5 |

三轮回填均经 [[paper-integration-approval-gate]] 批准后逐点最小 diff 编辑。论文现 = 理论 + 三部署组件。

### 第 5 章 enforcement-path 实验(进行中,2026-06-01)
**目标**:把论文最核心的归纳性主张——§5.2–§5.4 的 ①②③ 归类(非等价性→①平移=固定开销,因果历史→①平移=固定开销,可用性→②削弱+补偿=或有负债)——从定性推理升级为**部署 instrumentation 的定量检验**。

**方法**:在 Mysticeti 源码三条 enforcement 路径植入 Prometheus 计数器 + 直方图:
- Path A(`dag_state.rs:accept_block`):非等价性——own-slot 唯一性检查
- Path B(`base_committer.rs:decide_leader_from_anchor`):因果历史——leader 祖先引文核查
- Path C(`synchronizer.rs` + `commit_syncer.rs`):可用性——reconciliation PULL fetch(已有 STAGE9_RECOVERY)

**Grid**: 2(committee size) × 4(loss: 0%/2%/5%/10%) × 5(reps) = 40 runs。证伪判据已事前锚定(见 `stage9_.../EXPERIMENT_PLAN_CHAPTER5.md`)。

### 仍待实验(按优先级)
| # | 缺口 | 状态 |
|---|------|------|
| 1 | §5.2–§5.4 ①②③ 归类验证 | 🟡 进行中(本实验) |
| 2 | §7.3 ρ(故障频率)独立轴扫描 | ⬜ 待做(现有 harness 可复用) |
| 3 | §7.4 ρ–Δ_recover 耦合(GST 抖动) | ⬜ 待做(需新故障编排) |
| 4 | §7.5 网络非对称 | ⬜ 待做(需 tc 带宽限制) |
| 5 | 真 RBC 签名聚合 certified 臂(非可用性证书 emulation) | ⬜ 深 consensus 子项目 |

### 实验 infra 清单
| 组件 | 位置 | 状态 |
|------|------|------|
| Sui/Mysticeti 源码(sparse-clone) | `stage9_.../sui-src/` @ commit `62ee6ada` | ✅ |
| Docker 构建环境(rust:1.92-bookworm) | 缓存卷 `stage9_cargo_registry`/`stage9_target` | ✅ |
| cert-gate 共识改动(Route A1) | `parameters.rs`/`round_tracker.rs`/`proposer.rs` | ✅ |
| Δ_recover 旋钮 | `synchronizer.rs` + `commit_syncer.rs` | ✅ |
| Chapter 5 三条路径 instrumentation | `metrics.rs` + `dag_state.rs` + `base_committer.rs` | ✅ `cargo check` 绿 |
| n=7 多验证者 compose | `stage7_deployment/multivalidator/` | ✅ |
| n=4 compose(向后兼容 env 注入) | `stage7_deployment/multivalidator/` | ✅ |
| 关键路径轮转故障 harness | `stage9_.../scripts/phaseA_criticalpath_partition*.ps1` | ✅ |
| 丢包故障注入(跨验证者独立) | tc netem via compose exec | ✅ |

## 意图分类
goal-oriented(用户有明确截止任务与交付物 = 课程论文,实验驱动)
