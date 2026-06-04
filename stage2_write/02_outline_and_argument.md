# Stage 2 / Phase 2+3 — 论文大纲与论证蓝图

> 《认证之为结构:DAG-based BFT 共识中去认证的隐性代价与延迟优势的条件性》
> 理论分析型论文 | 目标 ~20000 字(正文)| 引用 IEEE | 中文为主,术语保留英文

## 全文中心主张(thesis)
移除认证机制(de-certification)并非可分离的性能优化,而是一次**结构性替换**:认证承载的安全性/活性不变量被重新分配至协议其他组件。uncertified 相对 certified 的提交延迟优势是**条件性的**——仅当承接这些不变量的替代机制在目标网络/敌手模型下边际成本低于认证时方成立。更进一步:certified/uncertified 只是浅层标签,真正的深层设计轴是 **availability-enforcement 机制 + reconciliation trigger 条件**。

## 章节大纲、字数分配与论证-证据映射

### 第 1 章 引言(~2200 字)
- 1.1 问题背景:DAG-based BFT 的崛起与"延迟焦虑"
- 1.2 一个被默认的判断:uncertified DAG"免费"降低延迟 —— 提出 SubRQ0(比较公平性/混淆变量)
- 1.3 本文论点与三层贡献(A benchmark 批判 / B fundamentality 批判 / C 轴批判)
- 1.4 研究问题:主 RQ + SubRQ1–3
- 1.5 misuse 声明(条件化结论易被断章)+ 论文结构
- 关键论证:CER 链 1 —— Claim「现有比较系统性偏向 happy path」/ Evidence [33][43][49] 报告的 benchmark 设定 / Reasoning 高维性能函数低维投影
- 证据:[22][31][32][33][43][57]

### 第 2 章 背景与相关工作(~3000 字)
- 2.1 BFT 共识谱系:从 PBFT 的 leader-based 到异步 BFT([10][11][12][16][17][18][20])
- 2.2 DAG-based BFT 的核心思想:数据传播与排序解耦([31][32][33])
- 2.3 certified DAG 谱系:DAG-Rider → Narwhal/Tusk → Bullshark → Aleph/GradedDAG/Sailfish/BBCA-Chain/Shoal([31]–[41])
- 2.4 uncertified DAG 的转向:Cordial Miners、Mysticeti、Mahi-Mahi([42][43][44])
- 2.5 研究空白:现有工作"提出协议+报 benchmark",缺少对 certified/uncertified 之分本身的批判性分析([57][58])
- 证据:[1]–[5][10]–[18][31]–[46][57][58][59][60]

### 第 3 章 方法论:不变量分解与受控比较框架(~2400 字)
- 3.1 SubRQ0 再阐述:为何"两个异质系统硬比"会混淆变量
- 3.2 模块化分解:以安全性/活性不变量为模块硬边界(去主观化)
- 3.3 受控 minimal-pair 比较:相同协议背景下仅改变认证强度
- 3.4 三分判据 C1-B(平移/削弱+补偿/消除)+ C1-C 成本-证明双判据
- 3.5 方法论自反性:minimal pair 可能不可构造 —— 本身即发现的前奏
- 关键论证:CER 链 2 —— Claim「认证不可被孤立移除」/ Evidence 真实 uncertified 协议均含补偿机制 [42][43][45] / Reasoning 结构性 vs 模块化
- 证据:[2][3][5][6][9][51][52]

### 第 4 章 SubRQ1 — 认证机制买到的三个不变量(~2400 字)
- 4.1 认证 = Reliable Broadcast:Bracha 两阶段结构([5][9])
- 4.2 不变量一:non-equivocation(非等价性)—— 一个 (author, round) 至多一个 certified block
- 4.3 不变量二:availability(数据可用性)—— certified block 的因果历史可被检索
- 4.4 不变量三:causal-history integrity(因果历史完整性)
- 4.5 认证在 certified DAG 中如何同时维持三者([31][32][34][39])
- 关键论证:CER 链 3 —— 三个不变量异质:逻辑型(规则可约束)vs 物理型(规则推不出)
- 证据:[5][6][31][32][34][39][51]

### 第 5 章 SubRQ2 — 去认证后的保证迁移与隐性代价(~3400 字,核心章)
- 5.1 工作假设 H 与三分法检验程序
- 5.2 non-equivocation 的命运:落入 ①平移 —— equivocation 被允许发生但在 commit 规则中被中和([42][43][45])
- 5.3 causal-history integrity 的命运:落入 ①平移 —— 引用关系 + 提交过滤([42][43])
- 5.4 availability 的命运:落入 ②削弱+补偿 —— 弱化为"提交时可恢复"+ skip/重试补偿([43][44][47][48])
- 5.5 隐性代价台账:commit 规则复杂度↑、最坏情况延迟、故障恢复、安全性证明负担([45][36][41])
- 5.6 反例排除(F1/F2):无任何 uncertified 协议干净去认证而无补偿
- 关键论证:CER 链 4 —— 隐性代价集中于 availability(物理型不变量)
- 证据:[36][41][42][43][44][45][46][47][48]

### 第 6 章 F4 — 非等价性的必要性论证(~2400 字)
- 6.1 命题:在纯异步模型(n=3f+1, Byzantine)下,DAG-BFT 安全性必要地依赖非等价性的某种 enforcement
- 6.2 证明思路:敌手构造 —— 若无 enforcement,构造 equivocation 攻击击穿 agreement([2][5])
- 6.3 部分同步推广讨论:M3 的诚实边界标注
- 6.4 安全网 C2-M4:限定到通用 DAG-BFT 模板的保守边界声明
- 6.5 推论:非等价性不可被"消除",只能被"重新 enforcement" —— 支撑结构性替换
- 关键论证:CER 链 5 —— 必要性 ⇒ 去认证必然是迁移而非消除
- 证据:[1][2][3][5][51][52]

### 第 7 章 SubRQ3 — 延迟优势的条件化结论(~2400 字)
- 7.1 成本台账方法:把 message-delay 与开销归因到各不变量 enforcement
- 7.2 happy-path:uncertified 优势成立(少 RBC 轮次)([42][43][44])
- 7.3 翻转条件一:recovery 频率升高 —— 补偿机制 amortized cost 反噬([45][49])
- 7.4 翻转条件二:partial-sync 退化与拥塞反馈([33][37][38][49])
- 7.5 翻转条件三:网络非对称 / workload skew([47])
- 7.6 条件化结论表:在 (敌手, 网络, 负载) 空间中标出优势成立/抵消/反转区域
- 关键论证:CER 链 6 —— "fundamental" 优势实为 conditional
- 证据:[33][37][38][39][43][44][45][47][49]

### 第 8 章 主贡献 C — availability-enforcement 作为深层设计轴(~1900 字)
- 8.1 从 SubRQ1–3 综合:决定行为的不是"是否认证",而是"availability 如何被 enforce"
- 8.2 深层轴的两个维度:enforcement 时机(引用前/提交前/提交后)+ reconciliation trigger 条件
- 8.3 用深层轴重新定位现有协议:certified/uncertified 是该轴上的两个投影点([31][32][33][42][43][44])
- 8.4 深层轴的解释力:它能解释 certified/uncertified 二分解释不了的现象(如 Adelie 的中间设计 [45])
- 关键论证:CER 链 7 —— 轴批判;naming 工程而非 theory 工程
- 证据:[6][42][43][44][45][46][47][48][56]

### 第 9 章 局限、misuse 声明与威胁有效性(~1000 字)
- 9.1 范围限定:语料库 C 明确界定,不主张普适性
- 9.2 F4 的模型边界:异步严格、部分同步为讨论
- 9.3 framing 失败风险:深层轴需读者"接住"
- 9.4 misuse:条件化结论的断章风险与 C 的结构性抗断章
- 证据:[53][54][55][56][57]

### 第 10 章 结论与未来工作(~900 字)
- 10.1 回答主 RQ 与三个 SubRQ
- 10.2 对协议设计者与 benchmark 设计者的启示
- 10.3 未来工作:深层轴的形式化、跨协议实证

## 论证链总览(7 条 CER 链)
1. 现有比较系统性偏向 happy path(benchmark 批判,A)
2. 认证不可被孤立移除(结构性 vs 模块化)
3. 三个不变量异质(逻辑型 vs 物理型)
4. 隐性代价集中于 availability
5. 非等价性必要 ⇒ 去认证是迁移非消除(F4)
6. happy-path 优势是 conditional 非 fundamental(B)
7. availability-enforcement 是深层轴,certified/uncertified 是投影(C,主贡献)

## 反方观点与处理(counter-arguments)
- 反方1:"uncertified 协议确实更快,benchmark 不会骗人" → 第7章条件化结论 + 第1章高维投影论证
- 反方2:"结构性替换是同义反复" → 第3章 C1-B/C1-C 预先讲定判据
- 反方3:"F4 只是异步结论,不适用真实部分同步部署" → 第6章 M3 诚实标注 + M4 兜底
- 反方4:"availability 在 uncertified 里没变弱,只是换了实现" → 第5.4 节用 C1-C 证其落入②而非①

## 字数总计
正文 ~21000 字(目标 20000±10%);双语摘要另计;参考文献 62 篇。
