"""
variants —— 协议变体的可插拔模块(实施计划 §4.3–§4.4)。

每个变体提供两个可插拔模块,注入到验证者:
  certification —— 区块内容到达后,以何种方式、何时进入本地 DAG;
  availability  —— 提交、展开因果历史时,缺失内容如何补偿。

这两个模块是 certified / uncertified 的唯一差别,其余配置逐项相同 ——
即论文 §3.3 的受控 minimal pair(§3.5 称其"现实中无法构造",仿真器
中则可一键切换构造)。

  uncertified —— best-effort 广播 + 提交时检查、缺失则 reconciliation
  certified   —— RBC 认证(引用前保证可用)+ 提交时被动等待
"""
from .uncertified import UncertifiedCertification, UncertifiedAvailability
from .certified import CertifiedCertification, CertifiedAvailability

__all__ = [
    "UncertifiedCertification", "UncertifiedAvailability",
    "CertifiedCertification", "CertifiedAvailability",
]
