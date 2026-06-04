"""
simulation.py
=============
仿真组装与运行(实施计划 §4.1–§4.5 步骤 1.1–1.5)。

build_simulation: 按配置装配 env、网络、验证者;注入可插拔模块、标记
                  拜占庭验证者,并为诚实验证者启动 commit_loop。
run_simulation:   运行并返回 SimResult。
SimResult:        汇总结果,提供正确性自检与提交 / reconciliation /
                  等价中和统计。
"""
from __future__ import annotations
import numpy as np
import simpy

from .config import SimConfig
from .delay import DelayDistribution
from .network import Network
from .validator import Validator


def _make_variant(variant: str):
    """按变体返回可插拔模块二元组 (certification, availability)。"""
    if variant == "skeleton":
        from variants.uncertified import UncertifiedCertification
        return UncertifiedCertification(), None
    if variant == "uncertified":
        from variants.uncertified import (UncertifiedCertification,
                                          UncertifiedAvailability)
        return UncertifiedCertification(), UncertifiedAvailability()
    if variant == "certified":
        from variants.certified import (CertifiedCertification,
                                        CertifiedAvailability)
        return CertifiedCertification(), CertifiedAvailability()
    raise ValueError(f"未知变体: {variant}")


def build_simulation(config: SimConfig):
    """按配置装配一次仿真。返回 (env, network, validators)。"""
    config.validate()
    rng = np.random.default_rng(config.seed)

    env = simpy.Environment()
    delay = DelayDistribution(config.delay_dist, config.delay_params, rng)
    network = Network(env, delay, config, rng)

    validators = [Validator(env, i, config, network) for i in range(config.n)]
    for v in validators:
        network.register(v)

    # 敌手:标记拜占庭验证者
    byzantine_ids: set = set()
    if config.adversary == "equivocation" and config.n_byzantine > 0:
        from adversary.equivocation import EquivocationAdversary
        byzantine_ids = EquivocationAdversary(config.n,
                                              config.n_byzantine).byzantine_ids

    certification, availability = _make_variant(config.variant)
    for v in validators:
        v.certification = certification
        v.availability = availability
        v.is_byzantine = v.vid in byzantine_ids
        env.process(v.run())                          # 数据传播进程
        # 诚实验证者运行共识排序;拜占庭验证者不运行
        if config.variant != "skeleton" and not v.is_byzantine:
            env.process(v.commit_loop())

    network.start_load_generators()
    return env, network, validators


def run_simulation(config: SimConfig) -> "SimResult":
    """运行一次仿真直至所有事件耗尽,返回结果。"""
    env, network, validators = build_simulation(config)
    env.run()
    return SimResult(config, env, network, validators)


def _mean(xs) -> float:
    return float(np.mean(xs)) if len(xs) else 0.0


class SimResult:
    """一次仿真的结果汇总。"""

    def __init__(self, config: SimConfig, env: simpy.Environment,
                 network: Network, validators: list):
        self.config = config
        self.end_time = env.now
        self.msg_count = network.msg_count
        self.echo_count = network.echo_count
        self.validators = validators
        self.honest = [v for v in validators if v.vid < config.n_honest]

        self.final_rounds = [v.final_round for v in validators]
        self.blocks_produced = sum(v.blocks_produced for v in validators)
        self.round_latency = self.end_time / config.n_rounds

        # 排队统计(步骤 1.2)
        self.tx_queue_wait_mean = _mean(network.tx_queue_wait)
        self.tx_queue_wait_max = max(network.tx_queue_wait, default=0.0)
        self.recovery_queue_wait_mean = _mean(network.recovery_queue_wait)
        self.recovery_jobs = network.recovery_jobs

        # 提交与 reconciliation 统计(步骤 1.3–1.4),仅就诚实验证者
        self.committed_lens = [len(v.committed_order) for v in self.honest]
        self.committed_anchors = [v.committed_anchors for v in self.honest]
        self.skipped_anchors = [v.skipped_anchors for v in self.honest]
        self.recon_triggers = sum(v.recon_triggers for v in self.honest)
        _rt = self.recon_triggers
        _rl = sum(v.recon_latency_total for v in self.honest)
        self.recon_latency_mean = (_rl / _rt) if _rt else 0.0

        # 等价中和统计(步骤 1.5)
        self.neutralized_anchors = sum(v.neutralized_anchors for v in self.honest)
        self.neutralized_blocks = sum(v.neutralized_blocks for v in self.honest)
        self.equivocated_slot_count = sum(1 for ids in network.slot_ids.values()
                                          if len(ids) >= 2)

    # ------------------------------------------------------------------
    # 正确性判据
    # ------------------------------------------------------------------
    @property
    def all_advanced(self) -> bool:
        return all(fr == self.config.n_rounds for fr in self.final_rounds)

    def dag_consistent(self) -> bool:
        """诚实验证者的规范 DAG 是否完全一致(无敌手时应成立)。"""
        ref = self.honest[0]
        for v in self.honest[1:]:
            if v.dag.keys() != ref.dag.keys():
                return False
            for rnd, ref_slot in ref.dag.items():
                if {a: b.id for a, b in v.dag[rnd].items()} \
                        != {a: b.id for a, b in ref_slot.items()}:
                    return False
        return True

    def order_consistent(self) -> bool:
        """诚实验证者的全序应互为前缀(进度可不同,已提交部分须一致)。"""
        orders = sorted((v.committed_order for v in self.honest), key=len)
        longest = orders[-1]
        return all(o == longest[:len(o)] for o in orders)

    def canonical_disagreements(self) -> int:
        """诚实验证者规范 DAG 中同一槽位被不同区块占据的槽位数(§6.2)。"""
        count = 0
        rounds: set = set()
        for v in self.honest:
            rounds |= v.dag.keys()
        for rnd in rounds:
            authors: set = set()
            for v in self.honest:
                authors |= v.dag.get(rnd, {}).keys()
            for a in authors:
                ids = {v.dag[rnd][a].id for v in self.honest
                       if a in v.dag.get(rnd, {})}
                if len(ids) >= 2:
                    count += 1
        return count

    def equivocated_slots(self) -> int:
        """被等价的槽位数(某槽位被广播过 >= 2 个不同区块)。"""
        return self.equivocated_slot_count

    def passed(self) -> bool:
        """该次运行是否通过全部正确性判据。"""
        ok = self.all_advanced
        if self.config.variant == "skeleton":
            return ok and self.dag_consistent()
        ok = ok and self.order_consistent()
        if self.config.n_byzantine == 0:
            ok = ok and self.dag_consistent()
        return ok

    # ------------------------------------------------------------------
    # 报告
    # ------------------------------------------------------------------
    def report(self) -> bool:
        advanced = self.all_advanced
        fr_min, fr_max = min(self.final_rounds), max(self.final_rounds)
        adversarial = self.config.n_byzantine > 0

        print(f"仿真结束时刻      : {self.end_time:.2f}(抽象时间单位)")
        print(f"每轮平均推进延迟  : {self.round_latency:.4f}")
        print(f"区块产出总数      : {self.blocks_produced}")
        print(f"验证者推进轮次    : 全部到达 {fr_min}"
              if fr_min == fr_max else
              f"验证者推进轮次    : {fr_min} ~ {fr_max}(不一致!)")

        checks = [(f"全部推进至 {self.config.n_rounds} 轮", advanced)]

        if self.config.variant != "skeleton":
            cmin, cmax = min(self.committed_lens), max(self.committed_lens)
            print(f"诚实验证者数      : {len(self.honest)}  "
                  f"拜占庭: {self.config.n_byzantine}")
            print(f"已提交区块数      : {cmin} ~ {cmax}")
            print(f"reconciliation    : 触发 {self.recon_triggers} 次"
                  f"  平均 Δ_recover = {self.recon_latency_mean:.3f}")
            checks.append(("所有诚实验证者全序一致", self.order_consistent()))

            if adversarial:
                eq_slots = self.equivocated_slots()
                disagree = self.canonical_disagreements()
                print(f"等价攻击          : 检出被等价槽位 {eq_slots} 个")
                print(f"槽位唯一性破坏    : 诚实验证者规范 DAG 槽位分歧 "
                      f"{disagree} 处(§6.2)")
                print(f"等价中和          : 中和锚点 {self.neutralized_anchors} 个"
                      f"、中和区块 {self.neutralized_blocks} 个(§5.2)")
                checks.append(("等价攻击已发生(检出被等价槽位)", eq_slots > 0))
                checks.append(("观测到槽位唯一性破坏(§6.2)", disagree > 0))
                checks.append(("等价中和逻辑已触发(§5.2)",
                                self.neutralized_anchors + self.neutralized_blocks > 0))
            else:
                checks.append(("所有诚实 DAG 一致", self.dag_consistent()))
                if self.config.variant == "uncertified":
                    checks.append(("reconciliation 已触发", self.recon_triggers > 0))
                elif self.config.variant == "certified":
                    checks.append(("提交时无需 reconciliation", self.recon_triggers == 0))
        else:
            checks.append(("所有诚实 DAG 一致", self.dag_consistent()))

        print("-" * 64)
        for label, ok in checks:
            print(f"[检查] {label:<34}: {'通过' if ok else '失败'}")
        print("-" * 64)
        passed = all(ok for _, ok in checks)
        tag = {"skeleton": "骨架", "uncertified": "uncertified 变体",
               "certified": "certified 变体"}[self.config.variant]
        suffix = " + 等价攻击" if adversarial else ""
        print(f"{tag}{suffix}自检: {'全部通过 ✓' if passed else '未通过 ✗'}")
        return passed
