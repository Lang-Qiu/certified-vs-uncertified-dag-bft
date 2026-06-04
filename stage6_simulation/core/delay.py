"""
delay.py
========
网络消息延迟分布(实施计划 §4.1 步骤 1.1,决策 3:指定分布)。

延迟以抽象时间单位计,可对应论文的"消息延迟数(message delays)"。
默认 lognormal —— 真实网络延迟通常右偏(少数消息显著慢于中位数),
lognormal 比常数或均匀区间更贴近这一形态。参数后续可由阶段二实测标定。
"""
from __future__ import annotations
import numpy as np


class DelayDistribution:
    """按指定分布采样单次消息投递延迟。

    支持的分布:
      - "constant"  : 固定延迟 value
      - "lognormal" : 右偏分布;以期望延迟 mean 与对数标准差 sigma 参数化
      - "gamma"     : 以 shape、scale 参数化

    所有采样均来自传入的 numpy Generator,以保证可复现性。
    """

    def __init__(self, kind: str = "lognormal",
                 params: dict | None = None,
                 rng: np.random.Generator | None = None):
        self.kind = kind
        self.params = dict(params or {})
        self.rng = rng if rng is not None else np.random.default_rng()

    def sample(self) -> float:
        """采样一次延迟(严格为正)。"""
        if self.kind == "constant":
            return float(self.params.get("value", 1.0))

        if self.kind == "lognormal":
            # 把直观的"期望延迟 mean"换算为 lognormal 的底层 mu。
            # 对 X~Lognormal(mu,sigma): E[X] = exp(mu + sigma^2/2)。
            mean = float(self.params.get("mean", 1.0))
            sigma = float(self.params.get("sigma", 0.4))
            mu = np.log(mean) - sigma ** 2 / 2.0
            return float(self.rng.lognormal(mu, sigma))

        if self.kind == "gamma":
            shape = float(self.params.get("shape", 2.0))
            scale = float(self.params.get("scale", 0.5))
            return float(self.rng.gamma(shape, scale))

        raise ValueError(f"未知延迟分布: {self.kind}")

    def __repr__(self) -> str:
        return f"DelayDistribution({self.kind}, {self.params})"
