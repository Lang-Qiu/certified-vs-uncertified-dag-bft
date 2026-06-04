"""
certified.py
============
certified 变体的可插拔模块(实施计划 §4.4 步骤 1.4)。

论文锚点:§2.5–§2.6 certified DAG、§4.1 认证即可靠广播、§5.5 提交路径
对照(certified 一侧)、§3.3 受控 minimal pair。

在 certified DAG 中,区块经可靠广播(RBC)认证后才可被引用:

  CertifiedCertification —— 认证模块(简化 RBC:send + echo)。验证者
      收到区块内容后向所有人广播一个 echo;收齐 2f+1 个 echo 即认为该
      区块已认证,纳入本地 DAG。这保证一个区块在能被引用之前,其内容
      已被足够多的诚实节点持有 —— 可用性在**引用前**即被强制(论文
      第 8 章深层轴的 pre-reference 端点)。代价是额外的认证延迟(echo
      往返)与 O(n²) 的 echo 通信开销。
      说明:完整 Bracha RBC 还含 ready 放大阶段以提供 totality;本步
      为无敌手的受控对照,省略 ready 阶段,留待引入拜占庭敌手时补全。

  CertifiedAvailability —— 可用性模块。RBC 已在引用前保证可用性,故
      提交、展开因果历史时无需主动 reconciliation:缺失区块的内容必将
      由 RBC 送达,只需被动等待。这笔可用性成本已在认证阶段预先、均匀
      支付 —— 与 uncertified 把成本推迟到提交、按需支付形成对照
      (论文 §5.5)。因此本模块**不**计入 reconciliation 触发。
"""
from __future__ import annotations


class CertifiedCertification:
    """RBC 认证模块:区块经 2f+1 echo 认证后才进入 DAG。"""

    name = "RBC(certified)"

    def on_content(self, validator, block) -> None:
        bid = block.id
        if bid in validator._rbc_certified or bid in validator._rbc_content:
            return                                  # 已处理
        validator._rbc_content[bid] = block
        validator.network.broadcast_echo(validator.vid, bid)   # 广播 echo
        self._try_certify(validator, bid)

    def on_echo(self, validator, from_vid, block_id) -> None:
        validator._rbc_echoes.setdefault(block_id, set()).add(from_vid)
        self._try_certify(validator, block_id)

    def _try_certify(self, validator, bid) -> None:
        """收齐内容且 echo 达 2f+1 时,认证该区块并纳入本地 DAG。"""
        if bid in validator._rbc_certified:
            return
        if bid not in validator._rbc_content:
            return                                  # 尚无内容
        if len(validator._rbc_echoes.get(bid, ())) >= validator.config.ref_threshold:
            validator._rbc_certified.add(bid)
            block = validator._rbc_content.pop(bid)
            validator.admit(block)


class CertifiedAvailability:
    """certified 可用性模块:RBC 已保证可用性,提交时只需被动等待。"""

    name = "certified"

    def recover(self, validator, block_id):
        """certified 下提交时若某区块尚未进入 DAG,只需等待 RBC 完成 ——
        不发起额外恢复请求,不占用额外带宽,不计为 reconciliation:
        这笔成本已在认证阶段预付(论文 §5.5)。
        """
        yield validator.wait_for_block(block_id)
