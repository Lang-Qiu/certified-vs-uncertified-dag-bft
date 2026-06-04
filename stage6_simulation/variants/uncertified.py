"""
uncertified.py
==============
uncertified 变体的可插拔模块(实施计划 §4.3 步骤 1.3)。

论文锚点:§5.4 数据可用性落入「② 削弱+补偿」、§5.5 提交路径对照。

在 uncertified DAG 中,区块以 best-effort 方式广播,不经 RBC 认证:

  UncertifiedCertification —— 认证模块:区块内容一到达即进入本地 DAG,
      无认证延迟。这正是 uncertified 省下的延迟(论文的 Δ_save)。

  UncertifiedAvailability —— 可用性模块:数据可用性的保证被**弱化** ——
      不再是"区块被引用前其内容已被足够多诚实节点持有",而只是"区块
      在被提交前其内容可被恢复"。验证者在提交、展开锚点因果历史时若
      发现某祖先区块缺失,即触发 reconciliation(retry):向持有该区块
      的节点发起恢复请求 —— 占用响应方出口带宽(与正常广播竞争同一
      资源,对应论文 §7.4 拥塞反馈),经传播延迟后取得内容,提交被阻塞
      直至恢复完成。这笔成本即论文 §5.6、§7 所称的"或有负债"。
"""
from __future__ import annotations


class UncertifiedCertification:
    """best-effort 认证模块:区块内容到达即进入 DAG。"""

    name = "best-effort"

    def on_content(self, validator, block) -> None:
        validator.admit(block)

    def on_echo(self, validator, from_vid, block_id) -> None:
        pass                                    # uncertified 无 RBC echo


class UncertifiedAvailability:
    """uncertified 可用性模块:提交时检查,缺失则主动 reconciliation。"""

    name = "uncertified"

    def recover(self, validator, block_id):
        """对一个在提交时缺失的祖先区块执行 reconciliation。

        simpy 生成器:提交进程 yield from 它,被阻塞直至区块到达本地。
        """
        env = validator.env
        t0 = env.now
        validator.recon_triggers += 1

        # 发起恢复请求(占用带宽);内容可能由此恢复或由正常广播先送达
        env.process(self._fetch(validator, block_id))

        # 阻塞直至内容到达 —— 提交的正确性依赖于此(论文 §5.4)
        yield validator.wait_for_block(block_id)

        validator.recon_latency_total += env.now - t0

    def _fetch(self, validator, block_id):
        """一次恢复请求:占用响应方(区块作者)出口带宽,经传播延迟送达。"""
        env = validator.env
        net = validator.network

        with net.egress[block_id.author].request() as req:
            yield req
            yield env.timeout(validator.config.recovery_service)

        yield env.timeout(net.delay.sample())
        if not validator.has_block(block_id):
            validator.admit(net.block_registry[block_id])
