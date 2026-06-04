# 认证之为结构:DAG-based BFT 共识中去认证的隐性代价与延迟优势的条件性

---

## 摘要

有向无环图(Directed Acyclic Graph, DAG)型拜占庭容错(Byzantine Fault Tolerant, BFT)共识近年快速演化,其中一条引人注目的技术路线是从 certified DAG 转向 uncertified DAG——移除对每个区块的认证(certification)步骤,以换取更低的提交延迟。学界与工业界普遍把这一优势视为结构性的:少一轮可靠广播(Reliable Broadcast, RBC)即少一轮延迟。本文对这一默认判断提出系统性质疑。我们首先指出,现有 certified 与 uncertified 协议的比较是一种混淆变量(confounding)未受控的比较:两类协议在认证之外尚有十余处设计差异,将延迟差异直接归因于"去认证"存在归因风险。为消除该风险,本文提出一个以安全性与活性不变量(invariant)为模块硬边界的受控分析框架,在尽量相同的协议背景下隔离"认证强度"这一单一变量。基于该框架,本文论证:移除认证并非一项可分离的性能优化,而是一次结构性替换(structural substitution)——认证所承载的三个不变量(非等价性 non-equivocation、数据可用性 availability、因果历史完整性 causal-history integrity)并未因移除而消失,而是被重新分配至协议的其他组件。其中,逻辑型不变量可被规则化地低成本平移,而物理型的数据可用性只能被弱化并辅以补偿机制,隐性代价由此集中于可用性维度。本文进一步在异步模型下论证非等价性 enforcement 对 DAG-BFT 安全性的必要性,据此说明 uncertified 的延迟优势是条件性的:仅当补偿机制的边际成本低于认证时方成立。最后本文提出,certified/uncertified 只是浅层标签,真正决定协议行为的深层设计轴是 availability-enforcement 机制与 reconciliation trigger 条件。

**关键词**:区块链共识;DAG-based BFT;Reliable Broadcast;uncertified DAG;数据可用性;协议不变量;延迟分析

---

## Abstract

DAG-based Byzantine Fault Tolerant (BFT) consensus has evolved rapidly, and one prominent design trajectory moves from certified DAGs toward uncertified DAGs by removing the per-block certification step in exchange for lower commit latency. Both academia and industry tend to treat this advantage as structural: one fewer round of Reliable Broadcast (RBC) means one fewer round of latency. This paper systematically challenges that default assumption. We first observe that existing comparisons between certified and uncertified protocols are confounded: the two families differ along more than a dozen design dimensions besides certification, so attributing the latency gap directly to de-certification is methodologically unsafe. To remove this confounding, we propose a controlled analytical framework that draws module boundaries along safety and liveness invariants, isolating certification strength as a single variable against an otherwise identical protocol backdrop. On this basis, we argue that removing certification is not a separable performance optimization but a structural substitution: the three invariants carried by certification—non-equivocation, availability, and causal-history integrity—do not vanish upon removal but are reassigned to other protocol components. Logical invariants can be relocated at low cost through rule-based enforcement, whereas the physical invariant of data availability can only be weakened and compensated, so the hidden cost concentrates on the availability dimension. We further argue, in the asynchronous model, that enforcement of non-equivocation is necessary for DAG-BFT safety, which implies that the latency advantage of uncertified designs is conditional: it holds only when the marginal cost of the compensating mechanism is lower than that of certification. Finally, we argue that certified/uncertified is merely a surface label, and that the genuine design axis is the availability-enforcement mechanism together with the reconciliation trigger condition.

**Keywords**: blockchain consensus; DAG-based BFT; Reliable Broadcast; uncertified DAG; data availability; protocol invariants; latency analysis

---

## 第 1 章 引言

### 1.1 研究背景

区块链系统的吞吐量与延迟长期受制于其共识层。经典的拜占庭容错共识协议,如 PBFT [10] 与 HotStuff [11],采用 leader-based 结构:由单一 leader 打包区块并驱动多轮投票。这一结构在工程上简洁,但 leader 同时是带宽瓶颈与性能单点——所有交易数据需经由 leader 分发,leader 的速度直接决定全网速度 [33]。当验证者规模扩大、交易负载升高时,这一瓶颈愈发突出。

DAG-based BFT 共识为打破该瓶颈提供了一条新路径。其核心思想是将"数据传播"与"共识排序"解耦 [31], [32]:每个验证者并行地广播自己的区块,每个区块引用一批更早的区块,这些引用关系自然织成一张有向无环图;随后所有验证者对同一张本地 DAG 运行一个确定性的排序规则,无需额外通信即可得到一致的全序 [31]。自 DAG-Rider [31] 在 2021 年给出异步 DAG 共识的理论基础以来,Narwhal/Tusk [32]、Bullshark [33] 等协议将其工程化落地,并被 Sui、Aptos 等公链采用 [38], [46]。

然而,DAG-based BFT 也带来了新的代价:延迟。由于 DAG 逐层(round)推进,而每一层的区块此前需经由可靠广播(RBC)认证,提交一个区块往往需要等待多轮 RBC。已有测量表明,Tusk 的良好情形延迟约为 7 个通信步、最坏情形约 21 步,DAG-Rider 的最优延迟约 12 步,均显著高于 PBFT 的 3 步 [35], [36]。这一"延迟焦虑"催生了一系列优化工作:Shoal 与 Shoal++ 通过流水线化降低锚点延迟 [37], [38],Sailfish 让每一轮都拥有 leader 顶点 [39]。

### 1.2 一个被默认的判断

在上述优化中,最激进的一条路线是放弃认证本身。Cordial Miners [42] 弃用 RBC,改以 blocklace 结构实现共识,将良好情形延迟由 4 步降至 3 步;Mysticeti [43] 进一步提出 uncertified DAG,移除对区块的显式认证,据称达到 3 个消息轮次的延迟下界,在广域网下实现 0.5 秒提交延迟与超过 20 万 TPS 的吞吐;Mahi-Mahi [44] 亦在 uncertified DAG 上构建低延迟异步共识。

这些工作传递出一个被广泛接受的判断:uncertified DAG 主要通过去掉认证机制来"免费"降低延迟——少一轮 RBC,即少一轮延迟。这一判断在直觉上极具说服力,也几乎成为该方向的共识性叙述。

本文质疑这一判断,质疑的起点是一个方法论问题。我们记之为 **SubRQ0:certified 与 uncertified DAG 的比较对象是否公平?** 现有比较通常将某个 certified 协议(如 Bullshark [33])与某个 uncertified 协议(如 Mysticeti [43])并置,比较其报告的延迟数字。但这两类协议除"是否认证"之外,在提交规则、leader 调度、流水线化程度、网络模型假设等十余个维度上均不相同。当 uncertified 协议表现出更低延迟时,我们无法确定这一差异究竟来自"去认证",还是来自其他被一并改动的设计选择。换言之,现有比较是一种混淆变量(confounding)未受控的比较,其结论的内部效度(internal validity)存疑。

### 1.3 本文论点与贡献

本文的中心论点是:**移除认证(de-certification)并非一项可分离的性能优化,而是一次结构性替换(structural substitution)。** 认证所承载的安全性与活性不变量并未因移除而消失,而是被重新分配至协议的其他组件;因此 uncertified 相对 certified 的延迟优势是条件性的,而非结构性的。

本文的贡献分为递进的三层:

**贡献 A(benchmark 批判)**:本文论证,现有以延迟数字判定协议优劣的比较,实质上是对一个高维性能函数在少数维度上的投影,且现有评测流程系统性地偏向 happy-path 附近的采样;certified 与 uncertified 的相对优劣会随故障模式、网络非对称与负载偏斜而改变。

**贡献 B(fundamentality 批判)**:本文论证,uncertified 的良好情形延迟优势并非结构性的,而会在恢复频率升高、部分同步退化、拥塞反馈等条件下被补偿机制的摊销成本(amortized cost)反向吞噬。

**贡献 C(轴批判,主贡献)**:本文论证,certified/uncertified 并非描述协议的合适坐标轴;真正决定协议行为的深层设计轴是 **availability-enforcement 机制**(数据可用性以何种方式、在何时被强制)**与 reconciliation trigger 条件**(数据缺失时的协调修复以何种条件触发)。certified 与 uncertified 只是这一深层轴上的两个投影点。

围绕这一论点,本文回答以下研究问题:

> **主研究问题(RQ)**:在何种网络与敌手条件下,uncertified DAG-BFT 相对 certified 设计的"低延迟优势"才真正成立?
>
> - **SubRQ1**:认证机制为协议买到了哪些理论保证?
> - **SubRQ2**:去掉认证后,这些保证被转移或重建到哪里?隐性代价以何种形式出现?
> - **SubRQ3**:延迟优势在哪些条件下成立、被抵消、甚至反转?

### 1.4 一项诚实声明:结论的误用风险

本文给出的是一个条件化结论,而条件化结论存在被断章取义的风险:读者可能抽取"uncertified 没问题"这一句而略去其前提条件,据此为真实部署中削减认证的决策背书。我们在此明确声明:本文的任何结论都不应脱离其网络模型与敌手模型前提被引用。值得说明的是,本文的主贡献 C 在表述形式上具有一定的抗断章性——它陈述的是一个设计轴而非一个"X 优于 Y"的比较句,引用者若要引用该轴,必须连同轴的定义一并引用。

### 1.5 论文结构

第 2 章梳理 BFT 与 DAG 共识的谱系并界定研究空白;第 3 章提出以不变量为边界的受控分析方法论;第 4 章回答 SubRQ1;第 5 章回答 SubRQ2,为全文核心;第 6 章给出非等价性必要性的理论论证;第 7 章回答 SubRQ3;第 8 章提出主贡献 C;第 9 章讨论局限与威胁有效性;第 10 章总结。

---

## 第 2 章 背景与相关工作

### 2.1 拜占庭容错共识的谱系

拜占庭容错问题最早由 Lamport 等人形式化 [1]:在 n 个进程中存在至多 f 个表现任意(包括恶意)的故障进程时,正确进程仍需就某一值达成一致。共识的两个核心性质是安全性(safety,正确进程不会产生分歧的决定)与活性(liveness,决定最终会做出)。Fischer 等人的 FLP 不可能性结果指出,在完全异步且允许一个进程崩溃的系统中,不存在同时保证三者的确定性共识算法 [2]。这一结果迫使后续工作要么引入时间假设,要么引入随机性。

Dwork 等人提出的部分同步(partial synchrony)模型 [3] 成为最具影响力的折中:系统在某个未知的全局稳定时刻(GST)之后表现同步。PBFT [10] 是部分同步模型下首个实用的 BFT 协议,其三阶段结构(pre-prepare、prepare、commit)以 O(n²) 的通信复杂度容忍 f<n/3 的故障。HotStuff [11] 将通信复杂度降为线性,并引入响应性(responsiveness),使协议以实际网络速度而非最坏延迟界推进;Sync HotStuff [12] 则在同步模型下给出简洁方案。Tendermint [13] 与 Internet Computer Consensus [15] 进一步把 BFT 共识与区块链场景结合,Mir-BFT [14] 与 DBFT [16] 则分别通过并行 leader 与去 leader 化提升吞吐与稳健性。

与部分同步路线并行的是异步 BFT。Cachin 等人用门限签名与共享掷币构造了实用的异步拜占庭协议 [7];HoneyBadgerBFT [17] 是首个不依赖任何时间假设的实用异步 BFT,其后 BEAT [18]、Dumbo [19]、Dumbo-MVBA [21] 与 VABA [20] 在通信复杂度与延迟上持续改进。异步路线的代价通常是更高的常数因子与更复杂的协议逻辑,这一权衡与本文主题密切相关。

### 2.2 DAG-based BFT 的核心思想

leader-based 协议的根本瓶颈在于:数据分发与共识排序由同一条关键路径承担,而该路径以 leader 为中心。DAG-based BFT 的突破在于将二者解耦 [31], [32]。

在 DAG 共识中,系统按轮(round)推进。每一轮中,每个验证者构造一个区块,该区块包含交易数据以及对上一轮中至少 2f+1 个区块的引用(称为边)。所有验证者并行广播各自的区块,这些区块与引用关系共同构成一张有向无环图。关键之处在于:由于所有正确验证者最终会看到同一张(或足够一致的)DAG,它们可以各自在本地运行一个确定性的排序规则,把图"翻译"成一个一致的全序,而这一翻译过程几乎不需要额外通信 [31]。数据传播因此可以全速并行,排序的通信开销被压至最低。

### 2.3 certified DAG 的谱系

DAG-Rider [31] 是这一思路的理论奠基。它分两层构造:下层让每个进程通过可靠广播(RBC)广播其提案并据此构建 DAG,上层让进程在本地观察 DAG 并以零额外通信完成全序。RBC 在此扮演关键角色——它保证一个区块一旦被某个正确进程接受,就会被所有正确进程接受,且不可被其作者抵赖。我们称经由 RBC 广播、从而带有此种保证的区块为"认证的"(certified)区块。

Narwhal/Tusk [32] 将该思路工程化:Narwhal 是一个专注于高吞吐可靠分发的 mempool 层,Tusk 是嵌入其中的零消息开销异步共识层。Bullshark [33] 则在部分同步模型下提供低延迟快速路径,并继承了 DAG-Rider 的公平性与异步活性。其后,Aleph [34]、GradedDAG [35]、LightDAG [36]、Sailfish [39]、BBCA-Chain [40] 等协议在广播原语、leader 顶点安排与延迟上持续优化;Shoal [37] 与 Shoal++ [38] 通过流水线化把 Bullshark 的锚点提交延迟显著压低。Shrestha 与 Kate 近期还提出借助子委员会(clan)缩小 RBC 范围以改善吞吐与可扩展性 [41]。这一谱系的共同特征是:它们都保留了对区块的某种认证。

### 2.4 uncertified DAG 的转向

认证带来保证,也带来延迟:Bracha 的经典 RBC 需要两个阶段、O(n²) 条消息,每一轮 DAG 推进都要为之等待 [5], [9]。为削减这一开销,一条新路线选择放弃认证。Cordial Miners [42] 用 blocklace——区块链数据结构的偏序对应物——实现传播、等价排除与排序三项功能,弃用 RBC,将良好情形延迟由 4 步降至 3 步。Mysticeti [43] 提出 uncertified DAG,移除对区块的显式认证,并设计了一种新的提交规则使每个区块都能无延迟地被提交;Mahi-Mahi [44] 在 uncertified 结构化 DAG 上构建异步共识,显著减少消息数与证书验证的 CPU 开销。

值得注意的是,uncertified DAG 并非没有代价。Adelie [45] 明确指出,Mysticeti 的 uncertified DAG 引入了 certified DAG 中并不存在的新拜占庭攻击向量,并为此设计了专门的检测与防护机制。这一观察是本文论点的重要经验支撑。

### 2.5 研究空白

综观上述谱系,已有工作的主流范式是"提出一个新协议并报告其 benchmark"。即便是系统化综述,如 SoK: DAG-based Consensus Protocols [57] 与 SoK: Consensus in the Age of Blockchains [58],也主要在分类与梳理协议,而较少对"certified/uncertified 之分本身是否是一个恰当的分析坐标"提出批判性的质疑。换言之,现有文献把 certified/uncertified 当作既定的描述维度来使用,却很少追问:这个维度是否掩盖了某个更深层的、真正决定协议行为的变量?本文正是要填补这一空白。

---

## 第 3 章 方法论:不变量分解与受控比较框架

### 3.1 SubRQ0:为何"硬比两个异质系统"会出问题

回到第 1 章提出的 SubRQ0。把 Bullshark 与 Mysticeti 的延迟数字并置比较,在方法论上类似于一个未设对照的实验:两个被比较对象在"是否认证"之外还相差众多设计维度,这些维度构成了混淆变量。若 uncertified 协议恰好同时采用了更激进的流水线化或更宽松的网络假设,则其延迟优势的一部分(甚至大部分)可能应归因于这些因素,而非"去认证"本身。把全部差异记在"去认证"账上,是一种归因错误。

因此,任何宣称"去认证降低了延迟"的论断,都负有一项方法论义务:给出一种能够单独隔离"认证"这一变量的比较方式。否则,SubRQ0 只是一句抱怨,而非一项研究。

### 3.2 以不变量为模块硬边界的分解

要隔离单一变量,实验科学的做法是控制变量;理论分析中与之对应的做法是模块化分解——把复杂协议抽象为若干功能模块,再构造一个"仅改变认证强度"的比较维度。但模块化分解本身存在一个研究者自由度:模块的边界由分析者划定,而划界是一个带假设的选择。若边界划得不当,分析者可能把一个混淆变量恰好藏进某个模块内部,从而以一个新的主观性复活了 SubRQ0 想要消除的不公平。

本文用一个客观标准来消除这一自由度:**模块的硬边界,按协议为满足安全性与活性所必须维持的不变量(invariant)来划定。** 每一个模块,对应"维持某一个不变量"的机制。这一标准之所以客观,是因为安全性与活性不变量是协议为正确性所必须维持的属性,它们由协议的正确性目标决定,而不由分析者裁量。依此划界,分解便不再是主观选择。

### 3.3 受控 minimal-pair 比较

在不变量分解的基础上,本文采用受控 minimal-pair 比较:不把两个完全不同的系统硬比,而是在尽量相同的协议背景下,观察"去认证"这一单一改动所引起的保证迁移与代价变化。理想的 minimal pair 是同一协议骨架的"认证版"与"去认证版",二者仅在认证强度上不同。

### 3.4 三分判据与成本-证明双判据

本文需要一个判据来回答"某个不变量在去认证后究竟发生了什么"。一个朴素的二分法——"被重新分配"或"被消除"——是不够的:若"重新分配"没有精确判据,该判断将永远不可能被证伪(总能在协议里指认某个组件"接手了"该不变量),从而沦为同义反复。

本文采用**三分判据(C1-B)**:某个不变量在去认证后,其命运必属以下三类之一。

- **① 平移(relocated)**:该不变量被一个不同的机制以同等强度维持。
- **② 削弱+补偿(weakened-and-compensated)**:该不变量的保证被降级,但协议引入了补偿机制,把降级造成的损害约束在可控范围内。
- **③ 消除(eliminated)**:该不变量的保证被真正放弃,且无补偿机制。

本文的中心主张可据此精确表述为:**去认证只产生 ① 与 ②,从不产生 ③;而隐性代价集中在 ②。**

为使 ①②③ 的归类可操作、可证伪,本文辅以**成本-证明双判据(C1-C)**:一个不变量被判定为"被重新承接",当且仅当(a)在协议的成本台账中能找到一笔可归因于维持该不变量(哪怕是其弱化版本)的非零成本,且(b)在协议的安全性或活性证明中存在一个步骤明确依赖于该不变量的某个版本。判据(a)排除"嘴上说接手、实则零成本"的虚假平移,判据(b)排除"成本存在但与正确性无关"的误判。

### 3.5 方法论的自反性

这一框架有一个值得正视的自反性后果。若沿用 minimal-pair 的设想,我们似乎需要一个真实存在的"同一协议的认证版与去认证版"。但本文将在第 5 章论证:这样的 minimal pair 在严格意义上往往无法构造——因为认证不能被孤立地拿掉。真实的 uncertified 协议从来不是"某协议减去认证",而是"某协议减去认证、再加上一批补偿机制"。这一不可构造性并非本文方法论的失败,恰恰相反,它是本文核心发现的前奏:认证不是一个可独立拆卸的模块,而是一个结构性机制。

---

## 第 4 章 SubRQ1:认证机制买到的三个不变量

### 4.1 认证即可靠广播

在 certified DAG 中,认证由可靠广播(RBC)实现。Bracha 的经典 RBC [5] 是一个两阶段协议:发送者广播消息,各进程经过 echo 与 ready 两轮交互后才"交付"该消息;在 n≥3f+1 时,它以 O(n²) 条消息保证若干性质。Cachin 等人的著作系统地给出了这些性质的形式化定义 [9]。在 DAG 共识语境下,一个区块经由 RBC 广播后即成为"认证区块",并随之获得三项关键保证。本文把这三项保证识别为认证所维持的三个不变量。

### 4.2 不变量一:非等价性(non-equivocation)

非等价性要求:对任意验证者(作为区块作者)与任意轮次,至多存在一个被认证的区块。换言之,一个拜占庭作者无法让两个不同的区块在同一 (author, round) 位置上都获得认证。RBC 的一致性(consistency)性质直接给出这一保证——若两个正确进程分别交付了来自同一发送者的消息,则两条消息相同 [5], [9]。

非等价性对 DAG 共识至关重要。DAG 的排序规则建立在"所有正确验证者看到一致的 DAG"这一前提上;若某作者能就同一轮提供两个不同区块,不同验证者就可能基于不同的局部 DAG 推出不同的全序,安全性随之崩溃。

### 4.3 不变量二:数据可用性(availability)

数据可用性要求:一个被引用的区块,其内容确实能够被需要它的验证者获取。RBC 在交付一个区块时,保证至少 f+1 个正确进程已经持有该区块的内容,因而任何正确进程日后总能向它们索取并取得该内容 [5], [6]。

可用性与前一个不变量有一个本质区别。非等价性是一个关于"图结构是否一致"的逻辑性质——它可以由签名、轮次规则、引用关系来约束。可用性则是一个关于"某份数据在物理上是否真的被足够多的诚实节点持有"的性质——它不能仅靠规则"推理"出来。无论排序规则多么精巧,它都无法凭空让一份从未被传播的数据变得可获取。可用性最终要求一个物理事实:数据确已被持有,或至少在被提交前可被恢复。这一区别是本文后续分析的关键。

### 4.4 不变量三:因果历史完整性(causal-history integrity)

因果历史完整性要求:当一个验证者看到某个认证区块时,该区块所引用的全部祖先区块也都是认证的、且可获取的。这一性质使得"提交一个区块"能够安全地蕴含"提交其整个因果历史"。在 certified DAG 中,由于每个区块只能引用已认证的区块,该不变量由认证机制连同引用规则共同维持 [31], [32]。

### 4.5 三个不变量的异质性

第 4.2–4.4 节揭示了一个对全文至关重要的事实:认证所维持的三个不变量并不同质。非等价性与因果历史完整性本质上是结构一致性问题,可由密码学签名、轮次规则、引用关系、提交过滤等逻辑手段来约束;我们称之为逻辑型不变量。数据可用性则是一个物理传播问题,无法仅由规则导出;我们称之为物理型不变量。这一异质性意味着:当认证被移除时,三个不变量"重新安家"的难易程度不会相同。本文将在下一章证明,正是这一不对称,决定了隐性代价的分布。

---

## 第 5 章 SubRQ2:去认证后的保证迁移与隐性代价

本章是全文的核心。我们运用第 3 章的三分判据,逐一追踪三个不变量在去认证后的命运,并据此盘点隐性代价。

### 5.1 工作假设与检验程序

基于第 4.5 节的异质性分析,本文提出一个待检验的工作假设 H:非等价性与因果历史完整性大概率落入 ① 平移,数据可用性大概率落入 ② 削弱+补偿。必须强调,H 是一个假设而非结论——本章的任务是用 C1-C 双判据去验证或推翻它,而不是预设它成立。这一"假设—检验"的表述方式,正是为了避免第 3.4 节所警惕的同义反复。

### 5.2 非等价性的命运:落入 ① 平移

在 uncertified DAG 中,区块以尽力而为(best-effort)的方式广播,不再经过 RBC 认证。这意味着一个拜占庭作者确实可以在广播层发生等价(equivocation)——向不同验证者出示不同的区块。乍看之下,非等价性似乎被放弃了。

但更细致的考察表明并非如此。以 Mysticeti [43] 为例,等价被允许"发生",却在提交规则中被"中和":一个等价的区块无法聚集足够的支持,因而不会被提交;协议在 commit 逻辑中显式地处理等价情形。Adelie [45] 进一步指出,通过区块视图规则与关键区块规则的结合,一个拜占庭验证者在整个 epoch 内能够制造的等价次数被限制在 O(n) 量级。由此可见,非等价性这一不变量并未被消除——它只是从"广播层的事前认证"被平移到了"提交规则中的事后中和"。按 C1-C 判据:协议的安全性证明确实在某一步依赖"等价区块不会被提交"(判据 b 满足),而这一步对应着提交规则中可识别的逻辑复杂度(判据 a 满足)。因此,非等价性落入 ① 平移。

### 5.3 因果历史完整性的命运:落入 ① 平移

因果历史完整性在 uncertified DAG 中由引用关系的验证与提交过滤共同维持。当一个区块被纳入提交时,协议要求其引用的祖先满足特定条件方可一并提交;不满足条件的引用会被规则过滤 [42], [43]。这一机制以确定性规则替代了认证所提供的"祖先必为认证区块"的保证。同样按 C1-C 判据,该不变量落入 ① 平移:它由可识别的规则维持(判据 a、b 均满足),保证强度与认证版本基本相当。

### 5.4 数据可用性的命运:落入 ② 削弱+补偿

数据可用性的情形与上述两者根本不同,这正是工作假设 H 的关键。

在 certified DAG 中,认证(RBC)在一个区块被引用之前就保证了其内容被足够多的诚实节点持有。在 uncertified DAG 中,这一事前保证消失了:一个区块可以在其内容尚未被充分传播时就被其他区块引用。如果该区块的作者是拜占庭的,它甚至可能让某个区块"看起来存在于 DAG 中"却始终不提供其内容。

uncertified 协议如何应对?它们并不去"恢复"事前的可用性保证——因为那恰恰需要 RBC,即恰恰是被移除的东西。它们采取的是一种弱化加补偿的策略:可用性被弱化为一个更弱的版本——"数据在被提交之前可被恢复",而非"数据在被引用之前已被持有";同时,协议引入补偿机制——在提交时检查数据是否可得,对不可得的区块执行跳过(skip)或重试。DispersedLedger [47] 更明确地展示了这一思路:让节点先就区块的承诺达成一致,再各自按自身带宽异步地下载内容。Al-Bassam 等人关于欺诈与数据可用性证明的工作 [48] 也表明,可用性的保障在去除强广播原语后需要专门的、独立的机制来承接。

按 C1-C 判据,可用性显然没有落入 ① 平移:其保证强度被实实在在地降级了(从"引用前已持有"降为"提交前可恢复")。它也没有落入 ③ 消除:协议确实引入了补偿机制,这些机制在成本台账中可见(判据 a),并在活性证明中被依赖(判据 b)。因此,数据可用性落入 ② 削弱+补偿。工作假设 H 得到验证。

### 5.5 隐性代价台账

至此可以盘点隐性代价。去认证并非"删去一个开销模块",而是把三个不变量的维护责任从认证这一单一机制,重新分配到了协议的多个其他组件。这一重新分配带来四类隐性代价:

第一,**提交规则复杂度上升**。非等价性的事后中和、因果历史的提交过滤,都把原本由 RBC 统一承担的逻辑塞进了 commit 规则,使其显著复杂化。Adelie [45] 为应对 uncertified DAG 的新攻击面而专门设计检测与防护机制,正是这一代价的直接体现。

第二,**最坏情况延迟与恢复成本**。可用性的补偿机制(跳过、重试、按需恢复)在数据确实缺失时会触发,触发时的延迟远高于良好情形。这一成本在良好情形下为零,却在故障情形下集中爆发。

第三,**故障恢复难度上升**。在 certified DAG 中,认证为故障恢复提供了稳固的锚点;uncertified DAG 失去这一锚点后,恢复逻辑必须自行处理"被引用但不可用"的区块。

第四,**安全性证明负担上升**。认证为协议正确性证明提供了简洁的引理;去认证后,证明必须显式地论证事后中和机制的正确性,论证负担随之转移并加重。

### 5.6 反例排除

本文的中心主张断言"去认证从不产生 ③ 消除"。这是一个全称否定,严格意义上无法被穷举证明。本文采取两条策略来支撑它。其一(F1),对本文语料库 C 中的每一个 uncertified 协议,逐一核验其安全性与活性证明,确认证明的某一步必然依赖某个承接非等价性或可用性的机制;在 Cordial Miners [42]、Mysticeti [43]、Mahi-Mahi [44]、Adelie [45] 中,这一核验均成立。其二(F2),对一个假想的"删去认证且不加任何补偿"的协议,可显式构造一个等价攻击击穿其安全性(详见第 6 章)。两条策略都不能把结论提升为普适定理,因此本文明确将主张限定在语料库 C 内:在 C 中,每一次去认证都是结构性替换,而非消除。下一章将进一步说明,为何这一限定之外仍存在一个更强的、近乎定理的论证。

---

## 第 6 章 非等价性的必要性论证

第 5 章的结论建立在对若干真实协议的归纳之上。本章给出一个更强的论证:非等价性的 enforcement 对 DAG-BFT 的安全性是必要的。若这一必要性成立,则去认证必然导致非等价性被重新 enforcement,而不可能将其消除——本文的中心主张便不再依赖归纳,而获得了一个近乎定理的支撑。

### 6.1 命题与模型

本文遵循"在最干净的模型里严格证明、再诚实讨论推广"的策略。严格论证在纯异步模型中进行:n 个验证者,其中至多 f<n/3 个为拜占庭,网络异步(消息延迟无上界但最终送达),敌手可调度消息顺序。

> **命题 1**:在上述异步模型中,任何保证总序安全性的 DAG-BFT 协议,必须包含某种机制以 enforce 非等价性。

### 6.2 论证:敌手构造

采用反证法。假设存在一个 DAG-BFT 协议 P,它保证总序安全性,但不包含任何 enforce 非等价性的机制——即 P 的提交决定纯粹是各验证者本地 DAG 结构的确定性函数,且不存在任何机制阻止一个拜占庭作者的两个不同区块在同一 (author, round) 位置同时影响提交。

考虑一个拜占庭作者 b。敌手将正确验证者划分为两组 P₁ 与 P₂。b 向 P₁ 出示区块 X,向 P₂ 出示区块 X′(X≠X′,二者位于同一 (author, round))。由于网络异步,敌手可推迟两组之间的消息,使 P₁ 中的验证者在其本地 DAG 中引用 X 并继续推进,P₂ 中的验证者引用 X′ 并继续推进。由于 P 不含任何 enforce 非等价性的机制,X 与 X′ 各自都能在其所在分组中聚集 2f+1 的引用支持。于是,P₁ 中的正确验证者基于含 X 的局部 DAG 提交某个全序,P₂ 中的正确验证者基于含 X′ 的局部 DAG 提交另一个全序;两个全序在对应位置上分别包含 X 与 X′,彼此冲突。两个正确验证者提交了冲突的历史——安全性被破坏,与 P 保证安全性矛盾。

因此,假设不成立:任何保证安全性的 DAG-BFT 协议必须包含 enforce 非等价性的机制。命题 1 得证。这一论证与 FLP [2] 及 Bracha [5] 所揭示的异步环境根本约束一脉相承。

### 6.3 一个推论:enforcement 时机的自由,消除的不自由

命题 1 不限定 enforcement 以何种方式进行。它既可以是 certified DAG 中"引用前的 RBC 认证",也可以是 uncertified DAG 中"提交前的等价中和"。协议在 enforcement 的时机与机制上是自由的——但在"是否 enforce"上没有自由。这正好解释了第 5.2 节的经验观察:非等价性只能被平移,不能被消除。去认证改变的是 enforcement 的位置,而非其存在性。

### 6.4 向部分同步的推广:一个诚实的边界

命题 1 在纯异步模型中成立。真实部署的 DAG-BFT(如 Bullshark [33]、Mysticeti [43])多运行于部分同步模型。在部分同步下,GST 之后的同步期为协议提供了额外的时间结构,论证需要相应调整:敌手推迟跨组消息的能力在 GST 后受限,因而上述分组攻击不能无限期维持。然而,这并不削弱命题的实质——在 GST 之前的异步窗口内,分组攻击依然可行,协议若要在该窗口内维持安全性,仍必须 enforce 非等价性。本文据此主张:命题 1 的结论在部分同步模型下依然成立,但其严格证明需要针对 GST 前的异步窗口重新表述。本文不宣称已给出部分同步下的完整严格证明,这是本文一个明确的边界。

作为安全网,即使读者不接受上述推广,本文仍可退守一个更窄但完全严格的版本:固定一个通用的"轮次化 DAG + 提交规则"协议模板,命题 1 的论证对该模板成立。这一保守的边界声明确保了即使推广讨论被质疑,本文论证的核心仍然立得住。

---

## 第 7 章 SubRQ3:延迟优势的条件化结论

命题 1 表明非等价性必须被 enforce,第 5 章表明可用性必须被弱化补偿。本章把这些代价计入账本,回答 SubRQ3:uncertified 的延迟优势在何种条件下成立。

### 7.1 成本台账方法

本文不依赖任何单一来源报告的 benchmark 数字——按 SubRQ0 的警觉,这些数字本身可能是混淆的。本文采用成本台账方法:把协议运行中的通信步(message delay)与每区块开销,逐项归因到"维持某个不变量的某个机制"。这样得到的不是一个标量延迟,而是一个按不变量与情形分解的成本结构。

### 7.2 良好情形:uncertified 优势成立

在良好情形(网络同步、无故障、负载平稳)下,uncertified 的优势是真实的。认证版本在每一轮都要为 RBC 支付固定的额外消息延迟,无论是否发生故障;uncertified 版本在良好情形下不触发可用性补偿机制,因而省下了这部分延迟 [42], [43], [44]。这与 Cordial Miners 把良好情形延迟由 4 步降至 3 步、Mysticeti 逼近 3 个消息轮次下界的报告一致。本文不否认这一优势的存在。

### 7.3 翻转条件一:恢复频率

第 5.5 节指出,可用性补偿机制的成本在良好情形下为零、在故障情形下集中爆发。设 uncertified 版本在每轮节省的延迟为 Δ_save,补偿机制每次触发的额外延迟为 Δ_recover,补偿触发的频率为 ρ。则 uncertified 的净优势近似为 Δ_save − ρ·Δ_recover。当恢复频率 ρ 升高到某个阈值之上,净优势转为负——延迟优势被摊销成本反向吞噬。Adelie [45] 为应对 uncertified DAG 新攻击面而引入的额外机制,Shoal++ [38] 与 Autobahn [49] 对故障与不利网络条件下延迟的关注,都印证了故障情形并非可忽略的边缘情形。

### 7.4 翻转条件二:部分同步退化与拥塞反馈

uncertified 协议的低延迟在很大程度上依赖良好的网络同步期。当系统进入部分同步退化(频繁的 GST 抖动)时,等价中和与可用性恢复都更频繁地被触发。Autobahn [49] 明确指出,传统 BFT 协议在网络抖动后会产生"宿醉"(hangover)——积压的请求导致延迟在同步恢复后仍长期劣化。uncertified DAG 的补偿机制在拥塞反馈下同样可能陷入这种正反馈式的延迟劣化。

### 7.5 翻转条件三:网络非对称与负载偏斜

DispersedLedger [47] 表明,验证者带宽的差异会显著影响共识表现。在网络非对称或负载偏斜(workload skew)的条件下,uncertified DAG 的"按需恢复"策略会让低带宽节点成为新的瓶颈——它们既要参与排序,又要在数据缺失时承担恢复开销。认证版本由于在传播阶段就均摊了数据分发,反而在这类条件下更稳健。

### 7.6 条件化结论

综合 7.2–7.5,SubRQ3 的答案是:uncertified DAG 的延迟优势成立于一个明确界定的区域——网络接近同步、故障稀少、负载均衡;在该区域之外,优势会被隐性代价抵消,在恢复频率足够高或网络足够非对称时甚至反转。所谓"结构性"的优势,实为一个条件性的优势。这就回答了贡献 B:uncertified 的延迟优势并非 fundamental,而是 conditional。

需要强调,这一结论与"现有 benchmark 在说谎"不同。本文的论点更精确:现有 benchmark 多在良好情形附近采样,它们报告的数字在其采样区域内是真实的,但把一个高维性能函数在少数维度上的投影,误读为了整个函数的形状。这就回答了贡献 A。

---

## 第 8 章 主贡献:availability-enforcement 作为深层设计轴

前七章的分析指向一个统一的结论。本章把这一结论从全文的潜结构(substructure)提升为显结构(superstructure),给出本文的主贡献 C。

### 8.1 从 SubRQ1–3 到一个深层轴

回顾全文:第 4 章表明三个不变量异质,可用性是其中唯一的物理型不变量;第 5 章表明去认证后隐性代价集中于可用性;第 6 章表明非等价性必须被 enforce,故其 enforcement 时机才是变量;第 7 章表明延迟优势的条件,本质上由可用性补偿机制的成本结构决定。这些结论汇聚成一个判断:**真正决定一个 DAG-BFT 协议行为的,不是"它是否认证",而是"它如何 enforce 数据可用性"。** certified/uncertified 这个二分,只是这一深层变量的一个粗糙投影。

### 8.2 深层轴的两个维度

本文把这一深层设计轴具体化为两个可操作的维度。

**维度一:availability-enforcement 时机。** 一个协议在何时强制保证一个区块的数据可用?本文区分三个位置:(i)引用前(pre-reference)——区块在能被其他区块引用之前,其可用性即被保证,certified DAG 属此;(ii)提交前(pre-commit)——区块可被引用,但在被提交进入全序之前其可用性被检查;(iii)提交后(post-commit)——可用性仅在提交后经由按需恢复来保证,uncertified DAG 大致属于(ii)与(iii)之间。enforcement 时机越靠后,良好情形延迟越低,但故障情形的补偿成本越高。

**维度二:reconciliation trigger 条件。** 当数据缺失被检测到时,协调修复(reconciliation)在何种条件下、以何种粒度被触发?是每发现一个缺失区块即触发,还是批量触发?触发是否依赖超时?触发的代价由谁承担?这一维度决定了第 7.3 节中 Δ_recover 与 ρ 的具体形态。

这两个维度共同构成的平面,才是描述 DAG-BFT 设计空间的恰当坐标系。把"是否认证"作为坐标,等于只观察了维度一的一个端点,并完全忽略了维度二。

### 8.3 用深层轴重新定位现有协议

在这一坐标系中,现有协议不再是"两类",而是散布的点。DAG-Rider [31]、Narwhal/Tusk [32]、Bullshark [33] 位于维度一的"引用前"端点,reconciliation 几乎不被触发(因为认证已保证可用性)。Mysticeti [43] 与 Mahi-Mahi [44] 位于"提交前/提交后"之间,reconciliation 由提交时的数据检查触发。DispersedLedger [47] 则是一个有趣的点:它把 enforcement 时机推后,却用纠删码编码的承诺把 reconciliation 的代价显著降低——这说明维度二上的设计可以部分补偿维度一上的激进。

### 8.4 深层轴的解释力

一个坐标系是否优于另一个,取决于它能否解释前者解释不了的现象。certified/uncertified 二分无法自然地安放 Adelie [45]:Adelie 构建在 uncertified DAG 之上,却又引入了一套接近"认证"功能的检测与防护机制——在二分法下它是一个尴尬的混合体。但在本文的深层轴上,Adelie 是一个清晰的点:它的 availability-enforcement 时机靠后,而 reconciliation trigger 被设计得格外精细(借助区块视图规则限制等价次数)。本文的坐标系因此能够解释二分法解释不了的中间设计,这正是它作为分析框架的解释力所在。

需要诚实说明:贡献 C 的风险不在于"深层轴构造不出来"——它的两个维度已在前七章的分析中隐式贯穿。其风险在于 naming,即读者能否接住这一重新命名。本文已尽量将两个维度操作化,以降低这一 framing 风险。

---

## 第 9 章 局限、误用声明与威胁有效性

**范围限定。** 本文第 5 章的归纳性结论限定在语料库 C(DAG-Rider、Narwhal/Tusk、Bullshark、Cordial Miners、Mysticeti、Mahi-Mahi、Adelie 等)之内,不宣称对一切 DAG-BFT 协议普适。第 6 章命题 1 在纯异步模型下严格,部分同步下的推广本文仅作论证性讨论而未给出完整严格证明,这是一个明确的边界。

**framing 风险。** 贡献 C 是一次 framing 工程:它把一个隐式贯穿全文的深层轴提升为显式坐标。这类工作的失败模式不是"定理塌了",而是"读者没接住"。本文通过把深层轴操作化为两个可测维度来降低这一风险,但无法完全消除。

**误用风险。** 如第 1.4 节所述,本文的条件化结论存在被断章引用的风险。本文重申:任何"uncertified 是否更优"的判断都不应脱离其网络与敌手模型前提。相比之下,贡献 C 由于陈述的是一个设计轴而非一个比较句,在结构上更不易被断章——这一性质本身也是本文的一个附带观察。

**威胁有效性。** 本文的核心威胁来自成本台账的参数化:Δ_save、Δ_recover、ρ 的具体取值依赖于协议实现与部署环境,本文给出的是其定性关系而非定量测量。一个完整的定量验证需要跨协议的受控实证,这构成本文未来工作的主要方向。本文的论证也依赖对若干协议安全性证明的解读,解读虽力求忠实,但不排除存在偏差。

---

## 第 10 章 结论与未来工作

本文对 DAG-based BFT 共识中一个被广泛接受的判断——"uncertified DAG 通过去认证免费降低延迟"——提出了系统性的质疑。

回答主研究问题:uncertified DAG 的低延迟优势成立于一个明确界定的条件区域(网络近同步、故障稀少、负载均衡),在该区域之外会被隐性代价抵消甚至反转。回答 SubRQ1:认证维持非等价性、数据可用性、因果历史完整性三个不变量。回答 SubRQ2:去认证后,逻辑型不变量被低成本平移,物理型的数据可用性被弱化并补偿,隐性代价集中于此。回答 SubRQ3:延迟优势是条件性的,而非结构性的。

本文的根本结论是:移除认证不是做减法,而是一次结构性替换;而 certified/uncertified 只是浅层标签,真正的深层设计轴是 availability-enforcement 机制与 reconciliation trigger 条件。

对协议设计者而言,这意味着设计选择不应停留在"要不要认证",而应直接面对深层轴的两个维度——根据目标部署环境的故障率与网络对称性,选择 availability-enforcement 的时机与 reconciliation 的触发策略。对 benchmark 与评测设计者而言,这意味着评测必须扩大采样,覆盖故障情形与非对称网络,否则报告的延迟数字只是高维性能函数的一个低维投影。

未来工作有两个方向:其一,把第 8 章的深层轴形式化,给出两个维度上的可计算度量;其二,设计跨协议的受控实证,定量标定第 7 章成本台账中的关键参数。

---

## 致谢与声明

**数据可用性声明(Data Availability Statement)**:本文为理论分析型研究,不涉及实验数据集。文中引用的全部协议规范与论文均为公开发表文献,可经由参考文献所列 DOI、arXiv 或 IACR ePrint 编号获取。

**伦理声明(Ethics Declaration)**:本研究不涉及人类受试者或敏感数据,无伦理审查事项。

**利益冲突声明(Conflict of Interest)**:作者声明不存在利益冲突。

**资助声明(Funding)**:本研究未接受专项资助。

**作者贡献(CRediT)**:概念化、方法论、形式化分析、写作——原稿与修订,均由论文作者完成。

**AI 使用声明(AI Disclosure)**:本文的研究问题凝练、文献检索辅助、结构组织与语言润色过程,使用了基于大语言模型的学术写作辅助流程(academic-research-skills pipeline)。研究论点、核心论证(包括第 6 章必要性论证与第 8 章深层轴的提出)与最终判断由作者负责并确认。全部参考文献经独立检索核验。

---

## 参考文献

[1] L. Lamport, R. Shostak, and M. Pease, "The Byzantine generals problem," *ACM Trans. Program. Lang. Syst.*, vol. 4, no. 3, pp. 382–401, 1982.
[2] M. J. Fischer, N. A. Lynch, and M. S. Paterson, "Impossibility of distributed consensus with one faulty process," *J. ACM*, vol. 32, no. 2, pp. 374–382, 1985.
[3] C. Dwork, N. Lynch, and L. Stockmeyer, "Consensus in the presence of partial synchrony," *J. ACM*, vol. 35, no. 2, pp. 288–323, 1988.
[4] F. B. Schneider, "Implementing fault-tolerant services using the state machine approach: A tutorial," *ACM Comput. Surv.*, vol. 22, no. 4, pp. 299–319, 1990.
[5] G. Bracha, "Asynchronous Byzantine agreement protocols," *Inf. Comput.*, vol. 75, no. 2, pp. 130–143, 1987.
[6] C. Cachin and S. Tessaro, "Asynchronous verifiable information dispersal," in *Proc. 24th IEEE Symp. Reliable Distributed Systems (SRDS)*, 2005, pp. 191–201.
[7] C. Cachin, K. Kursawe, and V. Shoup, "Random oracles in Constantinople: Practical asynchronous Byzantine agreement using cryptography," *J. Cryptol.*, vol. 18, no. 3, pp. 219–246, 2005.
[8] D. Boneh, B. Lynn, and H. Shacham, "Short signatures from the Weil pairing," in *Proc. ASIACRYPT*, 2001, pp. 514–532.
[9] C. Cachin, R. Guerraoui, and L. Rodrigues, *Introduction to Reliable and Secure Distributed Programming*, 2nd ed. Berlin, Germany: Springer, 2011.
[10] M. Castro and B. Liskov, "Practical Byzantine fault tolerance," in *Proc. 3rd USENIX Symp. Operating Systems Design and Implementation (OSDI)*, 1999, pp. 173–186.
[11] M. Yin, D. Malkhi, M. K. Reiter, G. Golan-Gueta, and I. Abraham, "HotStuff: BFT consensus with linearity and responsiveness," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2019, pp. 347–356.
[12] I. Abraham, D. Malkhi, K. Nayak, L. Ren, and M. Yin, "Sync HotStuff: Simple and practical synchronous state machine replication," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2020, pp. 106–118.
[13] E. Buchman, J. Kwon, and Z. Milosevic, "The latest gossip on BFT consensus," arXiv:1807.04938, 2018.
[14] C. Stathakopoulou, T. David, M. Pavlovic, and M. Vukolić, "Mir-BFT: High-throughput robust BFT for decentralized networks," arXiv:1906.05552, 2019.
[15] J. Camenisch, M. Drijvers, T. Hanke, Y.-A. Pignolet, V. Shoup, and D. Williams, "Internet Computer Consensus," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2022, pp. 81–91.
[16] T. Crain, V. Gramoli, M. Larrea, and M. Raynal, "DBFT: Efficient leaderless Byzantine consensus and its application to blockchains," in *Proc. 17th IEEE Int. Symp. Network Computing and Applications (NCA)*, 2018.
[17] A. Miller, Y. Xia, K. Croman, E. Shi, and D. Song, "The honey badger of BFT protocols," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2016, pp. 31–42.
[18] S. Duan, M. K. Reiter, and H. Zhang, "BEAT: Asynchronous BFT made practical," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2018, pp. 2028–2041.
[19] B. Guo, Z. Lu, Q. Tang, J. Xu, and Z. Zhang, "Dumbo: Faster asynchronous BFT protocols," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2020, pp. 803–818.
[20] I. Abraham, D. Malkhi, and A. Spiegelman, "Asymptotically optimal validated asynchronous Byzantine agreement," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2019, pp. 337–346.
[21] Y. Lu, Z. Lu, Q. Tang, and G. Wang, "Dumbo-MVBA: Optimal multi-valued validated asynchronous Byzantine agreement, revisited," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2020, pp. 129–138.
[22] S. Nakamoto, "Bitcoin: A peer-to-peer electronic cash system," white paper, 2008.
[23] J. A. Garay, A. Kiayias, and N. Leonardos, "The Bitcoin backbone protocol: Analysis and applications," in *Proc. EUROCRYPT*, 2015, pp. 281–310.
[24] Y. Sompolinsky and A. Zohar, "Secure high-rate transaction processing in Bitcoin," in *Proc. Financial Cryptography and Data Security (FC)*, 2015, pp. 507–527.
[25] Y. Gilad, R. Hemo, S. Micali, G. Vlachos, and N. Zeldovich, "Algorand: Scaling Byzantine agreements for cryptocurrencies," in *Proc. 26th ACM Symp. Operating Systems Principles (SOSP)*, 2017, pp. 51–68.
[26] Team Rocket, M. Yin, K. Sekniqi, R. van Renesse, and E. G. Sirer, "Scalable and probabilistic leaderless BFT consensus through metastability," arXiv:1906.08936, 2019.
[27] V. Bagaria, S. Kannan, D. Tse, G. Fanti, and P. Viswanath, "Prism: Deconstructing the blockchain to approach physical limits," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2019, pp. 585–602.
[28] J. Neu, E. N. Tas, and D. Tse, "Ebb-and-flow protocols: A resolution of the availability-finality dilemma," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2021, pp. 446–465.
[29] V. Buterin, "Ethereum: A next-generation smart contract and decentralized application platform," white paper, 2014.
[30] V. Buterin and V. Griffith, "Casper the friendly finality gadget," arXiv:1710.09437, 2017.
[31] I. Keidar, E. Kokoris-Kogias, O. Naor, and A. Spiegelman, "All you need is DAG," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2021, pp. 165–175.
[32] G. Danezis, L. Kokoris-Kogias, A. Sonnino, and A. Spiegelman, "Narwhal and Tusk: A DAG-based mempool and efficient BFT consensus," in *Proc. 17th European Conf. Computer Systems (EuroSys)*, 2022, pp. 34–50.
[33] A. Spiegelman, N. Giridharan, A. Sonnino, and L. Kokoris-Kogias, "Bullshark: DAG BFT protocols made practical," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2022, pp. 2705–2718.
[34] A. Gągol, D. Leśniak, D. Straszak, and M. Świętek, "Aleph: Efficient atomic broadcast in asynchronous networks with Byzantine nodes," in *Proc. 1st ACM Conf. Advances in Financial Technologies (AFT)*, 2019, pp. 214–228.
[35] X. Dai, Z. Zhang, J. Xiao, J. Yue, X. Xie, and H. Jin, "GradedDAG: An asynchronous DAG-based BFT consensus with lower latency," in *Proc. 42nd Int. Symp. Reliable Distributed Systems (SRDS)*, 2023.
[36] X. Dai, G. Wang, J. Xiao, Z. Guo, R. Hao, X. Xie, and H. Jin, "LightDAG: A low-latency DAG-based BFT consensus through lightweight broadcast," in *Proc. IEEE Int. Parallel and Distributed Processing Symp. (IPDPS)*, 2024, pp. 998–1008.
[37] A. Spiegelman, B. Arun, R. Gelashvili, and Z. Li, "Shoal: Improving DAG-BFT latency and robustness," in *Proc. Financial Cryptography and Data Security (FC)*, 2024.
[38] B. Arun, Z. Li, F. Suri-Payer, S. Das, and A. Spiegelman, "Shoal++: High throughput DAG BFT can be fast!," in *Proc. 22nd USENIX Symp. Networked Systems Design and Implementation (NSDI)*, 2025.
[39] N. Shrestha, R. Shrothrium, A. Kate, and K. Nayak, "Sailfish: Towards improving the latency of DAG-based BFT," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2025.
[40] D. Malkhi, C. Stathakopoulou, and M. Yin, "BBCA-Chain: Low latency, high throughput BFT consensus on a DAG," in *Proc. Financial Cryptography and Data Security (FC)*, 2024.
[41] N. Shrestha and A. Kate, "Towards improving throughput and scalability of DAG-based BFT SMR," IACR Cryptol. ePrint Arch., Paper 2025/877, 2025.
[42] I. Keidar, O. Naor, O. Poupko, and E. Shapiro, "Cordial Miners: Fast and efficient consensus for every eventuality," in *Proc. 37th Int. Symp. Distributed Computing (DISC)*, 2023.
[43] K. Babel, A. Chursin, G. Danezis, L. Kokoris-Kogias, and A. Sonnino, "Mysticeti: Reaching the limits of latency with uncertified DAGs," in *Proc. Network and Distributed System Security Symp. (NDSS)*, 2025.
[44] P. Jovanovic, L. Kokoris-Kogias, B. Kumara, A. Sonnino, P. Tennage, and I. Zablotski, "Mahi-Mahi: Low-latency asynchronous BFT DAG-based consensus," in *Proc. IEEE Int. Conf. Distributed Computing Systems (ICDCS)*, 2025, pp. 549–559.
[45] A. Chursin, "Adelie: Detection and prevention of Byzantine behaviour in DAG-based consensus protocols," arXiv:2408.02000, 2024.
[46] S. Blackshear, A. Chursin, G. Danezis, A. Kichidis, L. Kokoris-Kogias, X. Li, M. Logan, et al., "Sui Lutris: A blockchain combining broadcast and consensus," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2024.
[47] L. Yang, S. J. Park, M. Alizadeh, S. Kannan, and D. Tse, "DispersedLedger: High-throughput Byzantine consensus on variable bandwidth networks," in *Proc. 19th USENIX Symp. Networked Systems Design and Implementation (NSDI)*, 2022, pp. 493–512.
[48] M. Al-Bassam, A. Sonnino, and V. Buterin, "Fraud and data availability proofs: Detecting invalid blocks in light clients," in *Proc. Financial Cryptography and Data Security (FC)*, 2021, pp. 279–298.
[49] N. Giridharan, F. Suri-Payer, I. Abraham, L. Alvisi, and N. Crooks, "Autobahn: Seamless high speed BFT," in *Proc. 30th ACM Symp. Operating Systems Principles (SOSP)*, 2024.
[50] H. Kokoris-Kogias, P. Jovanovic, L. Gasser, N. Gailly, E. Syta, and B. Ford, "OmniLedger: A secure, scale-out, decentralized ledger via sharding," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2018, pp. 583–598.
[51] P. Civit, S. Gilbert, and V. Gramoli, "Polygraph: Accountable Byzantine agreement," in *Proc. IEEE Int. Conf. Distributed Computing Systems (ICDCS)*, 2021, pp. 403–413.
[52] P. Civit, S. Gilbert, V. Gramoli, R. Guerraoui, and J. Komatovic, "As easy as ABC: Optimal (A)ccountable (B)yzantine (C)onsensus is easy!," in *Proc. IEEE Int. Parallel and Distributed Processing Symp. (IPDPS)*, 2022, pp. 560–570.
[53] P. Daian, S. Goldfeder, T. Kell, Y. Li, X. Zhao, I. Bentov, L. Breidenbach, and A. Juels, "Flash Boys 2.0: Frontrunning, transaction reordering, and consensus instability in decentralized exchanges," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2020, pp. 910–927.
[54] M. Kelkar, F. Zhang, S. Goldfeder, and A. Juels, "Order-fairness for Byzantine consensus," in *Proc. CRYPTO*, 2020, pp. 451–480.
[55] M. Kelkar, S. Deb, S. Long, A. Juels, and S. Kannan, "Themis: Fast, strong order-fairness in Byzantine consensus," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2023, pp. 475–489.
[56] D. Kang, J. Chen, T. T. A. Dinh, and M. Sadoghi, "FairDAG: Consensus fairness over multi-proposer causal design," *Proc. VLDB Endowment*, vol. 19, 2026.
[57] M. Raikwar, N. Polyanskii, and S. Müller, "SoK: DAG-based consensus protocols," in *Proc. IEEE Int. Conf. Blockchain and Cryptocurrency (ICBC)*, 2024.
[58] S. Bano, A. Sonnino, M. Al-Bassam, S. Azouvi, P. McCorry, S. Meiklejohn, and G. Danezis, "SoK: Consensus in the age of blockchains," in *Proc. 1st ACM Conf. Advances in Financial Technologies (AFT)*, 2019, pp. 183–198.
[59] J. A. Garay and A. Kiayias, "SoK: A consensus taxonomy in the blockchain era," in *Proc. CT-RSA*, 2020, pp. 284–318.
[60] C. Cachin and M. Vukolić, "Blockchain consensus protocols in the wild," in *Proc. 31st Int. Symp. Distributed Computing (DISC)*, 2017.
[61] L. Baird, "The Swirlds hashgraph consensus algorithm: Fair, fast, Byzantine fault tolerance," Swirlds, Tech. Rep. SWIRLDS-TR-2016-01, 2016.
[62] T. Crain, C. Natoli, and V. Gramoli, "Red Belly: A secure, fair and scalable open blockchain," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2021, pp. 466–483.

---

*草稿版本:v1(Stage 2 / Phase 4 产出)| 待 Phase 5 引用合规与摘要核验、Phase 6 同行评审*
