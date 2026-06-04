"""
equivocation.py
===============
等价攻击敌手(实施计划 §4.5 步骤 1.5)。

论文锚点:§6.2 槽位唯一性的破坏、§5.2 非等价性的事后中和。

约定 id 在 [n-n_byzantine, n) 的验证者为拜占庭。拜占庭作者每轮(r>=1)
在同一 (author, round) 槽位产生两个区块(nonce 0 与 1,id 不同),向
半数验证者出示其一、另半数出示其二 —— 这就是等价(equivocation)。

后果(由仿真观测):
  - 同一槽位在不同诚实验证者的本地 DAG 中被不同区块占据 —— 即论文
    §6.2 所述槽位唯一性的破坏;
  - uncertified 变体的提交规则必须显式中和等价(§5.2):等价槽位的
    区块不被排序,等价作者占任的锚点轮被跳过。
"""
from __future__ import annotations


class EquivocationAdversary:
    """等价攻击:指定的拜占庭验证者每轮在同一槽位产生两个区块。"""

    name = "equivocation"

    def __init__(self, n: int, n_byzantine: int):
        self.n = n
        self.n_byzantine = n_byzantine
        # 末尾 n_byzantine 个 id 为拜占庭
        self.byzantine_ids = set(range(n - n_byzantine, n))

    def is_byzantine(self, vid: int) -> bool:
        return vid in self.byzantine_ids
