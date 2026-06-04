"""
validator.py
============
验证者进程(实施计划 §4.1–§4.5 步骤 1.1–1.5)。

每个验证者运行两个解耦的 simpy 进程 —— DAG-BFT "数据传播与共识排序
解耦" 的体现:
  run()         —— 数据传播:逐轮构造、广播区块,推进轮次。
  commit_loop() —— 共识排序:在本地 DAG 上按确定性规则提交锚点。
                   (拜占庭验证者不运行 commit_loop。)

可插拔模块(按变体注入,构成 §3.3 受控 minimal pair):
  self.certification —— 区块内容到达后以何种方式、何时进入本地 DAG
                        (best-effort / RBC)。
  self.availability  —— 提交、展开因果历史时,缺失内容如何补偿
                        (uncertified 主动 reconciliation / certified 被动等待)。

等价攻击与中和(步骤 1.5):拜占庭作者在同一槽位产生两个区块。验证者
用 slot_ids 记录每个 (author,round) 槽位见过的全部区块 id(含内容与
引用所揭示的);某槽位 id 数 >= 2 即判定该槽位被等价。提交规则据此
中和等价(论文 §5.2):等价作者占任的锚点轮被跳过,等价槽位的区块
不进入全序。
"""
from __future__ import annotations
import simpy

from .block import Block, BlockId
from .config import SimConfig


class Validator:
    """一个验证者(诚实或拜占庭)。"""

    def __init__(self, env: simpy.Environment, vid: int,
                 config: SimConfig, network):
        self.env = env
        self.vid = vid
        self.config = config
        self.network = network

        self.is_byzantine = False       # 由 build_simulation 按敌手设置

        # 本地 DAG 的"规范视图":round -> {author -> Block},每槽位首见区块。
        # 用于区块构造、轮次推进、锚点支持计数。
        self.dag: dict[int, dict[int, Block]] = {}
        # 见过的全部区块(含等价区块、reconciliation 取回的),按完整 id 索引。
        self.seen: dict[BlockId, Block] = {}

        # 可插拔模块
        self.certification = None
        self.availability = None

        # --- RBC 状态(仅 certified 变体) ---
        self._rbc_content: dict[BlockId, Block] = {}
        self._rbc_echoes: dict[BlockId, set] = {}
        self._rbc_certified: set[BlockId] = set()

        # --- 轮次推进同步(run 用) ---
        self._quorum_round: int | None = None
        self._quorum_event: simpy.Event | None = None

        # --- 提交同步(commit_loop 用) ---
        self._commit_wait_round: int | None = None
        self._commit_wait_event: simpy.Event | None = None
        self._waiters: dict[BlockId, simpy.Event] = {}

        # --- 提交状态 ---
        self.ordered_set: set[BlockId] = set()      # 已决定(已排序或已中和)
        self.committed_order: list[BlockId] = []
        self.committed_anchors = 0
        self.skipped_anchors = 0
        self.neutralized_anchors = 0                # 因等价被中和的锚点轮
        self.neutralized_blocks = 0                 # 因等价被排除出全序的区块

        # --- 统计 ---
        self.blocks_produced = 0
        self.blocks_admitted = 0
        self.final_round = 0
        self.recon_triggers = 0
        self.recon_latency_total = 0.0

    # ==================================================================
    # 接收
    # ==================================================================
    def receive(self, block: Block) -> None:
        """区块内容到达。由认证模块决定何时进入本地 DAG。"""
        self.certification.on_content(self, block)

    def receive_echo(self, from_vid: int, block_id: BlockId) -> None:
        """RBC echo 到达(仅 certified 变体)。"""
        self.certification.on_echo(self, from_vid, block_id)

    def admit(self, block: Block) -> None:
        """把一个区块正式纳入本地视图(认证模块在时机成熟时调用)。"""
        if block.id in self.seen:               # 幂等
            return
        self.seen[block.id] = block
        slot = self.dag.setdefault(block.round, {})
        if block.author not in slot:            # 规范视图:每槽位首见区块
            slot[block.author] = block
        self.blocks_admitted += 1

        # (a) 唤醒轮次推进
        ev = self._quorum_event
        if (ev is not None and not ev.triggered
                and block.round == self._quorum_round
                and len(self.dag[self._quorum_round]) >= self.config.ref_threshold):
            ev.succeed()
        # (b) 唤醒区块等待者
        w = self._waiters.pop(block.id, None)
        if w is not None and not w.triggered:
            w.succeed()
        # (c) 唤醒 commit_loop
        self._maybe_wake_commit(block.round)

    # ==================================================================
    # 数据传播
    # ==================================================================
    def run(self):
        """验证者主循环 —— 数据传播进程。"""
        threshold = self.config.ref_threshold

        self._broadcast(0, ())                  # round 0:创世区块
        prev = 0

        for r in range(1, self.config.n_rounds + 1):
            if len(self.dag.get(prev, {})) < threshold:
                self._quorum_round = prev
                self._quorum_event = self.env.event()
                yield self._quorum_event
                self._quorum_event = None
                self._quorum_round = None

            prev_slot = self.dag[prev]
            refs = tuple(prev_slot[a].id for a in sorted(prev_slot))
            self._broadcast(r, refs)
            prev = r

        self.final_round = prev
        self.network.notify_done()

    def _broadcast(self, rnd: int, refs: tuple) -> None:
        """构造并广播本验证者在第 rnd 轮的区块。

        拜占庭验证者(r>=1)实施等价攻击:同一槽位产生两个区块。
        """
        if self.is_byzantine and rnd >= 1:
            bx = Block(self.vid, rnd, refs, nonce=0)
            bx2 = Block(self.vid, rnd, refs, nonce=1)
            self.blocks_produced += 2
            self.network.broadcast_split(bx, bx2)
        else:
            block = Block(self.vid, rnd, refs)
            self.blocks_produced += 1
            self.network.broadcast(block)

    # ==================================================================
    # 共识排序(仅诚实验证者运行)
    # ==================================================================
    def commit_loop(self):
        """共识排序进程 —— 按轮提交锚点并展开其因果历史。"""
        n = self.config.n
        for r in range(1, self.config.n_rounds):
            if not self._commit_decided(r):
                self._commit_wait_round = r
                self._commit_wait_event = self.env.event()
                yield self._commit_wait_event
                self._commit_wait_round = None
                self._commit_wait_event = None

            leader = r % n
            # 等价中和(论文 §5.2):等价作者占任的锚点轮被跳过
            if self.is_equivocated(leader, r):
                self.neutralized_anchors += 1
                self.skipped_anchors += 1
                continue

            # 确保锚点内容可得(可能尚在途中/认证中)
            anchor_id = BlockId(author=leader, round=r, nonce=0)
            if not self.has_block(anchor_id):
                yield from self.availability.recover(self, anchor_id)
            anchor = self.get_block(anchor_id)

            if self._support(r) >= self.config.quorum:
                yield from self._commit_anchor(anchor)
                self.committed_anchors += 1
            else:
                self.skipped_anchors += 1

    def _support(self, r: int) -> int:
        """第 r 轮锚点(nonce 0)获得的引用支持数。"""
        anchor_id = BlockId(author=r % self.config.n, round=r, nonce=0)
        return sum(1 for b in self.dag.get(r + 1, {}).values()
                   if anchor_id in b.refs)

    def _commit_decided(self, r: int) -> bool:
        """锚点 r 是否已可决定。"""
        if len(self.dag.get(r + 1, {})) >= self.config.n:
            return True
        return self._support(r) >= self.config.quorum

    def _maybe_wake_commit(self, block_round: int) -> None:
        cw = self._commit_wait_round
        ev = self._commit_wait_event
        if cw is None or ev is None or ev.triggered:
            return
        if block_round != cw + 1:
            return
        if self._commit_decided(cw):
            ev.succeed()

    def _commit_anchor(self, anchor: Block):
        """提交一个锚点:展开因果历史,沿途中和等价区块、补偿缺失内容,
        再把新区块按确定性顺序(round, author, nonce)追加到全序。
        """
        new: list[BlockId] = []
        seen_set: set[BlockId] = set()
        stack: list[BlockId] = [anchor.id]

        while stack:
            bid = stack.pop()
            if bid in seen_set or bid in self.ordered_set:
                continue
            seen_set.add(bid)

            # 等价中和:等价槽位的区块不进入全序,也不追随其引用
            if self.is_equivocated(bid.author, bid.round):
                self.ordered_set.add(bid)
                self.neutralized_blocks += 1
                continue

            if not self.has_block(bid):
                yield from self.availability.recover(self, bid)

            block = self.get_block(bid)
            new.append(bid)
            for ref in block.refs:
                if ref not in self.ordered_set and ref not in seen_set:
                    stack.append(ref)

        for bid in sorted(new, key=lambda b: (b.round, b.author, b.nonce)):
            self.ordered_set.add(bid)
            self.committed_order.append(bid)

    # ==================================================================
    # 查询
    # ==================================================================
    def has_block(self, bid: BlockId) -> bool:
        return bid in self.seen

    def get_block(self, bid: BlockId) -> Block:
        return self.seen[bid]

    def is_equivocated(self, author: int, rnd: int) -> bool:
        """槽位 (author,round) 是否被等价(该槽位被广播过 >= 2 个不同区块)。

        判定依据全局槽位登记(network.slot_ids):建模等价证据在 gossip 型
        uncertified DAG 中终将完全传播,故各诚实验证者判定一致 —— 这正是
        等价中和(§5.2)得以保持全序一致的前提。
        """
        return len(self.network.slot_ids.get((author, rnd), ())) >= 2

    def wait_for_block(self, bid: BlockId) -> simpy.Event:
        """返回一个事件,在某区块进入本地视图时触发(已含则立即触发)。"""
        if self.has_block(bid):
            ev = self.env.event()
            ev.succeed()
            return ev
        if bid not in self._waiters:
            self._waiters[bid] = self.env.event()
        return self._waiters[bid]
