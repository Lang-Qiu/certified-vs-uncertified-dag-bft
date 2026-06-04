"""
network.py
==========
消息信道与共享带宽资源(实施计划 §4.1 步骤 1.1 + §4.2 步骤 1.2)。

步骤 1.1:把区块从作者投递到每个验证者,每次投递独立采样网络延迟。

步骤 1.2:把每个节点的出口带宽建模为一个 simpy 共享资源(容量 1 = 串行
链路)。区块传输与(合成的)恢复请求竞争同一资源 —— **排队延迟与相互
干扰由此自动涌现,无需显式公式建模**。这正面回应论文 §9「成本模型忽略
排队与相互干扰」与 §7.4 拥塞反馈。

合成恢复负载是步骤 1.2 的验证手段:真实 reconciliation 机制将在步骤 1.3
随 uncertified 变体接入,届时真实恢复请求取代这里的合成负载。
"""
from __future__ import annotations
import numpy as np
import simpy

from .block import Block
from .delay import DelayDistribution
from .config import SimConfig


class Network:
    """全连接消息信道 + 每节点出口带宽资源。"""

    def __init__(self, env: simpy.Environment, delay_dist: DelayDistribution,
                 config: SimConfig, rng: np.random.Generator):
        self.env = env
        self.delay = delay_dist
        self.config = config
        self.rng = rng

        self.validators: list = []
        self._by_id: dict[int, object] = {}
        self.egress: dict[int, simpy.Resource] = {}   # vid -> 出口带宽资源

        # 全局区块登记表:记录每个广播过的区块内容。
        # reconciliation 在恢复缺失区块时由此取得内容(模拟向持有该区块的
        # peer 索取)。无敌手情形下登记表必含被引用的区块。
        self.block_registry: dict = {}                # BlockId -> Block
        # 每个 (author,round) 槽位被广播过的区块 id 集合。验证者据此判定
        # 槽位是否被等价 —— 这建模"等价证据在 gossip 型 uncertified DAG
        # 中终将完全传播给所有诚实验证者",故各验证者判定一致;本仿真
        # 不刻画检测延迟(该简化见步骤 1.5 说明)。
        self.slot_ids: dict = {}                      # (author,round) -> {BlockId}

        # 统计
        self.msg_count = 0                  # 跨节点投递数(区块 + echo)
        self.echo_count = 0                 # 其中 RBC echo 投递数(certified)
        self.tx_queue_wait: list[float] = []        # 区块传输在出口带宽的排队等待
        self.recovery_queue_wait: list[float] = []  # 合成恢复请求的排队等待
        self.recovery_jobs = 0

        # 收尾同步:全部验证者完成后触发,用于停止合成负载生成器
        self._done_count = 0
        self.done_event = env.event()

    # ------------------------------------------------------------------
    # 登记与生命周期
    # ------------------------------------------------------------------
    def register(self, validator) -> None:
        """登记一个验证者并为其创建出口带宽资源。须在仿真启动前完成。"""
        self.validators.append(validator)
        self._by_id[validator.vid] = validator
        self.egress[validator.vid] = simpy.Resource(self.env, capacity=1)

    def notify_done(self) -> None:
        """验证者在 run() 结束时回调;全部完成则触发 done_event。"""
        self._done_count += 1
        if (self._done_count == len(self.validators)
                and not self.done_event.triggered):
            self.done_event.succeed()

    def start_load_generators(self) -> None:
        """启动合成恢复负载生成器(若 recovery_load>0)。须在全部 register 后调用。"""
        if self.config.recovery_load > 0:
            for v in self.validators:
                self.env.process(self._recovery_load_gen(v.vid))

    # ------------------------------------------------------------------
    # 广播与传输
    # ------------------------------------------------------------------
    def _register(self, block: Block) -> None:
        """登记一个区块的内容与其槽位 id(供 reconciliation 与等价判定)。"""
        self.block_registry[block.id] = block
        self.slot_ids.setdefault((block.author, block.round), set()).add(block.id)

    def broadcast(self, block: Block) -> None:
        """作者把一个区块广播给所有验证者。"""
        self._register(block)                            # 登记内容与槽位 id
        self._by_id[block.author].receive(block)        # 作者立即拥有自己的区块
        self.env.process(self._transmit(block))         # 出口带宽传输(独立进程)

    def broadcast_split(self, block_x: Block, block_x2: Block) -> None:
        """等价广播(步骤 1.5):拜占庭作者把两个等价区块分别发给半数验证者。

        偶数 id 的验证者收到 block_x,奇数 id 的收到 block_x2;作者两者皆持。
        诚实验证者据此在同一槽位看到不同区块 —— 论文 §6.2 槽位唯一性破坏。
        """
        self._register(block_x)
        self._register(block_x2)
        author = self._by_id[block_x.author]
        author.receive(block_x)
        author.receive(block_x2)                         # 作者两个等价区块皆持
        self.env.process(self._transmit_split(block_x, block_x2))

    def _transmit_split(self, block_x: Block, block_x2: Block):
        """占用作者出口带宽,再按 id 奇偶把两个等价区块分发给各 peer。"""
        egress = self.egress[block_x.author]
        with egress.request() as req:
            yield req
            yield self.env.timeout(self.config.tx_service)
        for v in self.validators:
            if v.vid == block_x.author:
                continue
            block = block_x if v.vid % 2 == 0 else block_x2
            self.env.process(self._deliver(v, block, self._peer_delay()))
            self.msg_count += 1

    def _transmit(self, block: Block):
        """占用作者出口带宽完成一次传输,再向各 peer 以传播延迟投递。

        出口带宽是共享资源:本传输可能排在该节点其他传输/恢复请求之后。
        排队等待时长被记录,用于观测拥塞。
        """
        egress = self.egress[block.author]
        t0 = self.env.now
        with egress.request() as req:
            yield req
            self.tx_queue_wait.append(self.env.now - t0)     # 排队等待
            yield self.env.timeout(self.config.tx_service)   # 占用链路(服务时间)
        # 传输完成,向每个 peer 以独立采样的传播延迟投递
        for v in self.validators:
            if v.vid != block.author:
                self.env.process(self._deliver(v, block, self._peer_delay()))
                self.msg_count += 1

    def _peer_delay(self) -> float:
        """采样一次区块投递延迟。以 straggler_prob 的概率,这次投递成为
        "掉队者",额外承受 straggler_delay —— 建模网络非对称 / 部分同步
        退化(论文 §7.4–§7.5):掉队区块在提交时往往尚未送达,从而触发
        reconciliation,推高频率 ρ。"""
        d = self.delay.sample()
        if (self.config.straggler_prob > 0
                and self.rng.random() < self.config.straggler_prob):
            d += self.config.straggler_delay
        return d

    def _deliver(self, validator, block: Block, delay: float):
        """延迟 delay 后把区块交付给一个验证者。"""
        yield self.env.timeout(delay)
        validator.receive(block)

    # ------------------------------------------------------------------
    # RBC echo 消息(仅 certified 变体)
    # ------------------------------------------------------------------
    def broadcast_echo(self, from_vid: int, block_id) -> None:
        """某验证者对一个区块广播 RBC echo。echo 同样占用出口带宽 ——
        n 个验证者各对每个区块 echo 一次,即 O(n²) 的认证通信开销。"""
        self._by_id[from_vid].receive_echo(from_vid, block_id)   # 自己的 echo 立即计入
        self.env.process(self._transmit_echo(from_vid, block_id))

    def _transmit_echo(self, from_vid: int, block_id):
        """占用 echo 发起方出口带宽,再向各 peer 投递 echo。"""
        egress = self.egress[from_vid]
        with egress.request() as req:
            yield req
            yield self.env.timeout(self.config.echo_service)
        for v in self.validators:
            if v.vid != from_vid:
                self.env.process(self._deliver_echo(v, from_vid, block_id))
                self.msg_count += 1
                self.echo_count += 1

    def _deliver_echo(self, validator, from_vid: int, block_id):
        yield self.env.timeout(self.delay.sample())
        validator.receive_echo(from_vid, block_id)

    # ------------------------------------------------------------------
    # 合成恢复负载(步骤 1.2 验证用;步骤 1.3 起由真实 reconciliation 取代)
    # ------------------------------------------------------------------
    def _recovery_load_gen(self, vid: int):
        """以 Poisson 速率产生恢复请求,与正常广播竞争同一出口带宽。"""
        rate = self.config.recovery_load
        while True:
            interval = self.env.timeout(self.rng.exponential(1.0 / rate))
            yield interval | self.done_event
            if self.done_event.triggered:
                break
            self.env.process(self._recovery_job(vid))

    def _recovery_job(self, vid: int):
        """一个恢复请求:占用该节点出口带宽 recovery_service 时间。"""
        egress = self.egress[vid]
        t0 = self.env.now
        with egress.request() as req:
            yield req
            self.recovery_queue_wait.append(self.env.now - t0)
            self.recovery_jobs += 1
            yield self.env.timeout(self.config.recovery_service)
