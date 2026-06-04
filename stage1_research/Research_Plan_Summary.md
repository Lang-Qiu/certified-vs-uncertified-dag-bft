# Research Plan Summary — Stage 1 RESEARCH 交付物

> socratic 引导模式 | academic-pipeline v3.7.0 | 生成日期 2026-05-20
> 本文件为 Stage 1 → Stage 2 的 handoff artifact。

---

## 工作题目(候选,Stage 2 最终敲定)

- **主选:** 《认证之为结构:DAG-based BFT 共识中去认证的隐性代价与延迟优势的条件性》
- 备选 1:《投影与轴:重新审视 certified 与 uncertified DAG-based BFT 共识的比较框架》
- 备选 2:《去认证不是减法:availability-enforcement 作为 DAG-based BFT 深层设计轴的分析》

---

## 一、研究问题(Layer 1)

**主 RQ:** 在何种网络与敌手条件下,uncertified DAG-based BFT 相对 certified 设计的"低延迟优势"才真正成立?

**子问题:**
- **SubRQ0**(潜框架,置于引言/背景):certified 与 uncertified 的比较对象是否公平?(混淆变量 / 内部效度问题)
- **SubRQ1**:认证机制(Reliable Broadcast)为协议买到了哪些理论保证——non-equivocation、availability、causal-history integrity?
- **SubRQ2**:去掉认证后,这些保证被转移/重建到哪里?隐性代价以何种形式出现?
- **SubRQ3**:延迟优势在哪些条件下成立、被抵消、甚至反转?

**中心主张(thesis,已学术化):**
> 在 DAG-based BFT 共识中,移除认证机制(de-certification)并非一项可分离的性能优化,而是一次**结构性替换**(structural substitution):认证承载的安全性/活性不变量被重新分配至协议其他组件。uncertified 相对 certified 的提交延迟优势是**条件性的**——当且仅当承接这些不变量的替代机制,在目标网络/敌手模型下边际成本低于认证时方成立。

**升级表述(经 Layer 4 三分法):** 去认证只产生 ①平移 与 ②削弱+补偿,从不产生 ③消除;隐性代价集中在 ②。

---

## 二、方法论方向(Layer 2)

- **模块化分解**:把复杂协议抽象为功能模块;模块硬边界按**安全性/活性不变量**划定(客观标准,去研究者主观性 → 闭合 SubRQ0)。
- **受控 minimal-pair 比较**:不硬比异质系统,在尽量相同的协议背景下**仅改变认证强度**,观察保证迁移与代价变化。
- **判据**:C1-B 三分法(平移 / 削弱+补偿 / 消除)作分类判据 + C1-C 成本-证明双判据作操作化工具(某不变量算被重新承接 ⟺ 成本台账有可归因非零成本 ∧ 安全性证明有一步强制它)。
- **F4 必要性论证**:采 C2-M3——纯异步模型(n=3f+1, Byzantine)严格证明"非等价性对 DAG-BFT 安全性必要" + 部分同步推广的诚实讨论;C2-M4(限定到通用 DAG-BFT 模板的保守边界声明)作安全网写入讨论章。

---

## 三、证据策略(Layer 3)

**证据骨架(互补四层):**
- **E1 不变量定位表**:`不变量 × 协议 → 维持机制` 映射(论文骨架)。
- **E2 安全性证明审查**:读 uncertified 协议形式化证明,定位承重机制(严谨性来源)。
- **E3 成本台账**:message-delay 计数 + 每区块开销,按不变量归因(给 SubRQ3 装牙齿)。
- **E4 天然 minimal pair**:同时有 certified/uncertified 双版本的协议族,diff 出补偿机制(锚定)。

**证伪策略:** F1 穷举证明审计 / F2 敌手构造测试 / F3 限定明确语料库 C(不证全称否定)/ F4 必要性定理。

---

## 四、已知局限与诚实声明(Layer 4)

1. 判据须**预先讲定**以防 tautology —— 已用 C1-B + C1-C 锁定。
2. F4 必要性命题须写清网络/敌手模型 —— M3 异步严格 + 部分同步诚实标注边界。
3. 三不变量的 ①②③ 归类是**分析章产物**,须写成"工作假设 H → C1-C 检验",不可动笔前预设。
4. 无法证全称否定,协议语料库 C 须明确界定;结论限定在 C 内。
5. C 的风险是 **naming/framing 失败**(读者没接住),非构造失败;watch-out:显式命名深层轴时可能反向暴露隐式 theory gap → 写作时"边提升边核验"。
6. **misuse**:conditional 结论易被断章("uncertified 没问题");C 的 axis 表述结构性抗断章——结论章须用一句话点明该风险。

---

## 五、预期贡献(Layer 5)

三层递进贡献框架,**主贡献 = C**:
- **A — Benchmark-as-truth 批判**:throughput/latency 数字是高维性能函数在少数维度上的投影;现有 evaluation pipeline 系统性地只采样 happy path 附近,certified/uncertified 优劣随 fault pattern / 网络非对称 / workload skew 翻转。
- **B — 优势 fundamentality 批判**:uncertified 的 happy-path 延迟优势并非结构性,会被 recovery 频率 / partial-sync 退化 / 拥塞反馈下的 amortized cost 反向吞噬——"fundamental"实为 conditional。
- **C —(主贡献)轴批判**:certified/uncertified 不是描述协议的合适轴;真正决定行为的深层轴 = **availability-enforcement 机制 + reconciliation trigger 条件**,certified/uncertified 只是其低维投影。

**受众:** 协议设计者(应选轴而非选标签)、benchmark/evaluation 设计者(应扩大采样覆盖)。

---

## 六、完整 INSIGHT 清单(16 条)

1. 选定 certified vs uncertified DAG 设计权衡为核心;偏好理论深度;视延迟(A)、排序公平/MEV(D)为相关利害。
2. RQ 形状 = ③条件化结论(骨架)+ ①隐性代价批判(灵魂);能一句话陈述论点。
3. 提出 SubRQ0:现有比较可能不公平 —— 混淆变量/内部效度问题。
4. 方法论 = 模块化分解 + 受控 minimal-pair 比较。
5. 核心发现(脊梁):认证不是可拆卸的性能优化模块,而是维持协议不变量的结构性机制 → 去认证 = 结构性替换。
6. 模块硬边界须按固定客观标准划定,防混淆变量藏入模块内。
7. 划界标准 = 安全性/活性不变量;每模块 = 维持某一不变量的机制 → 分解去主观化。
8. 决定执行 F4 必要性论证(理由:论文需理论深度,接受规范性风险)。
9. availability 最难重新安家:逻辑型不变量可由规则约束,availability 是物理传播问题 → 隐性代价集中于此。
10. 判据 = C1-B 三分法 + C1-C 成本-证明双判据;中心主张升级为"只产生①②、从不产生③"。
11. F4 模型 = C2-M3(异步严格 + 部分同步讨论),C2-M4 作安全网。
12. 三不变量①②③归类是分析章产物,写成"工作假设 H → 检验"(反同义反复)。
13. 三层递进贡献框架 A(benchmark 批判)→ B(fundamentality 批判)→ C(轴批判)。
14. C 的风险是 naming 失败(framing 工程)非构造失败;失败可恢复。
15. C 结构性抗断章:claim 的语法形态决定可滥用性,axis 型陈述无可提取的比较句位。
16. B 引用半衰期短,conditional 结论会被 unconditional 后续淹没;停 B 等于把 C 让给别人。

---

## 七、临时论文结构(供 Stage 2 structure_architect 参考)

| # | 章节 | 对应 |
|---|------|------|
| 1 | 引言(含 SubRQ0 潜框架 + misuse 声明) | RQ, A |
| 2 | 背景:DAG-based BFT 共识谱系与 certified/uncertified 之分 | 文献 |
| 3 | 方法论:模块化分解 + 受控 minimal-pair + 三分判据 | Layer 2 |
| 4 | SubRQ1:认证买到的三个不变量 | E1, E2 |
| 5 | SubRQ2:去认证后的保证迁移与隐性代价(三分法,availability 为重) | E1-E4, H |
| 6 | F4:非等价性必要性论证(异步严格 + 部分同步讨论) | F4, M3/M4 |
| 7 | SubRQ3:延迟优势的条件化结论 + 成本台账 | E3, B |
| 8 | 主贡献 C:availability-enforcement 作为深层设计轴 | C |
| 9 | 局限、misuse 声明与威胁有效性 | Layer 4 |
| 10 | 结论与未来工作 | Layer 5 |

---

## 八、工作假设 H(待论文检验,勿预设为结论)

non-equivocation、causal-history integrity → 大概率落入 ①(逻辑型,可规则化平移);availability → 大概率落入 ②(物理型,削弱 + 补偿)。论文任务是用 C1-C 验证或推翻 H。

---

## 九、Recommended Next Steps

→ **Stage 2 WRITE**(academic-paper)。Phase 1 文献搜集须围绕 DAG-based BFT 谱系顶会论文(PODC / EuroSys / CCS / OSDI / FC / AFT 等),目标 ≥ 60 篇,中文为主、术语保留英文,目标篇幅 ~20000 字。
