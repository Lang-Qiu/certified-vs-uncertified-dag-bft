# 论文提交材料包

## 论文信息

- **标题**: DAG-BFT 共识中认证机制的结构性作用：去认证设计的隐性代价与性能边界
- **英文**: The Structural Role of Certification in DAG-BFT Consensus: Hidden Costs and Performance Bounds of De-Certification
- **页数**: 43 页
- **参考文献**: 62 篇
- **图表**: 13 张图

## 目录结构

```
submit/
├── README.md                    # 本文件
│
├── paper/                       # 论文文件
│   ├── final_paper.pdf          # 最终 PDF（43 页）
│   ├── final_paper.tex          # LaTeX 源文件
│   ├── final_paper.docx         # Word 版本
│   ├── final_paper.md           # Markdown 源文件
│   ├── _paper_template.tex      # LaTeX 模板
│   ├── _build_tex.py            # Markdown → TeX 转换脚本
│   ├── _post_tex.py             # TeX 后处理脚本
│   ├── _refine.py               # 内容精炼脚本
│   └── figures/                 # 论文图片（13 张）
│       ├── figure_1_net_advantage.png/pdf
│       ├── figure_2_advantage_region.png/pdf
│       ├── figure_3_design_axis.png/pdf
│       ├── figure_4_1_payload_heterogeneity.png
│       ├── figure_5_1_logical_paths_flat.png
│       ├── figure_5_2_loss_no_pull.png
│       ├── figure_5_3_partition_dose_response.png
│       ├── figure_7_3_stability_grid.png
│       ├── figure_7_4_recover_calibration.png
│       ├── figure_7_5_certified_arm_crossover.png
│       ├── figure_7_6_rho_degradation.png
│       ├── figure_7_7_gst_jitter.png
│       ├── figure_7_8_net_asymmetry.png
│       └── make_figure_7_3.py
│
├── simulation/                  # SimPy 仿真代码（Stage 6）
│   ├── README.md                # 仿真说明
│   ├── run_skeleton.py          # 骨架仿真
│   ├── run_queuing.py           # 排队论仿真
│   ├── run_uncertified.py       # uncertified DAG 仿真
│   ├── run_compare.py           # 对比仿真
│   ├── run_equivocation.py      # 非等价性仿真
│   ├── run_measure.py           # 测量仿真
│   ├── run_sweep.py             # 参数扫描仿真
│   ├── run_verify.py            # 验证仿真
│   ├── run_calibrated_sweep.py  # 校准扫描仿真
│   ├── core/                    # 核心模块
│   │   ├── block.py             # 区块定义
│   │   ├── config.py            # 配置
│   │   ├── delay.py             # 延迟模型
│   │   ├── network.py           # 网络模型
│   │   ├── simulation.py        # 仿真引擎
│   │   └── validator.py         # 验证者模型
│   ├── adversary/               # 对手模型
│   │   └── equivocation.py      # 非等价性攻击
│   ├── variants/                # 协议变体
│   │   ├── certified.py         # certified DAG
│   │   └── uncertified.py       # uncertified DAG
│   ├── metrics/                 # 指标收集
│   │   ├── export.py            # 数据导出
│   │   ├── figures.py           # 图表生成
│   │   └── ledger.py            # 账本指标
│   ├── experiments/             # 实验编排
│   │   └── sweep.py             # 参数扫描
│   └── data/                    # 仿真数据
│       ├── cost_ledger_*.csv/json
│       ├── sweep_*.csv/json
│       ├── verification_*.json/md
│       └── figures/             # 仿真图表
│
├── deployment/                  # 真实部署实验（Stage 7）
│   ├── scripts/                 # 顶层部署脚本
│   │   ├── build_sui_image.ps1
│   │   ├── check_prereqs.ps1
│   │   ├── fetch_targets.ps1
│   │   ├── inject_netem.sh
│   │   ├── kill_validator.ps1
│   │   └── run_local_testnet.ps1
│   └── multivalidator/          # 多验证者实验
│       ├── README.md
│       ├── handoff_persistent.md
│       ├── scripts/             # 实验运行脚本（PS1/SH）
│       ├── tools/               # 分析工具（Python）
│       ├── compose/             # Docker Compose 配置
│       ├── config/              # 实验矩阵配置（YAML）
│       ├── tests/               # 测试用例
│       ├── reports/             # 实验报告（~25 个 MD 文件）
│       ├── figures/             # 部署实验图表
│       ├── paper_integration_prep/  # 论文集成准备文档
│       ├── data/
│       │   ├── manifests/       # 环境快照与留存清单
│       │   └── runs/            # 汇总 CSV（22 个摘要文件）
│       └── ...
│
├── calibration/                 # 跨协议校准实验（Stage 9）
│   ├── *.md                     # 实验报告与结果文档（13 个）
│   ├── scripts/                 # Python 分析脚本（11 个）+ PS1 扫描脚本（17 个）
│   ├── figures/                 # 校准图表（15 PDF + 15 PNG + 3 PNG）
│   ├── config/                  # 实验配置（YAML）
│   └── docker/                  # Docker 构建文件
│
├── model/                       # 形式化模型（Stage 2）
│   └── dag_bft_model.py         # DAG-BFT 数学模型
│
└── docs/                        # 关键文档
    ├── integrity_report.md      # 完整性审查报告
    ├── final_integrity_report.md
    ├── round4_backfill_integrity_report.md
    ├── editorial_decision.md    # 编辑决定
    └── response_to_reviewers.md # 审稿回复
```

## 关键数据文件说明

### 部署实验汇总 CSV（submit/deployment/multivalidator/data/runs/）

| 文件 | 对应论文章节 | 说明 |
|------|-------------|------|
| `payload_size_summary.csv` | §4.5 图 4-1 | 区块负载异质性实验 |
| `chapter5_enforcement_summary.csv` | §5.2-5.3 图 5-1 | 逻辑型路径开销实验 |
| `partition_grid_summary.csv` | §5.4 图 5-2/5-3 | 网络分区剂量响应实验 |
| `rho_scan_summary.csv` | §7.3 图 7-6 | 恢复频率 ρ 扫描实验 |
| `rho_spacing_summary.csv` | §7.3 | 恢复间距实验 |
| `gst_jitter_summary.csv` | §7.4 图 7-7 | sub-critical GST 抖动实验 |
| `net_asymmetry_summary.csv` | §7.5 图 7-8 | 非对称网络实验 |
| `phaseA_criticalpath_summary.csv` | §7.6.1 | n=7 关键路径故障实验 |
| `phaseA_criticalpath_n4_summary.csv` | §7.6.1 | n=4 关键路径故障实验 |
| `phase2c_excess_sweep_summary.csv` | §7.6.3 图 7-5 | certified 对照臂 excess 扫描 |
| `phase1b_dsave_calibration_summary.csv` | §7.6.3 | Δ_save 标定实验 |
| `formal_matrix_summary_*.csv` | §7.3 | 正式实验矩阵汇总 |

### 仿真数据（submit/simulation/data/）

| 文件 | 说明 |
|------|------|
| `cost_ledger_20260522_013422.csv` | 仿真成本账本 |
| `sweep_20260522_122807.csv` | 参数扫描结果 |

## 编译说明

### 前提条件

- TeX 发行版（MiKTeX 或 TeX Live）
- XeLaTeX 引擎（支持中文 CTeX 字体集）
- Windows 字体：SimSun、SimHei、KaiTi、Consolas

### 编译命令

```bash
cd paper/
xelatex -interaction=nonstopmode final_paper.tex
xelatex -interaction=nonstopmode final_paper.tex  # 第二遍修正交叉引用
xelatex -interaction=nonstopmode final_paper.tex  # 第三遍稳定
```

## 仿真复现

```bash
cd simulation/
pip install simpy numpy matplotlib
python run_sweep.py              # 运行参数扫描
python run_calibrated_sweep.py   # 运行校准扫描
python run_verify.py             # 运行验证
```

## 部署实验复现

前提：Docker Desktop 运行中，Sui 镜像已构建。

```bash
cd deployment/multivalidator/
# 查看实验矩阵
cat config/experiment_matrix.yaml
# 运行实验（需要 PowerShell）
./scripts/run_experiment_matrix.ps1
# 分析结果
python tools/summarize_runs.py
```

## AI 使用声明

本文的结构组织和实验脚本撰写使用了大语言模型辅助。研究论点、核心论证（包括第 6 章必要性论证与第 8 章深层轴的提出）与最终判断由作者负责并确认。全部参考文献经独立检索核验。
