"""
dag_bft_model.py
================
DAG-based BFT 共识中 certified vs uncertified 的成本模型与 Monte Carlo 仿真。

本模块实现论文《认证之为结构》第 7.2 节的解析成本模型:

    净延迟优势 ≈ Δ_save − ρ · Δ_recover

并提供一个 Monte Carlo 仿真,把该闭式模型展开为逐轮随机过程,
从而额外给出净优势的"分布"(闭式模型只给均值)。

重要声明
--------
本仿真是论文【自身解析模型】的数值图示(numerical illustration),
*不是* 对任何真实协议(Bullshark、Mysticeti 等)的实测。
所有参数(Δ_save、Δ_recover、ρ)以"消息延迟数(message delays)"为单位,
取值为说明性区间,用于揭示三个变量之间的定性关系,而非预测真实系统性能。

单位约定
--------
- Δ_save     : uncertified 版本每轮相对 certified 版本节省的延迟(省去 RBC 相关通信步)
- Δ_recover  : 可用性补偿机制(reconciliation)每次触发引入的额外延迟
- ρ          : 补偿机制被触发的频率 / 概率,ρ ∈ [0, 1]

运行
----
    python dag_bft_model.py
将打印若干参数点的解析值与仿真值对照。
"""

from __future__ import annotations
import numpy as np


# --------------------------------------------------------------------------
# 1. 解析模型(论文第 7.2 节)
# --------------------------------------------------------------------------
def net_advantage_analytic(rho, delta_save, delta_recover):
    """闭式净延迟优势:Δ_save − ρ·Δ_recover。

    返回值 > 0 表示 uncertified 占优;< 0 表示优势被补偿成本反向吞噬。
    rho 可为标量或 numpy 数组。
    """
    rho = np.asarray(rho, dtype=float)
    return delta_save - rho * delta_recover


def rho_star(delta_save, delta_recover):
    """临界恢复频率 ρ*:净优势恰为零之处(论文第 7.2 节)。

    ρ* = Δ_save / Δ_recover。当 ρ > ρ* 时 uncertified 的延迟优势消失。
    """
    return delta_save / delta_recover


# --------------------------------------------------------------------------
# 2. Monte Carlo 仿真:把闭式模型展开为逐轮随机过程
# --------------------------------------------------------------------------
def simulate_net_advantage(rho, delta_save, delta_recover,
                           n_rounds=2000, n_trials=500, seed=0):
    """对一段 DAG-BFT 执行做 Monte Carlo 仿真。

    每一轮:
      - uncertified 版本相对 certified 版本节省 Δ_save;
      - 以概率 ρ 发生一次数据缺失事件,触发 reconciliation,额外支付 Δ_recover。
    每条 trial 取 n_rounds 轮的逐轮净优势均值;返回 n_trials 条 trial 的结果数组。

    仿真均值会收敛到 net_advantage_analytic,但仿真额外给出方差信息
    (对应论文第 9 章指出的"简化模型忽略了排队与相互干扰"这一局限)。
    """
    rng = np.random.default_rng(seed)
    out = np.empty(n_trials, dtype=float)
    for t in range(n_trials):
        triggered = rng.random(n_rounds) < rho           # 每轮是否触发补偿
        per_round = delta_save - triggered * delta_recover
        out[t] = per_round.mean()
    return out


def summary(rho, delta_save, delta_recover, **kw):
    """返回某参数点的解析值、仿真均值、仿真标准差。"""
    sim = simulate_net_advantage(rho, delta_save, delta_recover, **kw)
    return {
        "rho": rho,
        "delta_save": delta_save,
        "delta_recover": delta_recover,
        "analytic": float(net_advantage_analytic(rho, delta_save, delta_recover)),
        "sim_mean": float(sim.mean()),
        "sim_std": float(sim.std()),
        "rho_star": rho_star(delta_save, delta_recover),
    }


# --------------------------------------------------------------------------
# 3. 命令行自检:打印解析值 vs 仿真值对照
# --------------------------------------------------------------------------
if __name__ == "__main__":
    DELTA_SAVE = 2.0          # uncertified 每轮节省约 2 个消息延迟
    print("DAG-BFT 成本模型 — 解析值与 Monte Carlo 仿真对照")
    print("(单位:消息延迟数;Δ_save = %.1f)" % DELTA_SAVE)
    print("-" * 72)
    print(f"{'Δ_recover':>10} {'ρ':>6} {'ρ*':>7} {'解析净优势':>12} "
          f"{'仿真均值':>12} {'仿真std':>10}")
    print("-" * 72)
    for d_rec in (4.0, 8.0, 16.0):
        for rho in (0.0, 0.10, 0.25, 0.50):
            s = summary(rho, DELTA_SAVE, d_rec)
            print(f"{d_rec:>10.1f} {rho:>6.2f} {s['rho_star']:>7.3f} "
                  f"{s['analytic']:>12.3f} {s['sim_mean']:>12.3f} "
                  f"{s['sim_std']:>10.4f}")
    print("-" * 72)
    print("解读:ρ 超过 ρ* 后解析净优势转负 —— uncertified 的延迟优势被")
    print("      补偿机制的摊销成本反向吞噬。仿真均值收敛到解析值,验证模型自洽。")
