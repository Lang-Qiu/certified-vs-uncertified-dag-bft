"""
sweep.py
========
网格扫参(实施计划 §4.7 步骤 1.7)。

论文锚点:§7.2 成本模型与图 1、§7.6 条件性延迟优势与图 2、§7.4 拥塞反馈、
§10 未来工作之二。

扫参自变量的选择
----------------
本步骤需要一个能 **单调驱动 ρ** 的旋钮,以便沿 ρ 轴出图。

曾试 straggler_prob(掉队投递概率),实测发现它对 ρ 是 **驼峰型** 而非
单调:概率过高时几乎每次投递都同样变慢,轮次推进随之同步变慢,"轮已满 /
锚点尚未到达"的时间缝隙反而闭合,ρ 回落。

亦考虑过 mean(对数正态位置参数),但抬高 mean 等于 **整体重标定时间轴**:
Δ_save、Δ_recover 同比放大,各操作点不在同一时间单位下,不可比。

故定为单一旋钮 —— sigma(对数正态尺度参数):它加大延迟 **离散度** 而
不改时间量级。轮次推进取 7 个区块里第 5 快者(低阶顺序统计量),锚点却是
其中某一特定区块;离散度越大,锚点成为迟到离群者的概率越高 → ρ 单调上升。

一个重要事实:在本模型里 ρ 与 Δ_recover **天然耦合** —— 同一个 sigma 既
推高 ρ 又推高 Δ_recover,二者不可独立设定。这一耦合本身即论文 §7.4 的
预测。因此一次 sigma 扫参得到的不是 (ρ,Δ_recover) 平面上的自由散点,而是
一条 **操作轨迹曲线**;图 2 正是把这条实测轨迹叠在 §7.6 条件性区域上。

做法
----
每个操作点用 **同一组随机种子** 各跑 uncertified / certified 两变体(§3.3
受控最小对照:除 variant 外配置全同),得到一个 trial;一个操作点跑
n_trials 个 trial(不同种子),聚合出均值与标准差。

每个 trial 实测三个量,全部来自运行而非假定(§4.6 测量层口径):

  ρ          = uncertified 的 reconciliation 触发次数 /(诚实验证者数×轮数)
  Δ_recover  = uncertified 单次 reconciliation 实测平均延迟(含排队)
  Δ_save     = certified 每轮延迟 − uncertified 每轮延迟

净优势按 §7.2 成本模型合成:净优势 = Δ_save − ρ·Δ_recover,三个分量都在
**该操作点本地实测**。
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace

import numpy as np

from core import SimConfig, run_simulation

# 数据性质标注(§2.5:诚实标注随数据走)
DATA_KIND = "仿真(解析模型的受控数值实验,非真实协议实测)"


@dataclass
class SweepPoint:
    """一个扫参操作点:给定延迟分布参数下,多 trial 聚合后的实测结果。"""
    sigma: float               # 对数正态尺度参数(自变量:驱动 ρ)
    mean: float                # 对数正态位置参数(自变量:驱动 Δ_recover)
    n_trials: int

    rho: float                 # 平均 ρ —— reconciliation 触发频率
    rho_std: float
    delta_recover: float       # 平均 Δ_recover —— 单次恢复延迟(含排队)
    delta_recover_std: float
    delta_save: float          # 平均 Δ_save —— certified−uncertified 每轮延迟
    delta_save_std: float
    net_adv: float             # 平均净优势 = Δ_save − ρ·Δ_recover
    net_adv_std: float

    unc_round_latency: float   # uncertified 平均每轮延迟
    cer_round_latency: float   # certified 平均每轮延迟
    recon_triggers: float      # uncertified 平均 reconciliation 触发次数
    all_passed: bool           # 全部 trial 的两变体均通过正确性自检
    trials: list = field(default_factory=list)   # 每个 trial 的原始 dict

    def as_row(self) -> dict:
        """导出为扁平字典,供 CSV/JSON 留存(§2.5)。"""
        return {
            "sigma": self.sigma,
            "mean": self.mean,
            "n_trials": self.n_trials,
            "rho": round(self.rho, 6),
            "rho_std": round(self.rho_std, 6),
            "delta_recover": round(self.delta_recover, 4),
            "delta_recover_std": round(self.delta_recover_std, 4),
            "delta_save": round(self.delta_save, 4),
            "delta_save_std": round(self.delta_save_std, 4),
            "net_adv": round(self.net_adv, 4),
            "net_adv_std": round(self.net_adv_std, 4),
            "unc_round_latency": round(self.unc_round_latency, 4),
            "cer_round_latency": round(self.cer_round_latency, 4),
            "recon_triggers": round(self.recon_triggers, 1),
            "all_passed": self.all_passed,
            "data_kind": DATA_KIND,
        }


def _run_trial(sigma: float, mean: float, base: SimConfig, seed: int) -> dict:
    """一个 trial:同种子下各跑 uncertified / certified,实测三个量。"""
    delay_params = {"mean": mean, "sigma": sigma}     # 每次新建,不共享引用
    cfg_unc = replace(base, variant="uncertified",
                      delay_params=dict(delay_params), seed=seed)
    cfg_cer = replace(base, variant="certified",
                      delay_params=dict(delay_params), seed=seed)

    unc = run_simulation(cfg_unc)
    cer = run_simulation(cfg_cer)

    n_eff = base.n_honest * base.n_rounds          # 验证者×轮 的有效计数基
    rho = unc.recon_triggers / n_eff
    delta_recover = unc.recon_latency_mean
    delta_save = cer.round_latency - unc.round_latency
    net_adv = delta_save - rho * delta_recover

    return {
        "seed": seed,
        "rho": rho,
        "delta_recover": delta_recover,
        "delta_save": delta_save,
        "net_adv": net_adv,
        "unc_round_latency": unc.round_latency,
        "cer_round_latency": cer.round_latency,
        "recon_triggers": unc.recon_triggers,
        "passed": unc.passed() and cer.passed(),
    }


def _aggregate(sigma: float, mean: float, trials: list) -> SweepPoint:
    """把同一操作点的多个 trial 聚合成一个 SweepPoint(均值 + 标准差)。"""
    def ms(key):
        xs = np.array([t[key] for t in trials], dtype=float)
        return float(xs.mean()), float(xs.std())

    rho_m, rho_s = ms("rho")
    drec_m, drec_s = ms("delta_recover")
    dsav_m, dsav_s = ms("delta_save")
    net_m, net_s = ms("net_adv")
    unc_m, _ = ms("unc_round_latency")
    cer_m, _ = ms("cer_round_latency")
    rec_m, _ = ms("recon_triggers")

    return SweepPoint(
        sigma=sigma, mean=mean, n_trials=len(trials),
        rho=rho_m, rho_std=rho_s,
        delta_recover=drec_m, delta_recover_std=drec_s,
        delta_save=dsav_m, delta_save_std=dsav_s,
        net_adv=net_m, net_adv_std=net_s,
        unc_round_latency=unc_m, cer_round_latency=cer_m,
        recon_triggers=rec_m,
        all_passed=all(t["passed"] for t in trials),
        trials=trials,
    )


def _measure_point(sigma: float, mean: float, base: SimConfig,
                   n_trials: int, progress=None) -> SweepPoint:
    """对一个 (sigma, mean) 操作点跑 n_trials 个 trial 并聚合。"""
    trials = []
    for seed in range(n_trials):
        trials.append(_run_trial(sigma, mean, base, seed))
        if progress is not None:
            progress()
    return _aggregate(sigma, mean, trials)


def sweep_delay_sigma(sigmas, base: SimConfig, n_trials: int = 4,
                      mean: float = 1.0, progress=None) -> list[SweepPoint]:
    """沿延迟离散度 sigma 一维扫参(图 1、图 2 共用)。

    mean 固定(时间量级不变),sigma 取 sigmas 中各值 —— 得到一串 ρ
    单调递增的操作点。返回顺序与 sigmas 输入顺序一致(便于校验 ρ 随
    sigma 单调)。

    图 1 沿 ρ 轴呈现这串点(净优势 vs ρ);图 2 把同一串点当作
    (ρ, Δ_recover) 平面上的操作轨迹,叠在 §7.6 条件性区域上。
    """
    return [_measure_point(sg, mean, base, n_trials, progress)
            for sg in sigmas]
