# stage6_simulation — DAG-BFT 共识仿真器

实施计划见项目根目录 `仿真与部署_实施计划.md`。本目录是该计划**阶段一**
（SimPy 本地仿真）的代码产出。

## 进度

- [x] 步骤 1.1 — 仿真骨架（`core/`）
- [x] 步骤 1.2 — 共享带宽资源与排队（`run_queuing.py`）
- [x] 步骤 1.3 — uncertified 变体（`variants/uncertified.py`、`run_uncertified.py`）
- [x] 步骤 1.4 — certified 变体 + 受控对照（`variants/certified.py`、`run_compare.py`）
- [x] 步骤 1.5 — 等价攻击敌手（`adversary/equivocation.py`、`run_equivocation.py`）
- [x] 步骤 1.6 — 测量层（`metrics/`、`run_measure.py` → `data/`）
- [x] 步骤 1.7 — 扫参与出图（`experiments/`、`metrics/figures.py`、`run_sweep.py` → `data/figures/`）
- [x] 步骤 1.8 — 验证与回归（`run_verify.py` → `data/verification_*`）

## 结构

| 路径 | 作用 |
|---|---|
| `core/config.py` | 仿真参数：n、f、延迟分布、随机种子、轮数 |
| `core/delay.py` | 网络延迟分布（lognormal / gamma / constant，指定分布） |
| `core/block.py` | 区块与 DAG 数据结构 |
| `core/network.py` | 消息信道：按指定分布采样延迟投递区块 |
| `core/validator.py` | 验证者 simpy 进程：逐轮构造、广播、推进 |
| `core/simulation.py` | 装配、运行与结果汇总 |
| `variants/` | uncertified / certified 两变体的可插拔认证与可用性模块 |
| `adversary/equivocation.py` | 等价攻击敌手（步骤 1.5） |
| `metrics/ledger.py` | 成本台账：按不变量×情形分解（论文 §7.1） |
| `metrics/figures.py` | 步骤 1.7 出图：图 1/2 实测版（标注"仿真实测"，300dpi PNG+PDF） |
| `experiments/sweep.py` | 步骤 1.7 沿延迟离散度 sigma 扫参，实测 ρ / Δ_recover / 净优势 |
| `run_skeleton.py` | 步骤 1.1 骨架自检入口 |
| `run_measure.py` | 步骤 1.6 测量层入口 → `data/` 成本台账 |
| `run_sweep.py` | 步骤 1.7 扫参与出图入口 → `data/figures/` 图 1/2 |
| `run_verify.py` | 步骤 1.8 验证与回归入口（交叉核对 stage2 解析模型）→ `data/verification_*` |

## 环境

Python ≥ 3.9，依赖 `simpy`、`numpy`：

```
pip install simpy numpy
```

## 运行

```
cd stage6_simulation
python run_skeleton.py
```

骨架自检（步骤 1.1）：无故障、无敌手下推进 2000 轮，校验所有验证者本地 DAG 一致。

## 重要声明

本仿真服务于论文《认证之为结构：DAG-based BFT 共识中去认证的隐性代价与延迟
优势的条件性》，是其解析模型的**受控数值实验**，**不是**对任何真实协议
（Bullshark、Mysticeti 等）的实测或复现。

骨架阶段（1.1）只验证 DAG 推进的正确性；提交规则、认证机制、拜占庭敌手与
测量层在后续步骤加入。所有结果的性质（"仿真" / "真实实测"）与留存方式以
实施计划 §2.5 留存规范为准。
