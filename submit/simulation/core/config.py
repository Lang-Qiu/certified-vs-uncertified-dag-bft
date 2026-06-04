"""
config.py
=========
DAG-BFT 仿真的参数配置(实施计划 §4.1–§4.5 步骤 1.1–1.5)。

所有可调参数集中于此,便于后续步骤(扫参、回填)统一管理。
延迟分布与带宽参数后续可由阶段二真实实测标定。
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class SimConfig:
    """一次仿真运行的完整配置。"""

    # --- 验证者规模 ---
    n: int = 7                       # 验证者总数
    f: int = 2                       # 拜占庭容错上限;需满足 n >= 3f+1

    # --- 运行长度 ---
    n_rounds: int = 2000             # 推进的轮数

    # --- 协议变体(步骤 1.3 起) ---
    variant: str = "skeleton"        # skeleton | uncertified | certified

    # --- 拜占庭敌手(步骤 1.5 起) ---
    n_byzantine: int = 0             # 拜占庭验证者数;0 <= n_byzantine <= f
    adversary: str = "none"          # none | equivocation

    # --- 网络延迟分布(决策 3:指定分布) ---
    delay_dist: str = "lognormal"    # lognormal | gamma | constant
    delay_params: dict = field(      # 分布参数;延迟单位为抽象"消息延迟数"
        default_factory=lambda: {"mean": 1.0, "sigma": 0.4})

    # --- 网络非对称 / 部分同步退化(步骤 1.7;论文 §7.4–§7.5) ---
    straggler_prob: float = 0.0      # 区块投递成为"掉队者"的概率
    straggler_delay: float = 8.0     # 掉队投递额外承受的延迟

    # --- 带宽与排队(步骤 1.2) ---
    tx_service: float = 0.1          # 单个区块传输占用出口带宽的服务时间
    recovery_load: float = 0.0       # 合成恢复请求速率(每节点每时间单位);0=关闭
    recovery_service: float = 0.5    # 单个恢复请求占用出口带宽的服务时间
    echo_service: float = 0.02       # 单个 RBC echo 占用出口带宽的服务时间(certified)

    # --- 可复现性 ---
    seed: int = 0                    # 随机种子(留存规范 §2.5 要求记录)

    @property
    def ref_threshold(self) -> int:
        """每个区块须引用的上一轮区块数下限,亦即轮次推进所需的区块数:2f+1。"""
        return 2 * self.f + 1

    @property
    def quorum(self) -> int:
        """法定人数 n-f;在 n=3f+1 时即 2f+1。锚点获此数量的支持即可提交。"""
        return self.n - self.f

    @property
    def n_honest(self) -> int:
        """诚实验证者数。约定:id 在 [0, n_honest) 为诚实,其余为拜占庭。"""
        return self.n - self.n_byzantine

    def validate(self) -> None:
        """校验配置自洽。"""
        if self.n < 3 * self.f + 1:
            raise ValueError(
                f"需 n >= 3f+1,实际 n={self.n}, f={self.f}(3f+1={3*self.f+1})")
        if self.n_rounds < 1:
            raise ValueError(f"n_rounds 须 >= 1,实际 {self.n_rounds}")
        if self.variant not in ("skeleton", "uncertified", "certified"):
            raise ValueError(f"未知变体: {self.variant}")
        if not (0 <= self.n_byzantine <= self.f):
            raise ValueError(
                f"n_byzantine 须在 [0, f]={[0, self.f]},实际 {self.n_byzantine}")
        if self.adversary not in ("none", "equivocation"):
            raise ValueError(f"未知敌手: {self.adversary}")
        if self.delay_dist not in ("lognormal", "gamma", "constant"):
            raise ValueError(f"未知延迟分布: {self.delay_dist}")
        if self.tx_service <= 0:
            raise ValueError(f"tx_service 须 > 0,实际 {self.tx_service}")
        if self.recovery_load < 0:
            raise ValueError(f"recovery_load 须 >= 0,实际 {self.recovery_load}")
        if self.recovery_service < 0:
            raise ValueError(f"recovery_service 须 >= 0,实际 {self.recovery_service}")
        if self.echo_service <= 0:
            raise ValueError(f"echo_service 须 > 0,实际 {self.echo_service}")
        if not (0 <= self.straggler_prob <= 1):
            raise ValueError(f"straggler_prob 须在 [0,1],实际 {self.straggler_prob}")
        if self.straggler_delay < 0:
            raise ValueError(f"straggler_delay 须 >= 0,实际 {self.straggler_delay}")

    def as_dict(self) -> dict:
        """导出为可序列化字典,供 §2.5 留存规范的 manifest 记录。"""
        return {
            "n": self.n, "f": self.f, "n_rounds": self.n_rounds,
            "variant": self.variant,
            "n_byzantine": self.n_byzantine, "adversary": self.adversary,
            "delay_dist": self.delay_dist, "delay_params": dict(self.delay_params),
            "straggler_prob": self.straggler_prob,
            "straggler_delay": self.straggler_delay,
            "tx_service": self.tx_service, "recovery_load": self.recovery_load,
            "recovery_service": self.recovery_service, "echo_service": self.echo_service,
            "seed": self.seed,
        }
