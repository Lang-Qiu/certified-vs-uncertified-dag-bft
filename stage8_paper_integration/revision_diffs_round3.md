# 阶段三 Round 3 —— 回填提案（最小 diff，待逐点二次确认）

**数据源**: Route A1 certified 对照臂部署实证 —— `stage9_cross_protocol_calibration/`
`PHASE1_RESULTS.md`（Δ_save）、`PHASE2_RESULTS.md`（恢复不对称 + ρ*(Δr) crossover），
harness `phase1_certgate_pilot.ps1`/`phase2_recovery_asymmetry.ps1`/`phase2c_excess_sweep.ps1`，
图 `figures/phase2c_rho_star.png`。
**门禁**: 本文件仅为提案；`final/final_paper.md` 在用户对以下各点二次确认后才编辑。
**性质（强于 Round 1/2）**: 这是论文**首次拥有一个 certified 对照臂**。它把 §7.2 现有的"无 certified
臂、定量标定属未来工作"这一**中心限定**（§7.2 第 313 行、§7.6.1、§7.6.2、§9 第 464 行、§10 第 478 行）
转为一个**已交付结果**。因此本轮不只新增 §7.6.3 + 图 7-5，还须**改述 4 处"未来工作/无 certified 臂"
旧表述**。构念效度限定全程保留并进一步强化（可用性证书≠密码学签名、单引擎、注入式旋钮、ρ* 为 band）。

核心实证主张（Round 3 新增）：
- **Δ_save 首次在部署上测得为正且可观**：cert ON 比 OFF 慢 ≈0.116 s/commit（认证确认轮的延迟）。
- **认证缩减恢复或有负债（不对称）**：同故障同 Δ_recover 下 cert ON 恢复更廉（fetch 123 vs 196、每故障
  t_resume 省 excess≈3–9 s，excess 随 Δ_recover 增长）。
- **净优势翻转 ρ\* 首次定量定位**：ρ\* ≈ 0.013–0.038 faults/commit（≈1 关键路径故障/26–78 commits）。
- **诚实的模型偏离（H3）**：amortized 直接观测下 net_advantage 非单调（R²=0.02），印证 §7.4 的 ρ–Δ_recover
  耦合；须用分解观测方能干净标定。

---

## EDIT R3-1【主】新增 §7.6.3（插入到 §7.6.2 图 7-4 之后，第 382 行 `![图 7-4 ...]` 行之后）

**操作**: 追加新子节，不改动 §7.6.1/§7.6.2 任何现有文字。

**新增内容（after）**:

```
#### 7.6.3 含 certified 对照臂的净优势翻转标定

§7.6.1、§7.6.2 在单一 uncertified 协议上刻画了或有负债侧的形状;它们都明确"无 certified 对照臂、非 §7.2 的定量标定"。本节补上这条对照臂,把 §7.2 成本模型的三个量——Δ_save、认证对恢复成本的缩减、以及净优势翻转频率 ρ\*——首次提升为真实 n=7 部署的实测。

操作化(受控 minimal-pair):在同一 Sui/Mysticeti binary 上把认证做成一个可开关的 certificate-gate。cert ON 时,一个父轮祖先区块仅当被一个 2f+1 权益 quorum 独立接受(经 Sui 已有的 RoundProber 确认通道直接观测,而非靠后续轮的提案引用隐式推断)后,方可被新区块引用——这把 certified-DAG 中"区块须先成证书再被构建于其上"的独立确认轮显式加回;cert OFF 即原生 uncertified Mysticeti。两臂共用同一引擎、同一提交规则与 leader 调度,仅"认证强度"这一单变量不同,从而规避 §3.3 所警惕的跨引擎混淆。

实证给出四项判断。其一(Δ_save 为正且可观):良好情形(无故障)下 cert ON 的共识 cadence 系统性低于 cert OFF(4.58→2.99 ckpt/s,约 0.116 s/commit)——这正是 §7.2 中 uncertified 省去的认证确认轮延迟,首次在部署上被测得为一个正的、可观的 Δ_save。其二(认证缩减恢复侧或有负债):在与 §7.6.2 相同的关键路径轮转故障、相同 Δ_recover 下,cert ON 恢复得更便宜——恢复拉取次数更少(123 vs 196),恢复停顿 t_resume 更短(每故障省 excess≈3–9 s),且这一节省随单次恢复成本 Δ_recover 增大而增大(线性拟合斜率为正,R²≈0.49)。机制:gate 只引用已被 quorum 持有的区块,故落后节点恢复时其缺失祖先已被 2f+1 节点持有,拉取更廉。这是 §7.5"认证在传播阶段事前均摊数据分发、因而在不利条件下恢复更鲁棒"一论断的部署确证。其三(净优势翻转 ρ\* 的定量定位):把良好情形的 Δ_save(0.116 s/commit)与每故障的恢复成本之差 excess(Δ_recover) 结合,可解出净优势归零的临界故障率 ρ\* ≈ 0.013–0.038 次/commit(约一次关键路径故障每 26–78 个 commit):故障频率高于此则 certified 占优,低于此则 uncertified 占优;ρ\* 随 Δ_recover 增大而下降(恢复越贵,certified 在越低的故障率即完成翻转)。这是 §7.2 条件化翻转——"存在一条净优势归零的边界 ρ\*"——在真实部署上的首次定量定位。其四(诚实的模型偏离,呼应 §7.4):若改用单一定窗的 amortized cadence 直接测净优势,则净优势对 Δ_recover 呈非单调(线性拟合 R²≈0.02)——一次性的恢复成本被测量窗稀释,且在极高 Δ_recover 下 certificate-gate 会延长地排斥仍在恢复、尚未被 quorum 接受的落后节点,形成一个与"恢复更廉"相竞争的效应。这一偏离印证了 §7.4 所述 ρ 与 Δ_recover 在极端条件下的耦合:闭式 net_advantage 在 amortized 观测下并非严格线性,只有用分解观测(清洁的 Δ_save 速率 + 清洁的每故障恢复成本差)方能干净标定 ρ\*。

须明确本节的范围与构念效度限定,其约束承自 §7.6.2 并进一步具体化。此 certificate-gate 实现的是认证的**可用性证书**(被一个 2f+1 quorum 接受),**非**密码学意义的 2f+1 签名聚合;Δ_save 因此是"等 quorum 接受再引用"这一独立确认轮的延迟,经真实 RoundProber 网络通道度量——它比一个纯注入式 sleep 更忠实(确实动用了一个独立的确认往返),但仍**不是**对真实 Bullshark/Narwhal RBC 签名开销的测量。实证仍在单一引擎(Mysticeti 加/去 gate)上展开,而非两套独立协议的 benchmark;Δ_recover 仍为注入式旋钮;ρ\* 为一个 band(2 次重复,Δ_recover=500 处有一个噪声离群点),可信的是其量级而非精确值。因此本节标定的是 certified/uncertified 净优势的**成本结构**——Δ_save 为正且可观、认证确实缩减恢复侧或有负债、且存在一个 ρ\* 翻转——而非某一对真实协议的绝对延迟比较。复现 harness、Route A1 共识源码改动与逐 rep 数据见 `stage9_cross_protocol_calibration/`(`PHASE1_RESULTS.md`、`PHASE2_RESULTS.md`、`phase2c_excess_sweep_summary.csv`)。

**图 7-5** 含 certified 对照臂的净优势翻转标定。左:关键路径故障下两臂的恢复停顿 t_resume 随 Δ_recover 的剂量响应(上:cert OFF/uncertified;下:cert ON/certified;绿带=认证带来的恢复节省 excess);右:由 Δ_save 与 excess(Δ_recover) 解出的净优势翻转故障率 ρ\*(Δ_recover)——其上 certified 占优、其下 uncertified 占优。注:本图为真实 n=7 Sui 部署实测;cert-gate 为可用性证书(非密码学签名),Δ_recover 为注入式旋钮。
```

`![图 7-5 含 certified 臂的净优势翻转标定](figures/figure_7_5_certified_arm_crossover.png)`

---

## EDIT R3-2【轻触】§7.2 第 313 行 Monte Carlo 段末追加一句（软化"超出本文范围"）

**before（第 313 行末尾）**:
```
...后者需要真实协议实测,超出本文范围(见第 9 章)。仿真真正新增的信息是净优势的**方差**...
```

**after**（在"超出本文范围"句后插入一句，再接原"仿真真正新增"）:
```
...后者需要真实协议实测;§7.6.3 以一个同引擎、可开关的 certificate-gate(认证的可用性证书操作化)对这一闭式模型作了首个部署层面的对照标定——实测到一个正的 Δ_save、认证对恢复成本的缩减、以及一个净优势翻转的 ρ\* band,同时也观察到 amortized 观测下对线性闭式的偏离(见 §7.4 的耦合)。仿真真正新增的信息是净优势的**方差**...
```

---

## EDIT R3-3【轻触·可选】§7.2 第 311 行 ρ\* 句后追加半句部署旁证

**before（第 311 行）**:
```
...§7.6.2 的部署标定为这一独立性简化提供了一个旁证:Δ_recover(每事件恢复时延)与恢复事件频率作为两个成本轴在实测中可分离。下文逐一分析...
```

**after**:
```
...§7.6.2 的部署标定为这一独立性简化提供了一个旁证:Δ_recover(每事件恢复时延)与恢复事件频率作为两个成本轴在实测中可分离。§7.6.3 进一步以含 certified 对照臂的部署实测,把这一翻转频率 ρ\* 首次定量定位在约 0.013–0.038 次/commit(单引擎可用性证书操作化下),并诚实地标出 amortized 观测对线性闭式的偏离。下文逐一分析...
```

---

## EDIT R3-4【改述】§9 威胁有效性 第 464 行（"未来工作的主要方向"已部分交付）

**before（第 464 行）**:
```
本文已对其中的或有负债侧提供了首个真实部署探查(§7.6.1),但那是单一 uncertified 协议上的故障代价实测;一个完整的定量标定仍需含 certified 对照臂的跨协议受控实证,这构成本文未来工作的主要方向。
```

**after**:
```
本文已对其中的或有负债侧提供了部署探查(§7.6.1、§7.6.2),并以一个同引擎、可开关的 certificate-gate 构建了 certified 对照臂(§7.6.3),首次在部署上测得正的 Δ_save、认证对恢复成本的缩减、以及净优势翻转的 ρ\* band。须明确这条对照臂的限定:它实现的是认证的可用性证书(2f+1 接受)而非密码学签名聚合,仍为单引擎、Δ_recover 为注入式旋钮,故标定的是净优势的成本结构而非真实协议对的绝对延迟。一个以真实 RBC 签名开销为对照、跨两套独立引擎的受控 benchmark 仍属未来工作。
```

---

## EDIT R3-5【改述】§9 注入式旋钮构念效度 第 454 行末（"无 certified 对照臂"已不再成立）

**before（第 454 行末）**:
```
...它精化而非削弱 §7.3 的或有负债论断。该实证仍限于单一 uncertified 协议、无 certified 对照臂。
```

**after**:
```
...它精化而非削弱 §7.3 的或有负债论断。§7.6.3 进一步补上了一条 certified 对照臂(同引擎、可开关的 certificate-gate),其构念效度限定与本段同源并更强:该 gate 捕获的是认证的可用性证书(2f+1 接受,经 RoundProber 确认通道观测)而非密码学 2f+1 签名,故其 Δ_save 是独立确认轮的延迟代价、其 ρ\* 是成本结构意义上的翻转点,均不可外推为某真实 RBC 协议的绝对数值。
```

---

## EDIT R3-6【改述】§10 未来工作 第 478 行末（certified 臂已操作化）

**before（第 478 行末）**:
```
...§7.6.2 进一步以受控旋钮标定出或有负债沿 Δ_recover 轴近似线性、随委员会收缩而加剧、且仅在恢复处于关键路径时 materialize;尚待完成的是含 certified 对照臂的跨协议受控实证,以定量标定 Δ_save、Δ_recover 与 ρ 三个参数。
```

**after**:
```
...§7.6.2 进一步以受控旋钮标定出或有负债沿 Δ_recover 轴近似线性、随委员会收缩而加剧、且仅在恢复处于关键路径时 materialize;§7.6.3 则以一个同引擎、可开关的 certificate-gate 补上 certified 对照臂,首次在部署上把 Δ_save 测为正、确认认证缩减恢复成本、并把净优势翻转 ρ\* 定量定位于约 0.013–0.038 次/commit。尚待完成的是把这条可用性证书的对照臂升级为含真实 RBC 签名开销、跨两套独立引擎的受控 benchmark,以从"成本结构标定"推进到"真实协议对的绝对延迟比较"。
```

---

## EDIT R3-7【轻触】数据可用性声明 第 484 行末追加一句

**before（第 484 行末）**:
```
...§7.6.2 的恢复侧旋钮标定(图 7-4)来自带受控 Δ_recover 旋钮的 Sui 构建在关键路径轮转故障下的部署实测,其 harness、逐 rep 数据(`phaseA_criticalpath_*.csv`)与图表生成脚本存档于 `stage9_cross_protocol_calibration/`。
```

**after**:
```
...§7.6.2 的恢复侧旋钮标定(图 7-4)来自带受控 Δ_recover 旋钮的 Sui 构建在关键路径轮转故障下的部署实测,其 harness、逐 rep 数据(`phaseA_criticalpath_*.csv`)与图表生成脚本存档于 `stage9_cross_protocol_calibration/`。§7.6.3 的 certified 对照臂标定(图 7-5)来自同一 Sui 构建中一个可经环境变量开关的 certificate-gate(Route A1,认证的可用性证书操作化)在关键路径轮转故障下的部署实测,其共识源码改动、Phase 1/2 harness、逐 rep 数据(`phase2c_excess_sweep_summary.csv` 等)与图表脚本一并存档于 `stage9_cross_protocol_calibration/`。
```

---

## EDIT R3-8【资产】新增图文件

`final/figures/figure_7_5_certified_arm_crossover.png` ← 复制自
`stage9_cross_protocol_calibration/figures/phase2c_rho_star.png`
（双面板：左=两臂 t_resume 剂量响应 + excess 绿带；右=ρ\*(Δr)）。

---

## 明确不做（本轮范围外）

- **摘要不再追加**：Round 1 已写入或有负债实证一句；certified 臂细节属同一论据的纵深，保持摘要简洁。
- **§1.3 / §1.5 贡献不改**：§7.6.3 是 §7.6 实证线的纵深，不另起贡献，不改贡献结构。
- **§7.2 闭式公式、图 1/图 2 不改**：模型本体不动；§7.6.3 是对它的部署对照，不替换解析图示。
- **不宣称"certified 绝对更优/更差"**：全程限定为成本结构标定，与 §7.5"相对斜率而非绝对最坏情况"一致。
- **标题、章节编号层级、贡献结构不变。**

## 验证清单（编辑后执行）

- 构念效度自检：§7.6.3 是否明确"可用性证书≠密码学签名、单引擎、注入式 Δ_recover、ρ\* 为 band、非真实协议绝对比较"？
- 数字一致性：§7.6.3 的 0.116 s/commit、123 vs 196、excess 3–9 s、R²≈0.49、ρ\* 0.013–0.038、amortized R²≈0.02 与 `PHASE1_RESULTS.md`/`PHASE2_RESULTS.md`/CSV 逐一对账。
- 旧表述一致性：§7.2(313)、§9(464)、§9(454)、§10(478) 的"无 certified 臂/未来工作"是否已改述且不与新 §7.6.3 自相矛盾？
- 交叉引用闭合：§7.2→§7.6.3、§9→§7.6.3、§10→§7.6.3、图 7-5 引用存在；图号 表 7-1→图 7-3→图 7-4→图 7-5 连续。
- 受保护文件 `consensus_metrics.json` 未被触碰；未引断言扫描。
