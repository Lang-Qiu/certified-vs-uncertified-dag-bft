# 认证之为结构:DAG-based BFT 共识中去认证的隐性代价与延迟优势的条件性

---

## 摘要

有向无环图(Directed Acyclic Graph, DAG)型拜占庭容错(Byzantine Fault Tolerant, BFT)共识近年快速演化,其中一条引人注目的技术路线是从 certified DAG 转向 uncertified DAG——移除对每个区块的认证(certification)步骤,以换取更低的提交延迟。学界与工业界普遍把这一优势视为结构性的:少一轮可靠广播(Reliable Broadcast, RBC)即少一轮延迟。本文对这一默认判断提出系统性质疑。我们首先指出,现有 certified 与 uncertified 协议的比较是一种混淆变量(confounding)未受控的比较:两类协议在认证之外尚有十余处设计差异,将延迟差异直接归因于"去认证"存在归因风险。为消除该风险,本文提出一个以安全性与活性不变量(invariant)为模块硬边界的受控分析框架,在尽量相同的协议背景下隔离"认证强度"这一单一变量。基于该框架,本文论证:移除认证并非一项可分离的性能优化,而是一次结构性替换(structural substitution)——认证所承载的三个不变量(非等价性 non-equivocation、数据可用性 availability、因果历史完整性 causal-history integrity)并未因移除而消失,而是被重新分配至协议的其他组件。其中一个可被提前预测的不对称是关键:逻辑型不变量系统性地被规则化低成本平移,而物理型的数据可用性只能被弱化并辅以补偿机制——隐性代价由此集中于可用性维度,且这一代价是一笔仅在故障情形爆发的或有负债(contingent liability),而非固定开销。本文进一步在异步模型下,针对一类安全性证明依赖"槽位唯一性"的 DAG-BFT 协议,论证非等价性 enforcement 的必要性,据此说明 uncertified 的延迟优势是条件性的:仅当补偿机制的边际成本低于认证时方成立。最后本文提出,certified/uncertified 只是浅层标签,真正决定协议行为的深层设计轴是 availability-enforcement 机制与 reconciliation trigger 条件。

**关键词**:区块链共识;DAG-based BFT;Reliable Broadcast;uncertified DAG;数据可用性;协议不变量;延迟分析

---

## Abstract

DAG-based Byzantine Fault Tolerant (BFT) consensus has evolved rapidly, and one prominent design trajectory moves from certified DAGs toward uncertified DAGs by removing the per-block certification step in exchange for lower commit latency. Both academia and industry tend to treat this advantage as structural: one fewer round of Reliable Broadcast (RBC) means one fewer round of latency. This paper systematically challenges that default assumption. We first observe that existing comparisons between certified and uncertified protocols are confounded: the two families differ along more than a dozen design dimensions besides certification, so attributing the latency gap directly to de-certification is methodologically unsafe. To remove this confounding, we propose a controlled analytical framework that draws module boundaries along safety and liveness invariants, isolating certification strength as a single variable against an otherwise identical protocol backdrop. On this basis, we argue that removing certification is not a separable performance optimization but a structural substitution: the three invariants carried by certification—non-equivocation, availability, and causal-history integrity—do not vanish upon removal but are reassigned to other protocol components. A predictable asymmetry is central here: logical invariants are systematically relocated at low cost through rule-based enforcement, whereas the physical invariant of data availability can only be weakened and compensated—so the hidden cost concentrates on the availability dimension, and it takes the form of a contingent liability that materializes only under faults rather than a fixed overhead. We further argue, in the asynchronous model, that for the class of DAG-BFT protocols whose safety proof relies on per-slot uniqueness, enforcement of non-equivocation is necessary, which implies that the latency advantage of uncertified designs is conditional: it holds only when the marginal cost of the compensating mechanism is lower than that of certification. Finally, we argue that certified/uncertified is merely a surface label, and that the genuine design axis is the availability-enforcement mechanism together with the reconciliation trigger condition.

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

第 2 章梳理区块链共识与 DAG 共识的谱系并界定研究空白;第 3 章提出以不变量为边界的受控分析方法论;第 4 章回答 SubRQ1;第 5 章回答 SubRQ2,为全文核心;第 6 章给出非等价性必要性的理论论证;第 7 章回答 SubRQ3;第 8 章提出主贡献 C 并讨论其对排序公平性的延伸;第 9 章讨论局限与威胁有效性;第 10 章总结。

---

## 第 2 章 背景与相关工作

### 2.1 区块链共识的两大谱系

区块链共识协议大致可分为两大谱系。第一条谱系源于 Nakamoto 的 Bitcoin 设计 [22],以工作量证明(Proof-of-Work)与最长链规则达成概率性一致。Garay 等人通过提取"Bitcoin 主干协议"并证明其公共前缀(common prefix)与链质量(chain quality)性质,为这一谱系奠定了形式化基础 [23];Sompolinsky 与 Zohar 的 GHOST 规则则改进了高交易率下的链选择 [24]。Nakamoto 谱系的特点是开放参与与概率性最终性,但其确认延迟以分钟乃至小时计。

第二条谱系源于经典分布式系统的状态机复制(State Machine Replication, SMR)。Schneider 的经典综述系统地阐述了 SMR 范式 [4]:只要所有正确副本以相同顺序执行相同的确定性操作,它们就能维持一致的状态。区块链的总序广播(total-order broadcast)本质上即 SMR 问题。这一谱系追求确定性最终性与秒级乃至亚秒级延迟,本文研究的 DAG-based BFT 即属于此。两条谱系并非完全隔离:Algorand 用可验证随机函数把委员会抽样引入 BFT 投票 [25],Avalanche 通过重复随机子采样达成亚稳态(metastable)共识 [26],而以太坊 [29] 的演进——从 Casper 的友好最终性小工具 [30] 到 ebb-and-flow 协议对"可用性-最终性两难"的解析 [28]——则展示了两条谱系的融合趋势。值得注意的是,"DAG"一词在两条谱系中含义不同:在 Nakamoto 谱系中它指 SPECTRE/PHANTOM 式的区块 DAG,在本文语境中它特指 BFT 共识的通信结构。

### 2.2 拜占庭容错共识的理论约束与经典协议

拜占庭容错问题最早由 Lamport 等人形式化 [1]:在 n 个进程中存在至多 f 个表现任意(包括恶意)的故障进程时,正确进程仍需就某一值达成一致。共识的两个核心性质是安全性(safety,正确进程不会产生分歧的决定)与活性(liveness,决定最终会做出)。Fischer 等人的 FLP 不可能性结果指出,在完全异步且允许一个进程崩溃的系统中,不存在同时保证三者的确定性共识算法 [2]。这一结果迫使后续工作要么引入时间假设,要么引入随机性。

Dwork 等人提出的部分同步(partial synchrony)模型 [3] 成为最具影响力的折中:系统在某个未知的全局稳定时刻(GST)之后表现同步。PBFT [10] 是部分同步模型下首个实用的 BFT 协议,其三阶段结构(pre-prepare、prepare、commit)以 O(n²) 的通信复杂度容忍 f<n/3 的故障。HotStuff [11] 将通信复杂度降为线性,并引入响应性(responsiveness),使协议以实际网络速度而非最坏延迟界推进;Sync HotStuff [12] 则在同步模型下给出简洁方案。Tendermint [13] 与 Internet Computer Consensus [15] 进一步把 BFT 共识与区块链场景结合,Mir-BFT [14] 通过并行 leader 提升吞吐,DBFT [16] 与 Red Belly [62] 则探索去 leader 化与开放式区块链的扩展。

与部分同步路线并行的是异步 BFT。Cachin 等人用门限签名与共享掷币构造了实用的异步拜占庭协议 [7];HoneyBadgerBFT [17] 是首个不依赖任何时间假设的实用异步 BFT,其后 BEAT [18]、Dumbo [19]、Dumbo-MVBA [21] 与 VABA [20] 在通信复杂度与延迟上持续改进。异步路线的代价通常是更高的常数因子与更复杂的协议逻辑,这一权衡与本文主题密切相关。此外,门限签名等密码学基元——如 Boneh 等人提出的可聚合 BLS 短签名 [8]——为这些协议提供了把 O(n) 个签名压缩为常数大小证书的能力,是认证机制工程实现的基础。

### 2.3 可扩展性的多条路径与解耦思想

提升共识可扩展性有多条路径。分片(sharding)是其中之一:OmniLedger [50] 把验证者划分为多个分片并行处理交易,以横向扩展吞吐。另一条路径是结构性解耦。Prism [27] 是这一思想的代表:它把区块链"解构"为提议、投票、交易处理三种功能区块,从而在保持 Bitcoin 安全性的同时把吞吐推向网络容量极限。Prism 的"解构"与 DAG-based BFT 的"数据传播与排序解耦"在思想上一脉相承——二者都认识到,把多种功能压在同一条关键路径上是性能瓶颈的根源。DAG-based BFT 可被理解为这一解耦思想在 BFT 共识中的彻底化。

### 2.4 DAG-based BFT 的核心思想

leader-based 协议的根本瓶颈在于:数据分发与共识排序由同一条关键路径承担,而该路径以 leader 为中心。DAG-based BFT 的突破在于将二者彻底解耦 [31], [32]。

在 DAG 共识中,系统按轮(round)推进。每一轮中,每个验证者构造一个区块,该区块包含交易数据以及对上一轮中至少 2f+1 个区块的引用(称为边)。所有验证者并行广播各自的区块,这些区块与引用关系共同构成一张有向无环图。关键之处在于:由于所有正确验证者最终会看到同一张(或足够一致的)DAG,它们可以各自在本地运行一个确定性的排序规则,把图"翻译"成一个一致的全序,而这一翻译过程几乎不需要额外通信 [31]。数据传播因此可以全速并行,排序的通信开销被压至最低。Hashgraph [61] 是这一思路的一个早期工业实例,它用"gossip about gossip"构造类似结构并以虚拟投票完成排序。

### 2.5 certified DAG 的谱系

DAG-Rider [31] 是这一思路的理论奠基。它分两层构造:下层让每个进程通过可靠广播(RBC)广播其提案并据此构建 DAG,上层让进程在本地观察 DAG 并以零额外通信完成全序。RBC 在此扮演关键角色——它保证一个区块一旦被某个正确进程接受,就会被所有正确进程接受,且不可被其作者抵赖。我们称经由 RBC 广播、从而带有此种保证的区块为"认证的"(certified)区块。

Narwhal/Tusk [32] 将该思路工程化:Narwhal 是一个专注于高吞吐可靠分发的 mempool 层,Tusk 是嵌入其中的零消息开销异步共识层。Bullshark [33] 则在部分同步模型下提供低延迟快速路径,并继承了 DAG-Rider 的公平性与异步活性。其后,Aleph [34]、GradedDAG [35]、LightDAG [36]、Sailfish [39]、BBCA-Chain [40] 等协议在广播原语、leader 顶点安排与延迟上持续优化;Shoal [37] 与 Shoal++ [38] 通过流水线化把 Bullshark 的锚点提交延迟显著压低。Shrestha 与 Kate 近期还提出借助子委员会(clan)缩小 RBC 范围以改善吞吐与可扩展性 [41]。这一谱系的共同特征是:它们都保留了对区块的某种认证。

### 2.6 uncertified DAG 的转向

认证带来保证,也带来延迟:Bracha 的经典 RBC 需要两个阶段、O(n²) 条消息,每一轮 DAG 推进都要为之等待 [5], [9]。为削减这一开销,一条新路线选择放弃认证。Cordial Miners [42] 用 blocklace——区块链数据结构的偏序对应物——实现传播、等价排除与排序三项功能,弃用 RBC,将良好情形延迟由 4 步降至 3 步。Mysticeti [43] 提出 uncertified DAG,移除对区块的显式认证,并设计了一种新的提交规则使每个区块都能无延迟地被提交;Mahi-Mahi [44] 在 uncertified 结构化 DAG 上构建异步共识,显著减少消息数与证书验证的 CPU 开销。

值得注意的是,uncertified DAG 并非没有代价。Adelie [45] 明确指出,Mysticeti 的 uncertified DAG 引入了 certified DAG 中并不存在的新拜占庭攻击向量,并为此设计了专门的检测与防护机制。这一观察是本文论点的重要经验支撑。须说明该证据的性质:Adelie 本身是一篇为该攻击面提出防护方案的论文,故"存在新攻击面"这一判断与其研究动机一致。为避免单一来源的循环论证,本文在第 5、7 章援引这一点时,会同时诉诸 Mysticeti [43] 自身在提交规则中对等价情形的显式处理作为独立佐证——一个协议若需在 commit 逻辑中专门处理等价,本身即说明该攻击面真实存在。

### 2.7 研究空白

综观上述谱系,已有工作的主流范式是"提出一个新协议并报告其 benchmark"。即便是系统化综述,如 SoK: DAG-based Consensus Protocols [57]、SoK: Consensus in the Age of Blockchains [58]、SoK: A Consensus Taxonomy in the Blockchain Era [59] 与 Cachin 与 Vukolić 对实际区块链共识协议的梳理 [60],也主要在分类与梳理协议,而尚无工作把 certified/uncertified 之分本身当作分析对象、追问它是否遮蔽了一个更恰当的坐标并加以重构(reframe)。须作一个区分:Mysticeti [43]、Adelie [45] 等单个协议工作确实讨论过认证的取舍,但它们讨论的是"在这条轴上如何取值",而非"这条轴本身是否是描述设计空间的恰当坐标"。换言之,现有文献把 certified/uncertified 当作既定的描述维度来使用,却很少追问:这个维度是否掩盖了某个更深层的、真正决定协议行为的变量?本文要填补的正是后一种 reframing 的空白。

---

## 第 3 章 方法论:不变量分解与受控比较框架

### 3.1 SubRQ0:为何"硬比两个异质系统"会出问题

回到第 1 章提出的 SubRQ0。把 Bullshark [33] 与 Mysticeti [43] 的延迟数字并置比较,在方法论上类似于一个未设对照的实验:两个被比较对象在"是否认证"之外还相差众多设计维度,这些维度构成了混淆变量。若 uncertified 协议恰好同时采用了更激进的流水线化或更宽松的网络假设,则其延迟优势的一部分(甚至大部分)可能应归因于这些因素,而非"去认证"本身。把全部差异记在"去认证"账上,是一种归因错误。

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

这里须对该主张的非平凡性作一个诚实的界定。"去认证从不产生 ③"本身并非一个令人惊讶的发现:任何能正常运行的协议都是安全且活的,其安全性/活性不变量按定义必被某种机制维持,因此 ③(无补偿的消除)对一个工作协议而言几乎必然不出现。换言之,①/② 二分本身更应被理解为本框架的**起点**,而非结论。本文真正非平凡、且并非同义反复的主张有两点:其一,**① 与 ② 的落点不是随机的,而可由第 4.5 节的逻辑型/物理型二分提前预测**——逻辑型不变量系统性地落入 ①,物理型的可用性系统性地落入 ②;这个"可预测的不对称"是一个有内容的经验论断,它本可以不成立(例如某个逻辑型不变量可能因协议结构而无法低成本平移)。其二,**落入 ② 的可用性,其补偿成本是一笔或有负债(contingent liability)而非固定开销**——它在良好情形为零、在故障情形集中爆发,这一成本结构正是第 7 章条件化结论的根源。后文的 ①②③ 归类服务于确立这两点,而非服务于"③ 不发生"这一近乎定义的陈述。

为使 ①②③ 的归类可操作、可证伪,本文辅以**成本-证明双判据(C1-C)**:一个不变量被判定为"被重新承接",当且仅当(a)在协议的成本台账中能找到一笔可归因于维持该不变量(哪怕是其弱化版本)的非零成本,且(b)在协议的安全性或活性证明中存在一个步骤明确依赖于该不变量的某个版本。判据(a)排除"嘴上说接手、实则零成本"的虚假平移,判据(b)排除"成本存在但与正确性无关"的误判。两个判据必须同时满足,缺一不可:仅满足(a)可能是与正确性无关的工程开销,仅满足(b)可能是一个未被实现却被证明默认的理想假设。

为便于对照,下表汇总两组判据:

| 判据 | 作用 | 内容 |
|------|------|------|
| C1-B 三分判据 | 刻画不变量去认证后的命运 | ① 平移(等强度、机制不同)/ ② 削弱+补偿(保证降级,补偿机制约束损害)/ ③ 消除(放弃且无补偿) |
| C1-C 判据(a)成本 | 排除"零成本的虚假平移" | 成本台账中存在一笔可归因于维持该不变量(含其弱化版本)的非零成本 |
| C1-C 判据(b)证明 | 排除"与正确性无关的开销" | 协议安全性/活性证明中存在一步明确依赖该不变量的某个版本 |

判定一个不变量"被重新承接",须 C1-C 的(a)(b)同时满足;再据其保证强度是否降级,归入 ① 或 ②。

### 3.5 方法论的自反性

这一框架有一个值得正视的自反性后果。若沿用 minimal-pair 的设想,我们似乎需要一个真实存在的"同一协议的认证版与去认证版"。但本文将在第 5 章论证:这样的 minimal pair 在严格意义上往往无法构造——因为认证不能被孤立地拿掉。真实的 uncertified 协议从来不是"某协议减去认证",而是"某协议减去认证、再加上一批补偿机制"。这一不可构造性并非本文方法论的失败,恰恰相反,它是本文核心发现的前奏:认证不是一个可独立拆卸的模块,而是一个结构性机制。换言之,方法论上的障碍本身,转化成了一项实质发现。

---

## 第 4 章 SubRQ1:认证机制买到的三个不变量

### 4.1 认证即可靠广播

在 certified DAG 中,认证由可靠广播(RBC)实现。Bracha 的经典 RBC [5] 是一个两阶段协议:发送者广播消息,各进程经过 echo 与 ready 两轮交互后才"交付"该消息;在 n≥3f+1 时,它以 O(n²) 条消息保证若干性质。Cachin 等人的著作系统地给出了这些性质的形式化定义 [9]:正确性(correctness)、一致性(consistency)、完整性(integrity)与终止性(totality)。在工程实现中,RBC 所产生的"认证"通常物化为一个由 2f+1 个验证者签名聚合而成的证书(certificate),BLS 聚合签名 [8] 使该证书的大小不随验证者数量增长。在 DAG 共识语境下,一个区块经由 RBC 广播后即成为"认证区块",并随之获得三项关键保证。本文把这三项保证识别为认证所维持的三个不变量。须说明这一识别的范围:本文聚焦的三个不变量——非等价性、数据可用性、因果历史完整性——分别对应 RBC 的一致性、终止性与完整性三条性质在 DAG 语境下的投影,它们是去认证分析中真正承载安全性/活性风险的维度。RBC 的标准性质集还包含一条 validity/correctness 性质(正确发送者广播的消息终将被正确进程交付);本文不把它单列为第四个不变量,因为在 DAG 语境下它表现为"正确作者的区块终被传播且可用",已被数据可用性不变量与广播活性共同涵盖,并不构成去认证所转移的额外安全性负担。因此本文不宣称三不变量是 RBC 性质的"完备分解",而只主张:它们覆盖了去认证分析所需的全部安全性/活性维度。

### 4.2 不变量一:非等价性(non-equivocation)

非等价性要求:对任意验证者(作为区块作者)与任意轮次,至多存在一个被认证的区块。换言之,一个拜占庭作者无法让两个不同的区块在同一 (author, round) 位置上都获得认证。RBC 的一致性(consistency)性质直接给出这一保证——若两个正确进程分别交付了来自同一发送者的消息,则两条消息相同 [5], [9]。

非等价性对 DAG 共识至关重要。DAG 的排序规则建立在"所有正确验证者看到一致的 DAG"这一前提上;若某作者能就同一轮提供两个不同区块,不同验证者就可能基于不同的局部 DAG 推出不同的全序,安全性随之崩溃。可以说,非等价性是把"局部 DAG"提升为"全局一致对象"的黏合剂。

### 4.3 不变量二:数据可用性(availability)

数据可用性要求:一个被引用的区块,其内容确实能够被需要它的验证者获取。RBC 在交付一个区块时,保证至少 f+1 个正确进程已经持有该区块的内容,因而任何正确进程日后总能向它们索取并取得该内容 [5], [6]。

可用性与前一个不变量有一个本质区别。非等价性是一个关于"图结构是否一致"的逻辑性质——它可以由签名、轮次规则、引用关系来约束。可用性则是一个关于"某份数据在物理上是否真的被足够多的诚实节点持有"的性质——它不能仅靠规则"推理"出来。无论排序规则多么精巧,它都无法凭空让一份从未被传播的数据变得可获取。可用性最终要求一个物理事实:数据确已被持有,或至少在被提交前可被恢复。Cachin 与 Tessaro 的异步可验证信息分散(AVID)正是为这一物理事实提供保障的专门机制——它用纠删码把数据切片分散存储,使数据可在部分节点缺席时被重构 [6]。这一区别是本文后续分析的关键。

### 4.4 不变量三:因果历史完整性(causal-history integrity)

因果历史完整性要求:当一个验证者看到某个认证区块时,该区块所引用的全部祖先区块在结构上都是良构的——即都是已认证的、且引用关系本身正确无环的区块。须特别说明本文对这一不变量的界定:它是一个**纯结构性质**,只关乎"祖先在 DAG 结构上是否良构",而**不包含**"祖先内容在物理上是否可被获取"这一要求——后者属于第 4.3 节的数据可用性不变量,本文将其严格剥离。作此剥离是必要的:若把"祖先可获取"并入因果历史完整性,该不变量就会同时含有逻辑成分与物理成分,第 4.5 节的逻辑型/物理型二分将不再干净。剥离之后,因果历史完整性是一个可仅凭本地结构检查验证的逻辑型性质。这一(结构)性质使得"提交一个区块"能够安全地蕴含"在结构上提交其整个因果历史"。在 certified DAG 中,由于每个区块只能引用已认证的区块,该不变量由认证机制连同引用规则共同维持 [31], [32]。因果历史完整性是 DAG 共识"零额外通信排序"得以成立的结构前提:正是因为提交一个锚点即在结构上蕴含提交其全部因果历史,排序才不需要为每个区块单独通信——而这些被蕴含的祖先其内容是否真的可得,则由数据可用性不变量单独负责。

### 4.5 三个不变量的异质性

第 4.2–4.4 节揭示了一个对全文至关重要的事实:认证所维持的三个不变量并不同质。非等价性与因果历史完整性本质上是结构一致性问题,可由密码学签名、轮次规则、引用关系、提交过滤等逻辑手段来约束;我们称之为逻辑型不变量。数据可用性则是一个物理传播问题,无法仅由规则导出;我们称之为物理型不变量。

这一逻辑型/物理型的二分可以用一个判准来刻画:一个不变量是逻辑型的,当且仅当它可以仅凭对协议消息的本地检查(签名验证、引用关系核对)被验证;它是物理型的,当且仅当它的验证最终依赖于"某份数据是否真实存在于某处"这一不可由本地检查推断的事实。按此判准,非等价性与因果历史完整性是逻辑型的,数据可用性是物理型的。这一异质性意味着:当认证被移除时,三个不变量"重新安家"的难易程度不会相同。本文将在下一章证明,正是这一不对称,决定了隐性代价的分布。

---

## 第 5 章 SubRQ2:去认证后的保证迁移与隐性代价

本章运用第 3 章的三分判据与 C1-C 双判据,逐一追踪三个不变量在去认证后的命运,并据此盘点隐性代价。

### 5.1 工作假设与检验程序

基于第 4.5 节的异质性分析,本文提出一个待检验的工作假设 H:非等价性与因果历史完整性大概率落入 ① 平移,数据可用性大概率落入 ② 削弱+补偿。必须强调,H 是一个假设而非结论——本章的任务是用 C1-C 双判据去验证或推翻它,而不是预设它成立。这一"假设—检验"的表述方式,正是为了避免第 3.4 节所警惕的同义反复。检验程序如下:对每个不变量,先在 uncertified 协议中定位承接它的机制(若存在),再用判据(a)核验该机制是否产生可归因成本,用判据(b)核验协议正确性证明是否依赖它,最后据保证强度是否降级判定其落入 ① 还是 ②。

### 5.2 非等价性的命运:落入 ① 平移

在 uncertified DAG 中,区块以尽力而为(best-effort)的方式广播,不再经过 RBC 认证。这意味着一个拜占庭作者确实可以在广播层发生等价(equivocation)——向不同验证者出示不同的区块。乍看之下,非等价性似乎被放弃了。

但更细致的考察表明并非如此。以 Mysticeti [43] 为例,等价被允许"发生",却在提交规则中被"中和":一个等价的区块无法聚集足够的支持,因而不会被提交;协议在 commit 逻辑中显式地处理等价情形。Adelie [45] 进一步指出,通过区块视图规则与关键区块规则的结合,一个拜占庭验证者在整个 epoch 内能够制造的等价次数被限制在 O(n) 量级。由此可见,非等价性这一不变量并未被消除——它只是从"广播层的事前认证"被平移到了"提交规则中的事后中和"。按 C1-C 判据:协议的安全性证明确实在某一步依赖"等价区块不会被提交"(判据 b 满足),而这一步对应着提交规则中可识别的逻辑复杂度(判据 a 满足)。作为判据(b)的一个具体落点(worked example):在 Mysticeti [43] 中,提交规则需要确保任意两个正确验证者不会把同一 (author, round) 槽位判定为"已提交"却对应不同区块——这一致性步骤正是其安全性论证所依赖的关键引理;而该引理之所以成立,依赖于提交规则的支持计数会使一个等价区块的两个分身都无法各自独立聚集到提交阈值。这一处即判据(b)所要求的、"证明中明确依赖该不变量某版本"的可指认步骤。因此,非等价性落入 ① 平移。

这一平移并非全无代价,但其代价是逻辑性的、可由规则界定的。等价的事后中和把原本由 RBC 统一承担的逻辑搬进了提交规则,使提交规则更复杂,却没有引入新的物理资源需求。这正是逻辑型不变量"易于重新安家"的体现。

### 5.3 因果历史完整性的命运:落入 ① 平移

因果历史完整性在 uncertified DAG 中由引用关系的验证与提交过滤共同维持。当一个区块被纳入提交时,协议要求其引用的祖先满足特定条件方可一并提交;不满足条件的引用会被规则过滤 [42], [43]。这一机制以确定性规则替代了认证所提供的"祖先必为认证区块"的保证。同样按 C1-C 判据,该不变量落入 ① 平移:它由可识别的规则维持(判据 a、b 均满足),保证强度与认证版本基本相当。须明确:依第 4.4 节的界定,这里平移的只是因果历史完整性的**结构成分**(祖先良构、引用正确);祖先内容"是否可得"不在此不变量之内,而由下一节的数据可用性单独追踪。正因如此,因果历史完整性的低成本 ① 平移并未"偷渡"任何物理可用性的代价——物理代价被完整地留给了 §5.4。

值得注意的是,因果历史完整性的平移与非等价性的平移共享同一个特征:二者都把保证从"广播层"搬到了"提交层",而提交层本就是 DAG 共识需要逻辑处理的地方。逻辑型不变量之所以可低成本平移,根本原因在于它们的"新家"——提交规则——已经存在,平移只是往里面增添逻辑,而不需要新建一个机制。

### 5.4 数据可用性的命运:落入 ② 削弱+补偿

数据可用性的情形与上述两者根本不同,这正是工作假设 H 的关键。

在 certified DAG 中,认证(RBC)在一个区块被引用之前就保证了其内容被足够多的诚实节点持有。在 uncertified DAG 中,这一事前保证消失了:一个区块可以在其内容尚未被充分传播时就被其他区块引用。如果该区块的作者是拜占庭的,它甚至可能让某个区块"看起来存在于 DAG 中"却始终不提供其内容。

uncertified 协议如何应对?它们并不去"恢复"事前的可用性保证——因为那恰恰需要 RBC,即恰恰是被移除的东西。它们采取的是一种弱化加补偿的策略:可用性被弱化为一个更弱的版本——"数据在被提交之前可被恢复",而非"数据在被引用之前已被持有";同时,协议引入补偿机制——在提交时检查数据是否可得,对不可得的区块执行跳过(skip)或重试。DispersedLedger [47] 更明确地展示了这一思路:让节点先就区块的承诺达成一致,再各自按自身带宽异步地下载内容;Al-Bassam 等人关于欺诈与数据可用性证明的工作 [48] 也表明,可用性的保障在去除强广播原语后需要专门的、独立的机制(纠删码加抽样)来承接。

按 C1-C 判据,可用性显然没有落入 ① 平移:其保证强度被实实在在地降级了(从"引用前已持有"降为"提交前可恢复")。它也没有落入 ③ 消除:协议确实引入了补偿机制,这些机制在成本台账中可见(判据 a),并在活性证明中被依赖(判据 b)。因此,数据可用性落入 ② 削弱+补偿。工作假设 H 得到验证。

这一结论的深层原因,正是第 4.5 节的逻辑型/物理型二分。可用性是物理型的:它的"新家"不像提交规则那样现成存在——要真正保证数据被持有,必须有节点真实地存储与传输数据,这是一个无法由规则凭空创造的物理资源。uncertified 协议无法为可用性提供一个零成本的逻辑新家,只能弱化它,再用补偿机制兜底。

### 5.5 一个具体的对照:认证区块与未认证区块的提交路径

为使上述分析更具体,考虑同一个区块 b 在两类协议中被提交的路径。在 certified DAG 中,b 先经 RBC 获得证书,此时其内容已被 f+1 个正确节点持有;此后任何引用 b 的区块都可安全地假定 b 可用,提交 b 时无需任何额外的可用性检查。在 uncertified DAG 中,b 被直接广播并可立即被引用;当某个锚点的提交牵连到 b 时,协议必须在此刻确认 b 的内容可得——若不可得,则触发恢复或将 b 标记为不可提交。同一个区块,在前者中可用性的代价在传播阶段被预先、均匀地支付;在后者中,这笔代价被推迟到提交阶段,并且只在需要时支付。这一对照清楚地显示:去认证并未消除可用性的代价,只是改变了它被支付的时机与条件——而"按需支付"在数据确实缺失时会变得昂贵。

### 5.6 隐性代价台账

至此可以盘点隐性代价。去认证并非"删去一个开销模块",而是把三个不变量的维护责任从认证这一单一机制,重新分配到了协议的多个其他组件。这一重新分配带来四类隐性代价:

第一,**提交规则复杂度上升**。非等价性的事后中和、因果历史的提交过滤,都把原本由 RBC 统一承担的逻辑塞进了 commit 规则,使其显著复杂化。Adelie [45] 为应对 uncertified DAG 的新攻击面而专门设计检测与防护机制,正是这一代价的直接体现。

第二,**最坏情况延迟与恢复成本**。可用性的补偿机制(跳过、重试、按需恢复)在数据确实缺失时会触发,触发时的延迟远高于良好情形。这一成本在良好情形下为零,却在故障情形下集中爆发——它是一笔"或有负债"。

第三,**故障恢复难度上升**。在 certified DAG 中,认证为故障恢复提供了稳固的锚点;uncertified DAG 失去这一锚点后,恢复逻辑必须自行处理"被引用但不可用"的区块,恢复路径的状态空间随之扩大。

第四,**安全性证明负担上升**。认证为协议正确性证明提供了简洁的引理;去认证后,证明必须显式地论证事后中和机制的正确性,论证负担随之转移并加重。这一点虽不直接影响运行时性能,却影响协议的可验证性与可信度。

### 5.7 反例排除

本文的中心主张断言"去认证从不产生 ③ 消除"。这是一个全称否定,严格意义上无法被穷举证明。本文采取两条策略来支撑它。其一(F1),对本文语料库 C 中的每一个 uncertified 协议,逐一核验其安全性与活性证明,确认证明的某一步必然依赖某个承接非等价性或可用性的机制;在 Cordial Miners [42]、Mysticeti [43]、Mahi-Mahi [44]、Adelie [45] 中,这一核验均成立。其二(F2),对一个假想的"删去认证且不加任何补偿"的协议,可显式构造一个等价攻击击穿其安全性(详见第 6 章)。两条策略都不能把结论提升为普适定理,因此本文明确将主张限定在语料库 C 内:在 C 中,每一次去认证都是结构性替换,而非消除。下一章将针对其中的非等价性这一维度,给出一个不依赖逐协议归纳的、范围明确界定的补充论证——它不把整体主张"提升为定理",但为其最易被质疑的一环提供一个比归纳更硬的支点。

---

## 第 6 章 非等价性的必要性论证

第 5 章的结论建立在对语料库 C 中若干真实协议的归纳之上。本章针对其中的非等价性维度,补充一个不依赖逐协议归纳的论证。须先界定本论证的范围与作用:它**只覆盖三个不变量中的非等价性这一个**,而非等价性恰是第 5 章判定为"低成本平移"的那一个;因此本章并不把中心主张整体"提升为定理",它做的是一件更有限也更扎实的事——为中心主张最容易被质疑的一环("去认证之后,非等价性是否真的还**必须**存在")提供一个比归纳更硬的支点。

### 6.1 模型、引理与命题

本文遵循"在范围明确的模型里严格论证、再诚实讨论推广"的策略。论证在纯异步模型中进行:n≥3f+1 个验证者,其中至多 f 个为拜占庭,网络异步(消息延迟无上界但最终送达),敌手可调度消息顺序。协议以轮次化 DAG 为通信结构,每个验证者的提交决定是其本地 DAG 的确定性函数;提交一个区块/锚点需要后续轮次中达到法定人数(quorum,规模 n−f,在最优容错 n=3f+1 时即 2f+1)的引用支持——这一 quorum 设定涵盖语料库 C 中的全部协议。

本章论证的对象不是"所有可设想的 DAG-BFT 协议",而是一类**安全性证明依赖槽位唯一性引理**的协议。所谓**槽位唯一性引理**,指:"在任意正确验证者的本地 DAG 中,每个 (author, round) 槽位至多被一个区块占据。" 这一引理(或其等价形式)是 DAG-BFT 安全性证明的标准构件:正是它,才使排序规则可以把"槽位"当作全序中的唯一对象来处理。本文已逐一核验:语料库 C 中的全部协议(DAG-Rider、Narwhal/Tusk、Bullshark、Cordial Miners、Mysticeti、Mahi-Mahi、Adelie)的安全性论证都使用了槽位唯一性引理,或与之等价的"每槽位至多一个被采纳区块"性质。

> **命题 1**:设 P 为一个 DAG-BFT 协议,其总序安全性证明依赖槽位唯一性引理。则 P 必须包含某种 enforce 非等价性的机制;若不含,则该安全性证明不成立。

### 6.2 论证:槽位唯一性的破坏

下文给出命题 1 的论证(argument)。须就严格度作一说明:本文以"论证 / 证明梗概(proof sketch)"的标准呈现它——其各步在逻辑上是完整的,但对异步消息调度的完全形式化刻画(如 I/O 自动机级别的执行建模)超出本文范围。

采用反证法。假设 P 的安全性证明依赖槽位唯一性引理,但 P 不包含任何 enforce 非等价性的机制。

**第一步:等价区块可同时进入正确验证者的本地 DAG。** 由于 P 不阻止等价,一个拜占庭作者 b 可以构造两个不同区块 X≠X′,二者位于同一 (author, round) 槽位。b 把 X 发送给一部分正确验证者、把 X′ 发送给另一部分。在异步网络中,敌手可自由调度消息送达顺序,使得在某个时刻确实存在两个正确验证者 v₁、v₂:v₁ 的本地 DAG 在槽位 (b,r) 上是 X,v₂ 的本地 DAG 在同一槽位上是 X′。这意味着槽位唯一性引理的结论为假——同一槽位在不同正确验证者的本地 DAG 中被不同区块占据。

**第二步:安全性证明因此失效。** P 的安全性证明依赖槽位唯一性引理,而该引理已被第一步证伪。需要具体指出它在证明链条中的哪一步失效:DAG-BFT 安全性证明的核心是 **quorum 交集论证**——任意两个规模为 n−f 的提交 quorum,其交集规模至少为 2(n−f)−n = n−2f;在 n≥3f+1 时 n−2f ≥ f+1,因而交集至少包含一个正确验证者;该正确验证者对每个槽位只持有唯一区块,于是它"钉住"了两个 quorum 在该槽位上的取值,迫使二者一致。这一步的有效性**前提性地依赖**槽位唯一性:它默认"任一正确验证者都全局性地为每个槽位钉住唯一区块"。一旦 b 等价,槽位 (b,r) 在不同正确验证者的本地 DAG 中已不再唯一,这一默认随之失效——交集中的正确验证者固然自身视图一致,但它对槽位 (b,r) 所持的区块只是 b 的两个分身(X 或 X′)之一,已无法迫使两个分别支持 v₁、v₂ 提交的 quorum 在该槽位上取值一致。quorum 交集不再蕴含取值一致,安全性证明的这一关键步骤断裂。

因此,在 P 不 enforce 非等价性的前提下,P 不存在一个依赖槽位唯一性的有效安全性证明——与"P 的安全性由该证明确立"矛盾。命题 1 得证:**安全性论证依赖槽位唯一性的 DAG-BFT 协议,必须 enforce 非等价性。**

**论证的范围:一个诚实的边界。** 命题 1 没有证明"一切可设想的安全 DAG-BFT 协议都必须 enforce 非等价性"这一与模型无关的强命题——原则上,可能存在一个用完全不同的证明技术(不经由槽位唯一性)建立安全性的协议,本文不排除这种可能。命题 1 证明的是一个**条件性**结论:只要协议沿用 DAG-BFT 标准的、以槽位唯一性为基石的安全性论证,非等价性就必须被 enforce。这一范围恰好是本文所需:已核验语料库 C 中的全部协议都属于这一类。这一论证与 FLP [2] 及 Bracha [5] 所揭示的异步环境根本约束一脉相承——它本质上是"异步网络中无法靠时间区分一致视图与分裂视图"这一困难,在 DAG 槽位结构下的具体化。

值得对照的是,本文在此**主动放弃**了一个更直观但不严格的论证:即"把正确验证者分成两组、让两组各自独立提交冲突全序"。该论证在最优容错 n=3f+1 下并不成立——两个能各自独立达到提交 quorum 的不相交正确节点组,需要至少 2(n−f) 个节点的参与,而 2(n−f)>n(因 n>2f),故无法构造。本文的论证不依赖"两组独立提交",而只依赖"等价破坏了安全性证明所依赖的槽位唯一性引理",从而绕开了上述算术障碍。

### 6.3 必要性的另一面:问责性视角的佐证

命题 1 从安全性角度论证了非等价性 enforcement 的不可或缺。问责性(accountability)研究从另一个角度提供了佐证。Polygraph [51] 是首个可问责的拜占庭共识算法:当分歧发生时,它能够检测出制造分歧的恶意节点。其关键发现是,仅靠检测等价(equivocation)本身并不足以问责——问责需要至少 Ω(n) 轮的额外日志。Civit 等人随后的 ABC 框架 [52] 则表明,把任意拜占庭共识协议转化为可问责协议,需要额外两轮全体通信与 O(n²) 比特的开销。这些结果从代价侧印证了本文的论点:与等价相关的保证,无论是"事前阻止"还是"事后问责",都必然伴随可观的、不可消去的成本。换言之,非等价性不仅在逻辑上必要(命题 1),其 enforcement 在代价上也不可能免费。

### 6.4 一个推论:enforcement 时机的自由,消除的不自由

命题 1 不限定 enforcement 以何种方式进行。它既可以是 certified DAG 中"引用前的 RBC 认证",也可以是 uncertified DAG 中"提交前的等价中和"。协议在 enforcement 的时机与机制上是自由的——但在"是否 enforce"上没有自由。这正好解释了第 5.2 节的经验观察:非等价性只能被平移,不能被消除。去认证改变的是 enforcement 的位置,而非其存在性。

须重申命题 1 在全文论证中的确切位置:它只锁定**非等价性**这一维,而非等价性恰是三个不变量中第 5 章判定为"低成本 ① 平移"的那一个。因此命题 1 **不蕴含**"去认证 = 结构性替换"这一整体主张——后者还需第 5 章对数据可用性(② 削弱+补偿)与因果历史完整性(① 平移)的独立分析共同支撑;真正承载隐性代价的可用性维度,其论证依据的是第 5.4 节的归纳与第 7 章的成本结构,而非命题 1。命题 1 的作用因此是精确而有限的:它堵死了"去认证可以干脆消除非等价性"这条最诱人的退路,使中心主张的三分之一获得了归纳之外的支撑;另外三分之二仍依赖第 5 章的归纳性分析。

### 6.5 向部分同步的推广:一个诚实的边界

命题 1 在纯异步模型中陈述。真实部署的 DAG-BFT(如 Bullshark [33]、Mysticeti [43])多运行于部分同步模型。部分同步并不削弱命题 1 的实质:在 GST 之前,网络实际上是异步的,敌手仍可如 §6.2 第一步那样,把等价区块送入不同正确验证者的本地 DAG,从而在 GST 前的窗口内破坏槽位唯一性。而安全性是一个必须**始终**维持、不能"等到 GST 之后"才成立的性质——因此,协议若要在 GST 前的异步窗口内保持安全,仍必须 enforce 非等价性。

需要诚实标注的是:GST 之后的同步期为协议提供了额外的时间结构,一个完整严格的部分同步版本论证应针对"GST 前异步窗口"重新表述其消息调度假设。本文不宣称已给出部分同步下逐字严格的证明,这是一个明确的边界。但由于命题 1 已被界定为一个**条件性**命题(以"安全性证明依赖槽位唯一性"为前提),它本身并不依赖纯异步假设的全部强度——只要存在一个网络行为如异步的窗口、且协议在该窗口内需维持安全,论证即可适用。语料库 C 中的协议均满足这一条件。

---

## 第 7 章 SubRQ3:延迟优势的条件化结论

命题 1 表明(在第 6 章界定的协议类内)非等价性必须被 enforce,第 5 章表明可用性必须被弱化补偿。本章把这些代价计入账本,回答 SubRQ3:uncertified 的延迟优势在何种条件下成立。

### 7.1 成本台账方法

本文不依赖任何单一来源报告的 benchmark 数字——按 SubRQ0 的警觉,这些数字本身可能是混淆的。本文采用成本台账方法:把协议运行中的通信步(message delay)与每区块开销,逐项归因到"维持某个不变量的某个机制"。这样得到的不是一个标量延迟,而是一个按不变量与情形分解的成本结构。

须强调一项记账原则:公平的成本台账必须让 certified 与 uncertified 双方的成本都随故障与不利网络而退化——certified DAG 在故障下同样有 RBC 重传、视图切换(view-change)等开销,并非一个固定不变的基线。因此本章关注的不是某一方的绝对最坏情况,而是两类设计的成本随条件恶化的**相对斜率**:uncertified 一侧的或有负债,是否比 certified 一侧增长得更快。下文的"翻转"判断,指的正是相对斜率的交叉,而非把一方的最坏情况与另一方的良好情况直接对比。

### 7.2 一个简化的成本模型

设 uncertified 版本相对认证版本在每轮节省的延迟为 Δ_save(主要来自省去 RBC 的额外通信步),补偿机制每次触发的额外延迟为 Δ_recover,补偿机制被触发的频率为 ρ(0≤ρ≤1)。则 uncertified 相对 certified 的净延迟优势可近似表示为

  净优势 ≈ Δ_save − ρ · Δ_recover。

这一模型有意保持简化,其目的不是给出精确数值,而是揭示三个变量之间的定性关系。两个观察立即可得。其一,当 ρ→0(良好情形)时,净优势 ≈ Δ_save>0,uncertified 占优;这与 Cordial Miners 把良好情形延迟由 4 步降至 3 步、Mysticeti 逼近 3 个消息轮次下界的报告一致 [42], [43]。其二,在把 ρ 与 Δ_recover 视为相互独立这一**显式建模假设**下,可解出一个临界频率 ρ\* = Δ_save / Δ_recover,当 ρ>ρ\* 时净优势转负——延迟优势被补偿成本反向吞噬。须强调这一独立性是一个被有意识采纳的简化:第 7.4 节将指出真实系统中 ρ 与 Δ_recover 可能相互耦合,届时 ρ\* 不再是一个良定义的标量阈值,而应被理解为"存在一条净优势归零的边界"这一定性事实。本文在用到 ρ\* 时,凡涉及精确数值即默认处于该独立性假设内,凡涉及定性结论(存在翻转)则不依赖它。下文逐一分析推高 ρ(及 Δ_recover)的三类条件。

为核对闭式模型的**实现正确性**,本文用一个 Monte Carlo 仿真把它展开为逐轮随机过程:在长度为 2000 轮的执行中,每一轮以概率 ρ 触发一次补偿,跨 500 条 trial 取均值。仿真均值在所测全部参数点上均收敛到解析值(相对误差 < 0.5%)。须明确这一核对的性质:逐轮随机过程的均值收敛到闭式期望,本质上是期望线性性的体现,因此该仿真验证的是"闭式公式被正确实现",属于实现层面的交叉核对(implementation cross-check),而**不**构成"模型贴合真实协议"的证据——后者需要真实协议实测,超出本文范围(见第 9 章)。仿真真正新增的信息是净优势的**方差**:它刻画了在给定 ρ 下逐次执行的离散程度,对应第 9 章所述"简化模型忽略排队与相互干扰"这一局限。图 1 给出该模型在 Δ_save = 2 时的净优势曲线。

**图 1** uncertified 相对 certified 的净延迟优势随恢复触发频率 ρ 的变化。Δ_save = 2;三条曲线对应不同的单次恢复成本 Δ_recover;圆点标出净优势归零的临界频率 ρ\*。注:本图为本节解析成本模型的数值图示,非真实协议实测。

![图 1 净延迟优势随恢复频率的变化](../stage2_write/code/figures/figure_1_net_advantage.png)

### 7.3 翻转条件一:恢复频率

第 5.6 节指出,可用性补偿机制的成本是一笔或有负债:良好情形下为零,故障情形下集中爆发。当系统中拜占庭节点积极地利用 uncertified DAG 的新攻击面——例如故意引用不提供内容的区块——补偿机制的触发频率 ρ 将显著上升。Adelie [45] 为应对正是这类新攻击面而引入额外机制,Shoal++ [38] 与 Autobahn [49] 对故障与不利网络条件下延迟的专门关注,都印证了故障情形并非可忽略的边缘情形,而是协议设计必须正视的常规情形。尽管本文不依赖任何单一来源的精确数字,这些已发表的故障实验为 ρ 的量级提供了定性锚点:Shoal++ [38] 与 Autobahn [49] 均专门测量了故障与网络抖动条件下的延迟,并报告了相对良好情形的显著劣化——这表明在真实部署中 ρ 远非可忽略的零,"故障情形"在成本台账中应作为常规列项,而非边角修正。当 ρ 越过临界值 ρ\*,uncertified 的延迟优势消失。

### 7.4 翻转条件二:部分同步退化与拥塞反馈

uncertified 协议的低延迟在很大程度上依赖良好的网络同步期。当系统进入部分同步退化(频繁的 GST 抖动)时,等价中和与可用性恢复都更频繁地被触发,Δ_recover 与 ρ 同时上升。Autobahn [49] 明确指出,传统 BFT 协议在网络抖动后会产生"宿醉"(hangover)——积压的请求导致延迟在同步恢复后仍长期劣化。uncertified DAG 的补偿机制在拥塞反馈下同样可能陷入这种正反馈式的延迟劣化:恢复请求本身占用带宽,带宽紧张又推高数据缺失率,从而进一步推高 ρ。

### 7.5 翻转条件三:网络非对称与负载偏斜

DispersedLedger [47] 表明,验证者带宽的差异会显著影响共识表现。在网络非对称或负载偏斜(workload skew)的条件下,uncertified DAG 的"按需恢复"策略会让低带宽节点成为新的瓶颈——它们既要参与排序,又要在数据缺失时承担恢复开销,从而推高其感知到的 Δ_recover。认证版本由于在传播阶段就均摊了数据分发,反而在这类条件下更稳健。这揭示了一个反直觉的事实:认证的"事前均摊"在不利网络下是一种鲁棒性资产,而非单纯的开销。这一论断需要一个诚实的限定:RBC 自身的 O(n²) 消息复杂度在带宽非对称下也会压迫低带宽节点,certified 一侧并非没有自己的非对称惩罚。本文的主张因此是**相对的**——事前、均匀支付的可用性成本,其随网络非对称恶化的斜率,通常小于"按需恢复"这种在数据缺失时集中爆发的成本;而非声称 certified 在不利网络下绝对占优。这正是 §7.1 所述"比较相对斜率而非绝对最坏情况"记账原则的一次具体应用。

### 7.6 条件化结论

综合 7.2–7.5,SubRQ3 的答案是:uncertified DAG 的延迟优势成立于一个明确界定的区域——网络接近同步、故障稀少、负载均衡(即 ρ<ρ\* 的区域);在该区域之外,优势会被隐性代价抵消,在恢复频率足够高或网络足够非对称时甚至反转。所谓"结构性"的优势,实为一个条件性的优势。下表概括了这一条件化结论。

| 条件维度 | uncertified 占优 | 优势被抵消/反转 |
|----------|------------------|------------------|
| 故障率 / 恢复频率 ρ | ρ 接近 0 | ρ 超过临界值 ρ\* |
| 网络同步性 | 长同步期、GST 稳定 | 部分同步退化、GST 频繁抖动 |
| 带宽分布 | 验证者带宽对称 | 网络非对称、负载偏斜 |
| 敌手行为 | 敌手不利用可用性攻击面 | 敌手主动制造数据缺失 |

图 2 把这一条件化结论可视化为一张参数空间地图:在 (ρ, Δ_recover) 平面上,临界边界 ρ\* 把平面切成两部分——其左上方为 uncertified 占优区,其右下方优势被抵消乃至反转。这张地图直观地显示,"uncertified 更快"并非平面上的普遍事实,而只是其中一个区域的局部事实。这就回答了贡献 B:uncertified 的延迟优势并非 fundamental,而是 conditional。

**图 2** (ρ, Δ_recover) 参数空间中的 uncertified 优势区域。颜色表示净延迟优势(>0 即 uncertified 占优);黑色实线为临界边界 ρ\* = Δ_save/Δ_recover。注:Δ_save = 2;本图为第 7 章解析成本模型的数值图示。

![图 2 优势区域地图](../stage2_write/code/figures/figure_2_advantage_region.png)

需要强调,这一结论与"现有 benchmark 在说谎"不同。本文的论点更精确:现有 benchmark 多在良好情形附近(ρ≈0)采样,它们报告的数字在其采样区域内是真实的,但把一个高维性能函数在少数维度上的投影,误读为了整个函数的形状。这就回答了贡献 A。

### 7.7 面向设计者的判定程序

第 7.6 节的结论表对设计者仍偏抽象。为提升可操作性,本文据上述分析给出一个粗粒度的判定程序——它不计算精确数值,只把"看情况"拆解为三个可分别估计的子判断,从而把一个具体部署定位到 §7.6 表格的某一行:

1. **估计敌手与故障强度。** 目标部署中是否存在有动机、有能力主动制造数据缺失的敌手?预期拜占庭比例是接近 f 上限,还是远低于?据此把恢复频率 ρ 粗分为"近 0 / 中等 / 高"。
2. **估计网络条件。** 同步期是否长而稳定、GST 抖动是否罕见?验证者带宽是否大致对称?据此把单次恢复成本 Δ_recover 粗分为"低 / 高"。
3. **定位。** 若(ρ 近 0)且(网络近同步、带宽对称),落入 §7.6 表格的"uncertified 占优"行;若(ρ 中等以上)或(网络非对称 / GST 频繁抖动),落入"优势被抵消乃至反转"行。
4. **边界情形。** 若 ρ 中等且网络条件中等,本文的定性模型给不出确定结论;此时应回退到针对该具体部署的受控实测——这正是第 10 章所列未来工作。

这一程序的价值不在于精确,而在于它把"延迟优势是否成立"从一个无法回答的笼统判断,转化为三个各自有据可依的工程估计;其输入(敌手模型、网络同步性、带宽分布)恰好都是部署方在选型阶段本就需要评估的量。

---

## 第 8 章 主贡献:availability-enforcement 作为深层设计轴

前七章的分析指向一个统一的结论。本章把这一结论从全文的潜结构(substructure)提升为显结构(superstructure),给出本文的主贡献 C。

### 8.1 从 SubRQ1–3 到一个深层轴

回顾全文:第 4 章表明三个不变量异质,可用性是其中唯一的物理型不变量;第 5 章表明去认证后隐性代价集中于可用性;第 6 章表明非等价性必须被 enforce,故其 enforcement 时机才是变量;第 7 章表明延迟优势的条件,本质上由可用性补偿机制的成本结构(ρ、Δ_recover)决定。这些结论汇聚成一个判断:**真正决定一个 DAG-BFT 协议行为的,不是"它是否认证",而是"它如何 enforce 数据可用性"。** certified/uncertified 这个二分,只是这一深层变量的一个粗糙投影。

### 8.2 深层轴的两个维度

本文把这一深层设计轴具体化为两个可操作的维度。

**维度一:availability-enforcement 时机。** 一个协议在何时强制保证一个区块的数据可用?本文区分三个位置:(i)引用前(pre-reference)——区块在能被其他区块引用之前,其可用性即被保证,certified DAG 属此;(ii)提交前(pre-commit)——区块可被引用,但在被提交进入全序之前其可用性被检查;(iii)提交后(post-commit)——可用性仅在提交后经由按需恢复来保证。enforcement 时机越靠后,良好情形延迟越低(Δ_save 越大),但故障情形的补偿成本越高(Δ_recover 越大)。

**维度二:reconciliation trigger 条件。** 当数据缺失被检测到时,协调修复(reconciliation)在何种条件下、以何种粒度被触发?是每发现一个缺失区块即触发,还是批量触发?触发是否依赖超时?触发的代价由谁承担?这一维度决定了第 7 章模型中 ρ 与 Δ_recover 的具体形态。

这两个维度共同构成的平面,才是描述 DAG-BFT 设计空间的恰当坐标系。把"是否认证"作为坐标,等于只观察了维度一的一个端点(引用前 vs 非引用前),并完全忽略了维度二。

### 8.3 用深层轴重新定位现有协议

在这一坐标系中,现有协议不再是"两类",而是散布的点。DAG-Rider [31]、Narwhal/Tusk [32]、Bullshark [33] 位于维度一的"引用前"端点,reconciliation 几乎不被触发(因为认证已保证可用性)。Mysticeti [43] 与 Mahi-Mahi [44] 位于"提交前/提交后"之间,reconciliation 由提交时的数据检查触发。DispersedLedger [47] 则是一个尤其有启发性的点:它把 enforcement 时机推后,却用纠删码编码的承诺把 reconciliation 的代价显著降低——这说明维度二上的精巧设计可以部分补偿维度一上的激进。换言之,在本文的坐标系中,"低延迟"与"鲁棒性"不是非此即彼,而是可以通过在两个维度上分别调参来联合优化的——这是二分法完全看不到的设计自由度。图 3 把语料库中的协议定位在这一坐标系中:certified 协议聚集于横轴"引用前"端、纵轴低位,uncertified 协议散布于"提交前/提交后"区间,而 Adelie 与 DispersedLedger 等中间设计落在二分法无法安放、本文坐标系却能清晰定位的位置上。

**图 3** 深层设计轴上的协议定位。横轴为 availability-enforcement 时机(引用前 / 提交前 / 提交后),纵轴为单次 reconciliation 开销(定性)。注:本图为按第 8 章深层轴框架的定性定位,坐标不代表实测数据。

![图 3 深层设计轴上的协议定位](../stage2_write/code/figures/figure_3_design_axis.png)

### 8.4 深层轴的解释力

一个坐标系是否优于另一个,取决于它能否解释前者解释不了的现象。certified/uncertified 二分无法自然地安放 Adelie [45]:Adelie 构建在 uncertified DAG 之上,却又引入了一套接近"认证"功能的检测与防护机制——在二分法下它是一个尴尬的混合体,既不纯粹 certified 也不纯粹 uncertified。但在本文的深层轴上,Adelie 是一个清晰的点:它的 availability-enforcement 时机靠后(继承 Mysticeti 的 uncertified 结构),而其 reconciliation trigger 被设计得格外精细(借助区块视图规则限制等价次数,从而压低 ρ)。本文的坐标系因此能够解释二分法解释不了的中间设计,这正是它作为分析框架的解释力所在。

需要诚实说明并对贡献 C 的主张作一个收窄。贡献 C 的风险不在于"深层轴构造不出来"——它的两个维度已在前七章的分析中隐式贯穿;其真正风险在于被指为单纯的重命名(relabeling)。这一指控有其道理:维度一(availability-enforcement 时机)在很大程度上确实是 certified/uncertified 二分的连续化——其"引用前"端点就是 certified。因此本文明确收窄贡献 C 的主张:贡献 C 真正非平凡、不可被归为重命名的部分,是**维度二(reconciliation trigger)的引入**,以及由此带来的**"延迟与鲁棒性是二维平面上可联合优化的目标,而非一维取舍"这一设计自由度**。DispersedLedger [47] 正是其证据:它在维度一上激进(时机靠后),却用维度二上的精巧设计(纠删码编码的承诺)把代价压低——这是任何只有维度一的坐标系都无法表达的。换言之,贡献 C 的可辩护内核应被理解为:reconciliation trigger 是一个被 certified/uncertified 二分完全遮蔽的、独立的设计维度。

一个坐标系的价值,还在于它能否指出尚未被占据的设计点。本文据此提出一个 **conjecture(尚待实现验证)**:"提交后 enforcement(维度一最靠后)+ 批量触发的 reconciliation + 纠删码编码的可用性承诺(维度二)"这一组合,在二维平面上对应一个语料库 C 尚未占据的点。其设想是:把维度一推到最靠后以最大化 Δ_save,同时用维度二的批量化与编码把 Δ_recover 压到接近 certified 的水平,从而争取一个"低良好情形延迟且低恢复成本"的区域。DispersedLedger 已展示了编码在维度二上的威力,但其维度一定位与上述组合不同;Mysticeti/Mahi-Mahi 在维度一靠后,但维度二仍以"逐缺失触发"为主。上述组合点能否真被构造出一个兼具两种优势的协议,是本文坐标系提出的一个**可证伪的预测**,留作未来工作——而能够提出这样一个具体、可证伪的预测,本身就是深层轴在"解释现有协议"之外、具有生成性的一面。

### 8.5 深层轴的延伸:availability-enforcement 与排序公平性

本文的深层轴虽以延迟为出发点,但它的影响并不止于延迟。DAG 共识的排序规则建立在 DAG 结构之上,而 DAG 结构由哪些区块可用、何时可用所塑造——这意味着 availability-enforcement 机制会间接影响交易的最终排序,进而触及最大可提取价值(Maximal Extractable Value, MEV)与排序公平性问题。

MEV 最早由 Daian 等人系统刻画:交易排序权可被用于抢先交易与重排序攻击,并危及共识层稳定性 [53]。为对抗之,Kelkar 等人提出"排序公平性"(order-fairness)并设计 Aequitas 协议族 [54],其后 Themis 进一步给出强排序公平性 [55]。这些工作多建立在 leader-based 协议之上。DAG 共识因其多提议者结构,被认为对排序公平性更友好——FairDAG [56] 正是把公平排序协议构建在 DAG 共识之上,利用其多提议者设计同时改善吞吐与公平性。

本文的深层轴为理解这一关联提供了新视角:当 availability-enforcement 时机靠后时,一个区块"是否进入 DAG"在更晚的时刻、由更依赖运行时条件的因素决定,这给了拜占庭节点更大的、操纵"哪些区块在排序时可见"的空间。换言之,availability-enforcement 时机不仅是一个延迟维度,也是一个排序可操纵性维度。

为把这一关联从断言落到机制,给出一个具体的(但尚不完整的)攻击草图。考虑 post-commit enforcement 下的一个拜占庭区块作者:由于其区块以尽力而为方式广播、内容可暂不提供,它能够先观察 DAG 与排序态势的演化,再"晚绑定"(late-binding)地决定是否让该区块的内容变得可恢复——使其被提交并插入到对应槽位的排序位置,或反之让其因不可恢复而被跳过。这等于赋予敌手一种能力:根据已经观察到的排序结果,有条件地决定某个携带交易的区块是否进入全序。而在 pre-reference(certified)enforcement 下,区块内容在作者能观察到排序态势之前就已被 RBC 认证锁定,这一晚绑定选项被关闭。因此 enforcement 时机靠后,确实打开了一个 certified 设计下不存在的排序操纵面。须强调这只是一个机制草图而非完整攻击分析:它未量化敌手由此可获取的 MEV、未给出防护下界,完整刻画留作未来工作;但它足以把"时机→可操纵性"的因果链从断言变为一个可被后续工作检验的具体命题。

这一观察表明,本文的深层轴并非仅服务于延迟分析,它是一个更具普遍解释力的设计坐标——这进一步支持了贡献 C 的可辩护内核:availability-enforcement 机制及其 reconciliation trigger,是比 certified/uncertified 更根本的变量。

---

## 第 9 章 局限、误用声明与威胁有效性

**范围限定。** 本文第 5 章的归纳性结论限定在语料库 C(DAG-Rider、Narwhal/Tusk、Bullshark、Cordial Miners、Mysticeti、Mahi-Mahi、Adelie 等)之内,不宣称对一切 DAG-BFT 协议普适。第 6 章命题 1 在纯异步模型下严格,部分同步下的推广本文仅作论证性讨论而未给出完整严格证明,这是一个明确的边界。

**模型抽象的代价。** 第 7 章的成本模型(净优势 ≈ Δ_save − ρ·Δ_recover)是一个有意简化的定性模型。它假定补偿成本可加性地计入,忽略了恢复请求之间可能的相互干扰与排队效应。这一简化使模型易于分析,但也意味着它给出的是趋势而非精确预测;真实系统中 ρ 与 Δ_recover 还可能相互耦合(如 7.4 节的拥塞反馈)。

**framing 风险。** 贡献 C 是一次 framing 工程:它把一个隐式贯穿全文的深层轴提升为显式坐标。这类工作的失败模式不是"定理塌了",而是"读者没接住"。本文通过把深层轴操作化为两个可测维度来降低这一风险,但无法完全消除。

**误用风险。** 如第 1.4 节所述,本文的条件化结论存在被断章引用的风险。本文重申:任何"uncertified 是否更优"的判断都不应脱离其网络与敌手模型前提。相比之下,贡献 C 由于陈述的是一个设计轴而非一个比较句,在结构上更不易被断章——这一性质本身也是本文的一个附带观察。

**未充分展开的利益相关者。** 本文的成本台账以验证者为中心。两个利益相关者的视角值得未来工作纳入:其一,轻客户端与外部验证者——数据可用性对无法存储全量数据的轻客户端尤为关键,availability-enforcement 时机靠后意味着轻客户端更晚才能确信数据可得,这与数据可用性采样(data-availability sampling)及欺诈/可用性证明 [48] 的研究直接相关;其二,验证者运营经济学——reconciliation 的恢复带宽由谁付费、如何计价,是真实部署决策中的现实变量,本文的定性模型未予刻画。把这两类视角纳入成本台账,会使第 7 章的条件化结论更贴近部署现实。

**威胁有效性。** 本文的核心威胁来自成本台账的参数化:Δ_save、Δ_recover、ρ 的具体取值依赖于协议实现与部署环境,本文给出的是其定性关系而非定量测量。一个完整的定量验证需要跨协议的受控实证,这构成本文未来工作的主要方向。本文的论证也依赖对若干协议安全性证明的解读,解读虽力求忠实,但不排除存在偏差;本文已尽量在引用处标注所依赖的具体性质。

---

## 第 10 章 结论与未来工作

本文对 DAG-based BFT 共识中一个被广泛接受的判断——"uncertified DAG 通过去认证免费降低延迟"——提出了系统性的质疑。

回答主研究问题:uncertified DAG 的低延迟优势成立于一个明确界定的条件区域(网络近同步、故障稀少、负载均衡,即在 §7.2 独立性假设下恢复频率 ρ 低于临界值 ρ\* 的区域),在该区域之外会被隐性代价抵消甚至反转。回答 SubRQ1:认证维持非等价性、数据可用性、因果历史完整性三个不变量,其中可用性是唯一的物理型不变量。回答 SubRQ2:去认证后,逻辑型不变量被低成本平移,物理型的数据可用性被弱化并补偿,隐性代价集中于此。回答 SubRQ3:延迟优势是条件性的,而非结构性的。

本文的根本结论是:移除认证不是做减法,而是一次结构性替换;而 certified/uncertified 只是浅层标签,真正的深层设计轴是 availability-enforcement 机制与 reconciliation trigger 条件。本文进一步论证,这一深层轴中真正不可被归为重命名的内核——reconciliation trigger 维度,以及延迟与鲁棒性的二维联合优化——不仅解释延迟,也触及排序公平性,并能提出可证伪的新设计点预测,因而具有超出原初问题的生成性与解释力。

对协议设计者而言,这意味着设计选择不应停留在"要不要认证",而应直接面对深层轴的两个维度——根据目标部署环境的故障率与网络对称性,选择 availability-enforcement 的时机与 reconciliation 的触发策略。对 benchmark 与评测设计者而言,这意味着评测必须扩大采样,覆盖故障情形与非对称网络,否则报告的延迟数字只是高维性能函数的一个低维投影。

未来工作有两个方向:其一,把第 8 章的深层轴形式化,给出两个维度上的可计算度量,特别是 reconciliation trigger 条件的形式刻画;其二,设计跨协议的受控实证,定量标定第 7 章成本台账中的关键参数 Δ_save、Δ_recover 与 ρ,从而把本文的定性条件化结论提升为定量的区域划分。

---

## 致谢与声明

**数据可用性声明(Data Availability Statement)**:本文为理论分析型研究,不涉及实验数据集。文中引用的全部协议规范与论文均为公开发表文献,可经由参考文献所列 DOI、arXiv 或 IACR ePrint 编号获取。第 7–8 章成本模型的仿真与图表生成代码(Python,含成本模型、Monte Carlo 仿真与 Figure 1–3 的可复现脚本)随论文一并提供;图 1、图 2 为该解析模型的数值图示,图 3 为按第 8 章深层轴框架的定性定位,均非真实协议实测。

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
[6] C. Cachin and S. Tessaro, "Asynchronous verifiable information dispersal," in *Proc. 24th IEEE Symp. Reliable Distributed Systems (SRDS)*, 2005, pp. 191–202.
[7] C. Cachin, K. Kursawe, and V. Shoup, "Random oracles in Constantinople: Practical asynchronous Byzantine agreement using cryptography," *J. Cryptol.*, vol. 18, no. 3, 2005.
[8] D. Boneh, B. Lynn, and H. Shacham, "Short signatures from the Weil pairing," in *Proc. ASIACRYPT*, 2001.
[9] C. Cachin, R. Guerraoui, and L. Rodrigues, *Introduction to Reliable and Secure Distributed Programming*, 2nd ed. Berlin, Germany: Springer, 2011.
[10] M. Castro and B. Liskov, "Practical Byzantine fault tolerance," in *Proc. 3rd USENIX Symp. Operating Systems Design and Implementation (OSDI)*, 1999.
[11] M. Yin, D. Malkhi, M. K. Reiter, G. Golan-Gueta, and I. Abraham, "HotStuff: BFT consensus with linearity and responsiveness," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2019, pp. 347–356.
[12] I. Abraham, D. Malkhi, K. Nayak, L. Ren, and M. Yin, "Sync HotStuff: Simple and practical synchronous state machine replication," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2020.
[13] E. Buchman, J. Kwon, and Z. Milosevic, "The latest gossip on BFT consensus," arXiv:1807.04938, 2018.
[14] C. Stathakopoulou, T. David, M. Pavlovic, and M. Vukolić, "Mir-BFT: High-throughput robust BFT for decentralized networks," arXiv:1906.05552, 2019.
[15] J. Camenisch, M. Drijvers, T. Hanke, Y.-A. Pignolet, V. Shoup, and D. Williams, "Internet Computer Consensus," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2022, pp. 81–91.
[16] T. Crain, V. Gramoli, M. Larrea, and M. Raynal, "DBFT: Efficient leaderless Byzantine consensus and its application to blockchains," in *Proc. 17th IEEE Int. Symp. Network Computing and Applications (NCA)*, 2018.
[17] A. Miller, Y. Xia, K. Croman, E. Shi, and D. Song, "The honey badger of BFT protocols," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2016.
[18] S. Duan, M. K. Reiter, and H. Zhang, "BEAT: Asynchronous BFT made practical," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2018, pp. 2028–2041.
[19] B. Guo, Z. Lu, Q. Tang, J. Xu, and Z. Zhang, "Dumbo: Faster asynchronous BFT protocols," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2020, pp. 803–818.
[20] I. Abraham, D. Malkhi, and A. Spiegelman, "Asymptotically optimal validated asynchronous Byzantine agreement," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2019.
[21] Y. Lu, Z. Lu, Q. Tang, and G. Wang, "Dumbo-MVBA: Optimal multi-valued validated asynchronous Byzantine agreement, revisited," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2020.
[22] S. Nakamoto, "Bitcoin: A peer-to-peer electronic cash system," white paper, 2008.
[23] J. A. Garay, A. Kiayias, and N. Leonardos, "The Bitcoin backbone protocol: Analysis and applications," in *Proc. EUROCRYPT*, 2015, pp. 281–310.
[24] Y. Sompolinsky and A. Zohar, "Secure high-rate transaction processing in Bitcoin," in *Proc. Financial Cryptography and Data Security (FC)*, 2015, pp. 507–527.
[25] Y. Gilad, R. Hemo, S. Micali, G. Vlachos, and N. Zeldovich, "Algorand: Scaling Byzantine agreements for cryptocurrencies," in *Proc. 26th ACM Symp. Operating Systems Principles (SOSP)*, 2017, pp. 51–68.
[26] Team Rocket, M. Yin, K. Sekniqi, R. van Renesse, and E. G. Sirer, "Scalable and probabilistic leaderless BFT consensus through metastability," arXiv:1906.08936, 2019.
[27] V. Bagaria, S. Kannan, D. Tse, G. Fanti, and P. Viswanath, "Prism: Deconstructing the blockchain to approach physical limits," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2019.
[28] J. Neu, E. N. Tas, and D. Tse, "Ebb-and-flow protocols: A resolution of the availability-finality dilemma," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2021.
[29] V. Buterin, "Ethereum: A next-generation smart contract and decentralized application platform," white paper, 2014.
[30] V. Buterin and V. Griffith, "Casper the friendly finality gadget," arXiv:1710.09437, 2017.
[31] I. Keidar, E. Kokoris-Kogias, O. Naor, and A. Spiegelman, "All you need is DAG," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2021.
[32] G. Danezis, L. Kokoris-Kogias, A. Sonnino, and A. Spiegelman, "Narwhal and Tusk: A DAG-based mempool and efficient BFT consensus," in *Proc. 17th European Conf. Computer Systems (EuroSys)*, 2022.
[33] A. Spiegelman, N. Giridharan, A. Sonnino, and L. Kokoris-Kogias, "Bullshark: DAG BFT protocols made practical," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2022.
[34] A. Gągol, D. Leśniak, D. Straszak, and M. Świętek, "Aleph: Efficient atomic broadcast in asynchronous networks with Byzantine nodes," in *Proc. 1st ACM Conf. Advances in Financial Technologies (AFT)*, 2019.
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
[47] L. Yang, S. J. Park, M. Alizadeh, S. Kannan, and D. Tse, "DispersedLedger: High-throughput Byzantine consensus on variable bandwidth networks," in *Proc. 19th USENIX Symp. Networked Systems Design and Implementation (NSDI)*, 2022.
[48] M. Al-Bassam, A. Sonnino, and V. Buterin, "Fraud and data availability proofs: Detecting invalid blocks in light clients," in *Proc. Financial Cryptography and Data Security (FC)*, 2021.
[49] N. Giridharan, F. Suri-Payer, I. Abraham, L. Alvisi, and N. Crooks, "Autobahn: Seamless high speed BFT," in *Proc. 30th ACM Symp. Operating Systems Principles (SOSP)*, 2024.
[50] E. Kokoris-Kogias, P. Jovanovic, L. Gasser, N. Gailly, E. Syta, and B. Ford, "OmniLedger: A secure, scale-out, decentralized ledger via sharding," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2018, pp. 583–598.
[51] P. Civit, S. Gilbert, and V. Gramoli, "Polygraph: Accountable Byzantine agreement," in *Proc. IEEE Int. Conf. Distributed Computing Systems (ICDCS)*, 2021.
[52] P. Civit, S. Gilbert, V. Gramoli, R. Guerraoui, and J. Komatovic, "As easy as ABC: Optimal (A)ccountable (B)yzantine (C)onsensus is easy!," in *Proc. IEEE Int. Parallel and Distributed Processing Symp. (IPDPS)*, 2022.
[53] P. Daian, S. Goldfeder, T. Kell, Y. Li, X. Zhao, I. Bentov, L. Breidenbach, and A. Juels, "Flash Boys 2.0: Frontrunning, transaction reordering, and consensus instability in decentralized exchanges," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2020.
[54] M. Kelkar, F. Zhang, S. Goldfeder, and A. Juels, "Order-fairness for Byzantine consensus," in *Proc. CRYPTO*, 2020.
[55] M. Kelkar, S. Deb, S. Long, A. Juels, and S. Kannan, "Themis: Fast, strong order-fairness in Byzantine consensus," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2023.
[56] D. Kang, J. Chen, T. T. A. Dinh, and M. Sadoghi, "FairDAG: Consensus fairness over multi-proposer causal design," *Proc. VLDB Endowment*, vol. 19, 2026.
[57] M. Raikwar, N. Polyanskii, and S. Müller, "SoK: DAG-based consensus protocols," in *Proc. IEEE Int. Conf. Blockchain and Cryptocurrency (ICBC)*, 2024.
[58] S. Bano, A. Sonnino, M. Al-Bassam, S. Azouvi, P. McCorry, S. Meiklejohn, and G. Danezis, "SoK: Consensus in the age of blockchains," in *Proc. 1st ACM Conf. Advances in Financial Technologies (AFT)*, 2019.
[59] J. A. Garay and A. Kiayias, "SoK: A consensus taxonomy in the blockchain era," in *Proc. CT-RSA*, 2020.
[60] C. Cachin and M. Vukolić, "Blockchain consensus protocols in the wild," in *Proc. 31st Int. Symp. Distributed Computing (DISC)*, 2017.
[61] L. Baird, "The Swirlds hashgraph consensus algorithm: Fair, fast, Byzantine fault tolerance," Swirlds, Tech. Rep. SWIRLDS-TR-2016-01, 2016.
[62] T. Crain, C. Natoli, and V. Gramoli, "Red Belly: A secure, fair and scalable open blockchain," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2021, pp. 466–483.

---

*定稿(Stage 5 FINALIZE 产出)| 经 Stage 1 socratic 研究规划 → Stage 2 写作 → Stage 2.5 完整性核查(PASS)→ Stage 3 五人评审(Major Revision)→ Stage 4 修订(13 项)→ Stage 3' 验证复审(Minor Revision)→ Stage 4.5 终核(PASS)定稿 | 62 篇参考文献,3 图,中英文双语摘要*
