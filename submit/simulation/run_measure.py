"""
run_measure.py
==============
阶段一 步骤 1.6 测量层入口。

运行三次受控仿真,把测得的量组织成按不变量与情形分解的成本台账
(论文 §7.1),并按 §2.5 留存规范导出到 data/:

  uncertified  无敌手  —— 良好情形:Δ_save、ρ、Δ_recover
  certified    无敌手  —— 良好情形:RBC echo 开销、每轮延迟
  uncertified  等价攻击 —— 故障情形:非等价性中和开销

验收标准(实施计划 §4.6):能导出每次运行的成本台账 CSV/JSON,
字段含回填追溯标记(paper_ref + data_kind)。

运行:
    cd stage6_simulation
    python run_measure.py
"""
from dataclasses import replace
from pathlib import Path

from core import SimConfig, run_simulation
from metrics import CostLedger, export_ledger


def main() -> int:
    base = SimConfig(n=7, f=2, n_rounds=2000, seed=0)

    print("=" * 64)
    print("测量层:成本台账导出 — 阶段一 步骤 1.6")
    print("=" * 64)
    print(f"共享配置: n={base.n}  f={base.f}  轮数={base.n_rounds}  种子={base.seed}")
    print("运行三次受控仿真(uncertified良好 / certified良好 / uncertified等价)...")

    cfg_unc = replace(base, variant="uncertified")
    cfg_cer = replace(base, variant="certified")
    cfg_fault = replace(base, variant="uncertified",
                        adversary="equivocation", n_byzantine=1)

    unc = run_simulation(cfg_unc)
    cer = run_simulation(cfg_cer)
    unc_fault = run_simulation(cfg_fault)
    print("-" * 64)

    ledger = CostLedger.from_runs(unc, cer, unc_fault)
    ledger.print_table()
    print()
    print("-" * 64)

    configs = {
        "uncertified_良好": cfg_unc.as_dict(),
        "certified_良好": cfg_cer.as_dict(),
        "uncertified_等价攻击": cfg_fault.as_dict(),
    }
    paths = export_ledger(ledger, configs, out_dir="data")
    print("成本台账已按 §2.5 留存规范导出至 data/:")
    for p in paths:
        print(f"  · {p.name}")
    print(f"  · 留存清单.md(汇总索引)")

    # --- 自检 ---
    print("-" * 64)
    has_rows = len(ledger.rows) > 0
    traceable = all(r["paper_ref"] and r["data_kind"] for r in ledger.rows)
    files_ok = all(Path(p).exists() for p in paths)
    inventory_ok = (Path("data") / "留存清单.md").exists()

    checks = [
        ("成本台账非空", has_rows),
        ("每行均含回填追溯标记(paper_ref + data_kind)", traceable),
        ("CSV / JSON / manifest 均已写出", files_ok),
        ("留存清单.md 已生成", inventory_ok),
    ]
    for label, ok in checks:
        print(f"[检查] {label:<38}: {'通过' if ok else '失败'}")
    print("-" * 64)
    ok = all(c for _, c in checks)
    print(f"步骤 1.6 测量层自检: {'全部通过 ✓' if ok else '未通过 ✗'}")
    print()
    print("说明:成本台账按不变量(非等价性 / 数据可用性 / 因果历史完整性)")
    print("      与情形(良好 / 故障)分解,Δ_save、ρ、Δ_recover 均为实测;")
    print("      每行 paper_ref 标注 §2.4 映射表落点,可直接用于阶段三回填。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
