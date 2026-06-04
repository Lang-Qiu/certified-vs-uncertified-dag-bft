"""
adversary —— 拜占庭敌手模型(实施计划 §4.5 步骤 1.5)。

每个敌手类描述一种拜占庭行为。当前实现:

  EquivocationAdversary —— 等价攻击:拜占庭作者在同一 (author, round)
      槽位产生两个不同区块,向不同验证者出示不同区块。

后续迭代(本模块的兄弟类,接口预留):
  - 引用但不提供内容(推高 uncertified 的 ρ);
  - 晚绑定排序操纵(post-commit enforcement 下的 MEV 攻击面)。
"""
from .equivocation import EquivocationAdversary

__all__ = ["EquivocationAdversary"]
