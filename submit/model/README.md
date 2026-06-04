# 仿真与可视化代码包

论文《认证之为结构:DAG-based BFT 共识中去认证的隐性代价与延迟优势的条件性》
第 7–8 章的成本模型仿真与图表生成代码。

## 文件

| 文件 | 作用 |
|------|------|
| `dag_bft_model.py` | 第 7.2 节解析成本模型 + Monte Carlo 仿真;`python dag_bft_model.py` 打印解析值与仿真值对照 |
| `make_figures.py` | 生成论文 Figure 1–3;`python make_figures.py` 输出至 `figures/` |
| `figures/` | 三张图的 `.png`(预览)与 `.pdf`(LaTeX 嵌入,300 DPI) |

## 环境

Python ≥ 3.9,依赖 `numpy`、`matplotlib`。中文标签需系统中文字体(Windows 自带
Microsoft YaHei;脚本会自动探测并回退)。

## 运行

```
python dag_bft_model.py     # 模型自检:解析值 vs 仿真值
python make_figures.py      # 生成 Figure 1-3
```

## 重要声明

本代码包是论文**解析模型的数值图示**,不是对任何真实协议(Bullshark、
Mysticeti 等)的实测或复现。所有参数(Δ_save、Δ_recover、ρ)以"消息延迟数"
为单位,取说明性数值,用于揭示三个变量之间的定性关系。Figure 3 的协议定位
是按论文第 8 章深层轴框架的**定性定位**,坐标不代表实测数据。
