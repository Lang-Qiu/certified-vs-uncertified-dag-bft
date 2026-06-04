# 阶段三 Round 3 完成记录 —— Route A1 certified 对照臂 §7.2 标定回填

**完成时间**: 2026-05-31
**数据源**: `stage9_cross_protocol_calibration/PHASE1_RESULTS.md` + `PHASE2_RESULTS.md`（Route A1 certified-arm：Δ_save + 恢复不对称 + ρ*(Δr) crossover）
**门禁**: 逐点最小 diff 提案（`revision_diffs_round3.md`）→ 用户「全部批准，执行」→ 编辑 `final/final_paper.md`。

## 已落地的 8 处编辑（`final/final_paper.md`）

| EDIT | 章节 | 操作 | 状态 |
|---|---|---|---|
| R3-1 | §7.6.3（新增，图 7-4 之后） | 含 certified 对照臂的净优势翻转标定（4 判断：Δ_save 正、认证缩减恢复、ρ* crossover、H3 amortized 偏离）+ 图 7-5 | ✅ |
| R3-2 | §7.2 Monte Carlo 段（313） | 软化「超出本文范围」→ §7.6.3 提供部署对照标定 | ✅ |
| R3-3 | §7.2 ρ* 句（311） | 追加：§7.6.3 把 ρ* 定量定位 ~0.013–0.038 + amortized 偏离 | ✅ |
| R3-4 | §9 威胁有效性（464→478） | 改述：certified 臂已建（Route A1），剩余=真 RBC 跨引擎 benchmark | ✅ |
| R3-5 | §9 注入式旋钮（454→468） | 改述：§7.6.3 补 certified 臂；可用性证书≠密码学签名 | ✅ |
| R3-6 | §10 未来工作（478→492） | 改述：certified 臂已操作化；剩余=升级为真 RBC benchmark | ✅ |
| R3-7 | 数据可用性声明（484→498） | 追加：§7.6.3/图 7-5 工件存档于 stage9 | ✅ |
| R3-8 | figures | `phase2c_rho_star.png` → `final/figures/figure_7_5_certified_arm_crossover.png` | ✅ |

## 核心实证主张（Round 3 新增，附构念效度限定）

- **Δ_save 首次部署实测为正**：cert ON 比 OFF 慢 ≈0.116 s/commit（4.58→2.99 ckpt/s）——认证确认轮的延迟。
- **认证缩减恢复侧或有负债**：同故障同 Δ_recover 下 cert ON 恢复更廉（fetch 123 vs 196、每故障省 excess≈3–9 s，excess 随 Δr 增长 R²≈0.49）。§7.5「认证事前均摊 → 故障下恢复更鲁棒」的部署确证。
- **净优势翻转 ρ\* 首次定量定位**：ρ\* ≈ 0.013–0.038 次/commit（1 关键路径故障/26–78 commits），随 Δr 增大而下降。
- **诚实模型偏离（H3）**：amortized 直接观测非单调（R²≈0.02）——一次性恢复成本被窗口稀释 + 高 Δr gate 排斥 recovering 节点的竞争效应，印证 §7.4 的 ρ–Δ_recover 耦合；须用分解观测方能干净标定。
- **限定（强于 §7.6.2）**：可用性证书（2f+1 接受，RoundProber 通道）≠密码学 2f+1 签名；单引擎（非两协议 benchmark）；Δ_recover 注入式；ρ\* 为 band。标定的是**成本结构**，非真实协议对的绝对延迟。

## 完整性校验（已过）

- §7.6.3 唯一（line 384）；图 7-5 资产就位（112 KB）+ 引用正确（line 396）。
- 数字对账：0.116 s/commit、4.58→2.99、123 vs 196、excess 3–9 s、R²≈0.49、ρ\* 0.013–0.038、26–78、amortized R²≈0.02 与 PHASE1/PHASE2_RESULTS + CSV 一致。
- 旧表述改述：「未来工作的主要方向」=0、「以定量标定…三个参数」=0（均已移除）；§9 改述就位（line 468）。残留「无 certified 对照臂」仅在 §7.6.2（line 378，该实验确无）与 §7.6.3 历史引述（line 386）——正确无矛盾。
- 图号连续：表 7-1 → 图 7-3 → 图 7-4 → 图 7-5。
- 受保护文件 `consensus_metrics.json` 未被回填触碰（hash chain 未动）。

## 排除项（与 Round 1/2 一致）

- 摘要不再追加；§1.3/§1.5 贡献结构不改；§7.2 闭式公式与图 1/图 2 不改；不宣称 certified 绝对更优/更差；标题、章节编号、贡献结构不变。

## 论文当前状态

论文 = 理论 + 实证（**三个部署组件**）：§7.6.1（故障强度轴）+ §7.6.2（Δ_recover 关键路径标定）+ §7.6.3（certified 对照臂 §7.2 净优势翻转标定，Route A1）。§7.2 成本模型现有真实 n=7 部署的对照标定（Δ_save/认证恢复缩减/ρ* crossover），其"无 certified 臂/定量标定属未来工作"的中心限定已更新为已交付（附诚实限定）。

## 续作（仍待，非本轮）

- 把可用性证书的 certified 臂升级为含**真实 RBC 签名开销、跨两套独立引擎**的受控 benchmark（从成本结构标定 → 真实协议对绝对延迟比较）。
- 可选：更多 reps 收紧 ρ\* band（Δr=500 outlier）、n=4 跨规模 certified 臂、OFF≡stock 正式对账。
