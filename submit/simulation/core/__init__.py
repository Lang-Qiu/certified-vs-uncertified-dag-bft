"""
core —— DAG-BFT 仿真器骨架(实施计划阶段一 步骤 1.1)。

对外导出仿真的装配与运行入口,以及核心数据结构。
"""
from .config import SimConfig
from .delay import DelayDistribution
from .block import Block, BlockId
from .network import Network
from .validator import Validator
from .simulation import build_simulation, run_simulation, SimResult

__all__ = [
    "SimConfig", "DelayDistribution", "Block", "BlockId",
    "Network", "Validator", "build_simulation", "run_simulation", "SimResult",
]
