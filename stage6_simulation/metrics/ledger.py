"""
ledger.py
=========
成本台账(实施计划 §4.6 步骤 1.6)。

论文锚点:§7.1 成本台账方法、§7.2 成本模型、§4.5 不变量的逻辑型/物理型
二分、§2.4 回填映射表。

§7.1 的记账方法:不把协议成本归结为一个标量延迟,而是逐项归因到"维持
某个不变量的某个机制",得到一个按**不变量**与**情形**(良好 / 故障)
分解的成本结构。本模块据此把仿真测得的量组织成一张成本台账,每一行
带 §2.4 映射表对应的 paper_ref 与数据性质标注(§2.5 留存规范)。
"""
from __future__ import annotations

# 数据性质标注(§2.5:诚实标注随数据走)
DATA_KIND = "仿真(解析模型的受控数值实验,非真实协议实测)"


class CostLedger:
    """按不变量与情形分解的成本台账。"""

    COLUMNS = ["invariant", "mechanism", "variant", "situation",
               "metric", "value", "unit", "paper_ref", "data_kind"]

    def __init__(self, label: str):
        self.label = label
        self.rows: list[dict] = []

    def add(self, invariant, mechanism, variant, situation,
            metric, value, unit, paper_ref) -> None:
        self.rows.append({
            "invariant": invariant, "mechanism": mechanism,
            "variant": variant, "situation": situation, "metric": metric,
            "value": ("" if value is None else value),
            "unit": unit, "paper_ref": paper_ref, "data_kind": DATA_KIND,
        })

    @classmethod
    def from_runs(cls, unc, cer, unc_fault,
                  label: str = "DAG-BFT 成本台账(uncertified vs certified)"):
        """从三次受控仿真构建成本台账:
          unc       —— uncertified,无敌手(良好情形)
          cer       —— certified,无敌手(良好情形)
          unc_fault —— uncertified,等价攻击(故障情形)
        """
        led = cls(label)
        n_eff = unc.config.n_honest * unc.config.n_rounds   # 验证者×轮 的有效计数基

        # ============ 不变量一:非等价性(逻辑型,§4.5) ============
        led.add("非等价性", "RBC echo(send+echo,O(n²))", "certified", "良好",
                "echo 消息数", cer.echo_count, "条",
                "§4.1,§5.2 / 映射表'参数标定'行")
        led.add("非等价性", "提交规则等价中和", "uncertified", "故障:等价攻击",
                "被中和锚点数", unc_fault.neutralized_anchors, "个", "§5.2,§6.2")
        led.add("非等价性", "提交规则等价中和", "uncertified", "故障:等价攻击",
                "被中和区块数", unc_fault.neutralized_blocks, "个", "§5.2,§6.2")

        # ============ 不变量二:数据可用性(物理型,§4.5) ============
        rho = unc.recon_triggers / n_eff
        led.add("数据可用性", "reconciliation(retry)", "uncertified", "良好",
                "ρ 触发频率", round(rho, 6), "次/验证者/轮",
                "§5.4,§7.2 / 映射表'参数标定'行")
        led.add("数据可用性", "reconciliation(retry)", "uncertified", "良好",
                "Δ_recover 单次恢复延迟", round(unc.recon_latency_mean, 4),
                "时间单位", "§7.2 / 映射表'参数标定'行")
        led.add("数据可用性", "RBC(引用前保证可用)", "certified", "—",
                "reconciliation 次数", cer.recon_triggers, "次",
                "§5.5(可用性成本已在认证阶段预付)")

        # ============ 不变量三:因果历史完整性(逻辑型,§4.5) ============
        led.add("因果历史完整性", "引用规则 + 提交过滤",
                "uncertified/certified", "—",
                "结构性平移(无独立运行时成本)", None, "—", "§5.3,§4.4")

        # ============ 综合:§7.2 成本模型(实测) ============
        delta_save = cer.round_latency - unc.round_latency
        delta_recover = unc.recon_latency_mean
        net_adv = delta_save - rho * delta_recover
        led.add("(综合)", "轮次推进", "uncertified", "良好",
                "每轮延迟", round(unc.round_latency, 4), "时间单位", "§7.2")
        led.add("(综合)", "轮次推进", "certified", "良好",
                "每轮延迟", round(cer.round_latency, 4), "时间单位", "§7.2")
        led.add("(综合)", "§7.2 成本模型", "对照", "良好",
                "Δ_save(certified−uncertified 每轮延迟)", round(delta_save, 4),
                "时间单位/轮", "§7.2 / 映射表 Figure 1·2 行")
        led.add("(综合)", "§7.2 成本模型", "对照", "良好",
                "净优势 = Δ_save − ρ·Δ_recover", round(net_adv, 4),
                "时间单位/轮", "§7.2,§7.6 / 映射表 Figure 2 行")
        return led

    # ------------------------------------------------------------------
    def to_csv_rows(self) -> list[list]:
        return [self.COLUMNS] + [[r[c] for c in self.COLUMNS] for r in self.rows]

    def print_table(self) -> None:
        """按不变量分组打印成本台账。"""
        print(f"成本台账:{self.label}")
        print("(按论文 §7.1 记账方法,逐项归因到维持某不变量的机制)")
        current = None
        for r in self.rows:
            if r["invariant"] != current:
                current = r["invariant"]
                print(f"\n■ {current}")
            val = r["value"] if r["value"] != "" else "—"
            print(f"  · [{r['variant']}/{r['situation']}] {r['metric']} "
                  f"= {val} {r['unit']}")
            print(f"      ↳ 回填: {r['paper_ref']}")
