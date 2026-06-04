"""
block.py
========
区块与 DAG 数据结构(实施计划 §4.1 步骤 1.1)。

DAG 共识中,每个区块由某验证者在某轮构造,并引用上一轮的若干区块;
这些引用关系织成有向无环图。骨架阶段每个 (author, round) 槽位至多
一个区块;`nonce` 字段是步骤 1.5 等价攻击的预留扩展位 —— 拜占庭作者
可对同一槽位产生多个 nonce 不同的区块。
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class BlockId:
    """区块的唯一标识。诚实区块 nonce 恒为 0;等价区块以 nonce 区分。"""
    author: int
    round: int
    nonce: int = 0


@dataclass
class Block:
    """一个 DAG 区块。"""
    author: int               # 作者验证者 id
    round: int                # 轮次
    refs: tuple               # tuple[BlockId, ...]:引用的上一轮区块
    nonce: int = 0            # 等价区分位;诚实区块恒为 0

    @property
    def id(self) -> BlockId:
        return BlockId(self.author, self.round, self.nonce)

    def __repr__(self) -> str:
        tag = f"#{self.nonce}" if self.nonce else ""
        return f"Block(v{self.author},r{self.round}{tag},refs={len(self.refs)})"
