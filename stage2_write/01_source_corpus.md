# Stage 2 / Phase 1 — Source Corpus(文献库与引用清单)

> 论文:《认证之为结构:DAG-based BFT 共识中去认证的隐性代价与延迟优势的条件性》
> 引用格式:IEEE | 检索日期:2026-05-20 | 共 62 篇,全部经 WebSearch 真实核验

## 检索策略(Search Strategy)
- **数据库/来源**:arXiv、IACR ePrint、ACM DL、IEEE Xplore、Springer、USENIX、DROPS/Dagstuhl、Semantic Scholar、dblp
- **核心关键词**:DAG-based BFT、certified/uncertified DAG、Reliable Broadcast、Byzantine atomic broadcast、consensus latency、mempool consensus、equivocation、data availability
- **纳入标准**:顶会/顶刊(PODC, DISC, CCS, EuroSys, OSDI, NSDI, NDSS, S&P, FC, AFT, ICDCS, SOSP, OPODIS, IPDPS)或高被引经典;时间跨度 1982–2026,以 2021–2025 DAG 共识前沿为重心
- **排除**:无同行评议且无法核验元数据者

## 引用清单(IEEE 格式)

### A. 分布式共识基础理论
[1] L. Lamport, R. Shostak, and M. Pease, "The Byzantine generals problem," *ACM Trans. Program. Lang. Syst.*, vol. 4, no. 3, pp. 382–401, 1982.
[2] M. J. Fischer, N. A. Lynch, and M. S. Paterson, "Impossibility of distributed consensus with one faulty process," *J. ACM*, vol. 32, no. 2, pp. 374–382, 1985.
[3] C. Dwork, N. Lynch, and L. Stockmeyer, "Consensus in the presence of partial synchrony," *J. ACM*, vol. 35, no. 2, pp. 288–323, 1988.
[4] F. B. Schneider, "Implementing fault-tolerant services using the state machine approach: A tutorial," *ACM Comput. Surv.*, vol. 22, no. 4, pp. 299–319, 1990.
[5] G. Bracha, "Asynchronous Byzantine agreement protocols," *Inf. Comput.*, vol. 75, no. 2, pp. 130–143, 1987.
[6] C. Cachin and S. Tessaro, "Asynchronous verifiable information dispersal," in *Proc. 24th IEEE Symp. Reliable Distributed Systems (SRDS)*, 2005, pp. 191–201.
[7] C. Cachin, K. Kursawe, and V. Shoup, "Random oracles in Constantinople: Practical asynchronous Byzantine agreement using cryptography," *J. Cryptol.*, vol. 18, no. 3, pp. 219–246, 2005.
[8] D. Boneh, B. Lynn, and H. Shacham, "Short signatures from the Weil pairing," in *Proc. ASIACRYPT*, 2001, pp. 514–532.
[9] C. Cachin, R. Guerraoui, and L. Rodrigues, *Introduction to Reliable and Secure Distributed Programming*, 2nd ed. Berlin, Germany: Springer, 2011.

### B. Leader-based BFT 共识
[10] M. Castro and B. Liskov, "Practical Byzantine fault tolerance," in *Proc. 3rd USENIX Symp. Operating Systems Design and Implementation (OSDI)*, 1999, pp. 173–186.
[11] M. Yin, D. Malkhi, M. K. Reiter, G. Golan-Gueta, and I. Abraham, "HotStuff: BFT consensus with linearity and responsiveness," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2019, pp. 347–356.
[12] I. Abraham, D. Malkhi, K. Nayak, L. Ren, and M. Yin, "Sync HotStuff: Simple and practical synchronous state machine replication," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2020, pp. 106–118.
[13] E. Buchman, J. Kwon, and Z. Milosevic, "The latest gossip on BFT consensus," arXiv:1807.04938, 2018.
[14] C. Stathakopoulou, T. David, M. Pavlovic, and M. Vukolić, "Mir-BFT: High-throughput robust BFT for decentralized networks," arXiv:1906.05552, 2019.
[15] J. Camenisch, M. Drijvers, T. Hanke, Y.-A. Pignolet, V. Shoup, and D. Williams, "Internet Computer Consensus," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2022, pp. 81–91.
[16] T. Crain, V. Gramoli, M. Larrea, and M. Raynal, "DBFT: Efficient leaderless Byzantine consensus and its application to blockchains," in *Proc. 17th IEEE Int. Symp. Network Computing and Applications (NCA)*, 2018.

### C. 异步 BFT 共识
[17] A. Miller, Y. Xia, K. Croman, E. Shi, and D. Song, "The honey badger of BFT protocols," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2016, pp. 31–42.
[18] S. Duan, M. K. Reiter, and H. Zhang, "BEAT: Asynchronous BFT made practical," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2018, pp. 2028–2041.
[19] B. Guo, Z. Lu, Q. Tang, J. Xu, and Z. Zhang, "Dumbo: Faster asynchronous BFT protocols," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2020, pp. 803–818.
[20] I. Abraham, D. Malkhi, and A. Spiegelman, "Asymptotically optimal validated asynchronous Byzantine agreement," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2019, pp. 337–346.
[21] Y. Lu, Z. Lu, Q. Tang, and G. Wang, "Dumbo-MVBA: Optimal multi-valued validated asynchronous Byzantine agreement, revisited," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2020, pp. 129–138.

### D. 区块链共识与 PoS/PoW
[22] S. Nakamoto, "Bitcoin: A peer-to-peer electronic cash system," white paper, 2008.
[23] J. A. Garay, A. Kiayias, and N. Leonardos, "The Bitcoin backbone protocol: Analysis and applications," in *Proc. EUROCRYPT*, 2015, pp. 281–310.
[24] Y. Sompolinsky and A. Zohar, "Secure high-rate transaction processing in Bitcoin," in *Proc. Financial Cryptography and Data Security (FC)*, 2015, pp. 507–527.
[25] Y. Gilad, R. Hemo, S. Micali, G. Vlachos, and N. Zeldovich, "Algorand: Scaling Byzantine agreements for cryptocurrencies," in *Proc. 26th ACM Symp. Operating Systems Principles (SOSP)*, 2017, pp. 51–68.
[26] Team Rocket, M. Yin, K. Sekniqi, R. van Renesse, and E. G. Sirer, "Scalable and probabilistic leaderless BFT consensus through metastability," arXiv:1906.08936, 2019.
[27] V. Bagaria, S. Kannan, D. Tse, G. Fanti, and P. Viswanath, "Prism: Deconstructing the blockchain to approach physical limits," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2019, pp. 585–602.
[28] J. Neu, E. N. Tas, and D. Tse, "Ebb-and-flow protocols: A resolution of the availability-finality dilemma," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2021, pp. 446–465.
[29] V. Buterin, "Ethereum: A next-generation smart contract and decentralized application platform," white paper, 2014.
[30] V. Buterin and V. Griffith, "Casper the friendly finality gadget," arXiv:1710.09437, 2017.

### E. DAG-based BFT 共识:certified DAG
[31] I. Keidar, E. Kokoris-Kogias, O. Naor, and A. Spiegelman, "All you need is DAG," in *Proc. ACM Symp. Principles of Distributed Computing (PODC)*, 2021, pp. 165–175.
[32] G. Danezis, L. Kokoris-Kogias, A. Sonnino, and A. Spiegelman, "Narwhal and Tusk: A DAG-based mempool and efficient BFT consensus," in *Proc. 17th European Conf. Computer Systems (EuroSys)*, 2022, pp. 34–50.
[33] A. Spiegelman, N. Giridharan, A. Sonnino, and L. Kokoris-Kogias, "Bullshark: DAG BFT protocols made practical," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2022, pp. 2705–2718.
[34] A. Gągol, D. Leśniak, D. Straszak, and M. Świętek, "Aleph: Efficient atomic broadcast in asynchronous networks with Byzantine nodes," in *Proc. 1st ACM Conf. Advances in Financial Technologies (AFT)*, 2019, pp. 214–228.
[35] X. Dai, Z. Zhang, J. Xiao, J. Yue, X. Xie, and H. Jin, "GradedDAG: An asynchronous DAG-based BFT consensus with lower latency," in *Proc. 42nd Int. Symp. Reliable Distributed Systems (SRDS)*, 2023.
[36] X. Dai, G. Wang, J. Xiao, Z. Guo, R. Hao, X. Xie, and H. Jin, "LightDAG: A low-latency DAG-based BFT consensus through lightweight broadcast," in *Proc. IEEE Int. Parallel and Distributed Processing Symp. (IPDPS)*, 2024, pp. 998–1008.
[37] A. Spiegelman, B. Arun, R. Gelashvili, and Z. Li, "Shoal: Improving DAG-BFT latency and robustness," in *Proc. Financial Cryptography and Data Security (FC)*, 2024.
[38] B. Arun, Z. Li, F. Suri-Payer, S. Das, and A. Spiegelman, "Shoal++: High throughput DAG BFT can be fast!," in *Proc. 22nd USENIX Symp. Networked Systems Design and Implementation (NSDI)*, 2025. (arXiv:2405.20488)
[39] N. Shrestha, R. Shrothrium, A. Kate, and K. Nayak, "Sailfish: Towards improving the latency of DAG-based BFT," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2025. (IACR ePrint 2024/472)
[40] D. Malkhi, C. Stathakopoulou, and M. Yin, "BBCA-Chain: Low latency, high throughput BFT consensus on a DAG," in *Proc. Financial Cryptography and Data Security (FC)*, 2024. (arXiv:2310.06335)
[41] N. Shrestha and A. Kate, "Towards improving throughput and scalability of DAG-based BFT SMR," IACR ePrint 2025/877, 2025.

### F. DAG-based BFT 共识:uncertified DAG
[42] I. Keidar, O. Naor, O. Poupko, and E. Shapiro, "Cordial Miners: Fast and efficient consensus for every eventuality," in *Proc. 37th Int. Symp. Distributed Computing (DISC)*, 2023.
[43] K. Babel, A. Chursin, G. Danezis, L. Kokoris-Kogias, and A. Sonnino, "Mysticeti: Reaching the limits of latency with uncertified DAGs," in *Proc. Network and Distributed System Security Symp. (NDSS)*, 2025. (arXiv:2310.14821)
[44] P. Jovanovic, L. Kokoris-Kogias, B. Kumara, A. Sonnino, P. Tennage, and I. Zablotski, "Mahi-Mahi: Low-latency asynchronous BFT DAG-based consensus," in *Proc. IEEE Int. Conf. Distributed Computing Systems (ICDCS)*, 2025, pp. 549–559.
[45] A. Chursin, "Adelie: Detection and prevention of Byzantine behaviour in DAG-based consensus protocols," arXiv:2408.02000, 2024.
[46] S. Blackshear, A. Chursin, G. Danezis, A. Kichidis, L. Kokoris-Kogias, X. Li, M. Logan, et al., "Sui Lutris: A blockchain combining broadcast and consensus," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2024.

### G. 数据可用性、信息分散与可扩展性
[47] L. Yang, S. J. Park, M. Alizadeh, S. Kannan, and D. Tse, "DispersedLedger: High-throughput Byzantine consensus on variable bandwidth networks," in *Proc. 19th USENIX Symp. Networked Systems Design and Implementation (NSDI)*, 2022, pp. 493–512.
[48] M. Al-Bassam, A. Sonnino, and V. Buterin, "Fraud and data availability proofs: Detecting invalid blocks in light clients," in *Proc. Financial Cryptography and Data Security (FC)*, 2021, pp. 279–298.
[49] N. Giridharan, F. Suri-Payer, I. Abraham, L. Alvisi, and N. Crooks, "Autobahn: Seamless high speed BFT," in *Proc. 30th ACM Symp. Operating Systems Principles (SOSP)*, 2024.
[50] H. Kokoris-Kogias, P. Jovanovic, L. Gasser, N. Gailly, E. Syta, and B. Ford, "OmniLedger: A secure, scale-out, decentralized ledger via sharding," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2018, pp. 583–598.

### H. 问责性、公平排序与 MEV
[51] P. Civit, S. Gilbert, and V. Gramoli, "Polygraph: Accountable Byzantine agreement," in *Proc. IEEE Int. Conf. Distributed Computing Systems (ICDCS)*, 2021, pp. 403–413.
[52] P. Civit, S. Gilbert, V. Gramoli, R. Guerraoui, and J. Komatovic, "As easy as ABC: Optimal (A)ccountable (B)yzantine (C)onsensus is easy!," in *Proc. IEEE Int. Parallel and Distributed Processing Symp. (IPDPS)*, 2022, pp. 560–570.
[53] P. Daian, S. Goldfeder, T. Kell, Y. Li, X. Zhao, I. Bentov, L. Breidenbach, and A. Juels, "Flash Boys 2.0: Frontrunning, transaction reordering, and consensus instability in decentralized exchanges," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2020, pp. 910–927.
[54] M. Kelkar, F. Zhang, S. Goldfeder, and A. Juels, "Order-fairness for Byzantine consensus," in *Proc. CRYPTO*, 2020, pp. 451–480.
[55] M. Kelkar, S. Deb, S. Long, A. Juels, and S. Kannan, "Themis: Fast, strong order-fairness in Byzantine consensus," in *Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS)*, 2023, pp. 475–489.
[56] D. Kang, J. Chen, T. T. A. Dinh, and M. Sadoghi, "FairDAG: Consensus fairness over multi-proposer causal design," *Proc. VLDB Endowment*, vol. 19, 2026. (arXiv:2504.02194)

### I. 综述、系统化与稳健性
[57] M. Raikwar, N. Polyanskii, and S. Müller, "SoK: DAG-based consensus protocols," in *Proc. IEEE Int. Conf. Blockchain and Cryptocurrency (ICBC)*, 2024. (arXiv:2411.10026)
[58] S. Bano, A. Sonnino, M. Al-Bassam, S. Azouvi, P. McCorry, S. Meiklejohn, and G. Danezis, "SoK: Consensus in the age of blockchains," in *Proc. 1st ACM Conf. Advances in Financial Technologies (AFT)*, 2019, pp. 183–198.
[59] J. A. Garay and A. Kiayias, "SoK: A consensus taxonomy in the blockchain era," in *Proc. CT-RSA*, 2020, pp. 284–318.
[60] C. Cachin and M. Vukolić, "Blockchain consensus protocols in the wild," in *Proc. 31st Int. Symp. Distributed Computing (DISC)*, 2017.
[61] L. Baird, "The Swirlds hashgraph consensus algorithm: Fair, fast, Byzantine fault tolerance," Swirlds, Tech. Rep. SWIRLDS-TR-2016-01, 2016.
[62] T. Crain, C. Natoli, and V. Gramoli, "Red Belly: A secure, fair and scalable open blockchain," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2021, pp. 466–483.

---

## 文献矩阵(Literature Matrix:文献 × 论文章节)

| 章节 | 主要支撑文献 |
|------|-------------|
| 第2章 背景:BFT 谱系 | [1]–[5],[10]–[28] |
| 第2章 背景:DAG 共识谱系 | [31]–[46],[57] |
| 第3章 方法论:不变量与模块分解 | [2],[3],[5],[6],[9],[51],[52] |
| 第4章 SubRQ1:认证买到的三个不变量 | [5],[6],[31],[32],[34],[39] |
| 第5章 SubRQ2:保证迁移与隐性代价 | [42]–[46],[36],[41],[47],[48] |
| 第6章 F4:非等价性必要性论证 | [1],[2],[3],[5],[51],[52] |
| 第7章 SubRQ3:延迟优势的条件化结论 | [33],[37],[38],[39],[43],[44],[49] |
| 第8章 主贡献 C:availability-enforcement 深层轴 | [6],[42]–[48],[56] |
| 第9章 局限、misuse、威胁有效性 | [53]–[56],[57] |

## 关键事实锚点(供 draft_writer 使用,均来自上述文献)
- DAG 共识"零额外通信":排序在本地 DAG 上完成,不需共识层额外消息 —— [31],[32],[33]
- certified DAG 的延迟:Tusk good-case ~7 步、worst ~21 步;DAG-Rider best ~12 步 —— [35],[36]
- Bullshark 为部分同步、有快速路径,继承 DAG-Rider 的 fairness 与异步 liveness —— [33]
- uncertified DAG:Mysticeti-C 去除显式 block 认证,达 3 message rounds 延迟下界,WAN 0.5s/200k+ TPS —— [43]
- Cordial Miners 用 blocklace,弃用 RBC,good-case 延迟由 4 降至 3 —— [42]
- uncertified DAG 暴露新攻击面:Adelie 指出 Mysticeti 的 uncertified DAG 引入 certified DAG 中不存在的 Byzantine 攻击向量 —— [45]
- Mahi-Mahi:uncertified DAG 减少消息数与证书验证 CPU 开销 —— [44]
- 认证 = Reliable Broadcast,提供非等价性 + 可用性;Bracha RBC 两阶段、O(n²) 消息 —— [5],[9]
- 可用性的物理性:AVID 用纠删码实现可验证信息分散 —— [6];DispersedLedger 解耦下载与排序 —— [47]
- 等价(equivocation)与问责:Polygraph 检测等价需 Ω(n) 轮额外日志 —— [51]
