"""
experiments —— 扫参实验(实施计划 §4.7 步骤 1.7)。

沿延迟离散度 sigma 扫参(建模论文 §7.4–§7.5 的网络退化),产出论文
§7.2 图 1 / §7.6 图 2 的仿真实测版。ρ 与 Δ_recover 在本模型里天然耦合,
一次扫参得到一条 (ρ,Δ_recover) 操作轨迹;ρ、Δ_recover、Δ_save、净优势
均为每个操作点的实测量。
"""
from .sweep import SweepPoint, sweep_delay_sigma, DATA_KIND

__all__ = ["SweepPoint", "sweep_delay_sigma", "DATA_KIND"]
