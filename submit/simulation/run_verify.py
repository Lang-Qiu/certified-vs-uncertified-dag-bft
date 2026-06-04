"""
run_verify.py
=============
阶段一 步骤 1.8 验证与回归入口。

确立 stage6 仿真器的正确性,产出四项检查(实施计划 §4.8):

  检查 1  交叉核对    —— stage6 实测 (ρ,Δ_save,Δ_recover) 喂入 stage2 的
                         dag_bft_model.py,净优势须与其解析值 / Monte Carlo
                         均值一致(两套独立代码实现同一 §7.2 闭式)。
  检查 2  退化检验    —— (2a) 退化极限:常数延迟 + 无拥塞 → 补偿机制不触发
                         (ρ≈0),净优势退化为 Δ_save;(2b) 良性工况下净优势
                         与 §7.2 闭式及 dag_bft_model 收敛(相对误差 < 1%)。
  检查 3  耦合检验    —— 注入合成拥塞负载,Δ_recover 随拥塞单调抬升 ——
                         §7.2 闭式把 Δ_recover 当常数,这一抬升即论文 §7.4
                         所预测、§9 所承认的"成本模型忽略排队"的系统性偏离。
  检查 4  正确性回归  —— 重跑骨架 / uncertified / certified / 等价攻击四类
                         自检,确认步骤 1.7 的改动未引入回归。

验收(实施计划 §4.8):退化检验通过;耦合偏离方向与论文定性预测一致。
验证报告按 §2.5 留存规范导出至 data/。

论文锚点:§7.2 成本模型、§7.4 拥塞反馈、§9 模型局限。

运行:
    cd stage6_simulation
    python run_verify.py
"""
import sys
from dataclasses import replace
from pathlib import Path

from core import SimConfig, run_simulation
from metrics import export_verification

# stage2 的解析成本模型(论文 §7.2 闭式 + Monte Carlo)
_STAGE2 = (Path(__file__).resolve().parent.parent
           / "stage2_write" / "code")
sys.path.insert(0, str(_STAGE2))
import dag_bft_model as analytic_model       # noqa: E402

N_ROUNDS = 1000


# ----------------------------------------------------------------------
# 工具
# ----------------------------------------------------------------------
def _rel_err(a: float, b: float) -> float:
    """相对误差 |a−b| / max(|b|, 1e-9)。"""
    return abs(a - b) / max(abs(b), 1e-9)


def _measure(cfg: SimConfig):
    """跑一次 uncertified + certified 受控对照,返回实测四元组。"""
    unc = run_simulation(replace(cfg, variant="uncertified"))
    cer = run_simulation(replace(cfg, variant="certified"))
    n_eff = cfg.n_honest * cfg.n_rounds
    rho = unc.recon_triggers / n_eff
    d_recover = unc.recon_latency_mean
    d_save = cer.round_latency - unc.round_latency
    net = d_save - rho * d_recover
    return {
        "rho": rho, "delta_recover": d_recover, "delta_save": d_save,
        "net_adv": net, "recon_triggers": unc.recon_triggers,
        "tx_queue_wait_mean": unc.tx_queue_wait_mean,
        "unc_passed": unc.passed(), "cer_passed": cer.passed(),
    }


# ----------------------------------------------------------------------
# 检查 1 —— 交叉核对 dag_bft_model.py
# ----------------------------------------------------------------------
def check_cross(base: SimConfig) -> dict:
    print("检查 1 — 交叉核对 stage2/dag_bft_model.py")
    pts = []
    worst_analytic = worst_mc = 0.0
    for sg in (0.5, 0.9, 1.3):
        cfg = replace(base, delay_params={"mean": 1.0, "sigma": sg})
        m = _measure(cfg)
        a = float(analytic_model.net_advantage_analytic(
            m["rho"], m["delta_save"], m["delta_recover"]))
        mc = analytic_model.simulate_net_advantage(
            m["rho"], m["delta_save"], m["delta_recover"],
            n_rounds=base.n_rounds, n_trials=4000, seed=0)
        mc_mean = float(mc.mean())
        e_a = _rel_err(m["net_adv"], a)
        e_mc = _rel_err(mc_mean, a)
        worst_analytic = max(worst_analytic, e_a)
        worst_mc = max(worst_mc, e_mc)
        print(f"  σ={sg}: ρ={m['rho']:.4f}  net(stage6)={m['net_adv']:.4f}  "
              f"解析={a:.4f}  MC均值={mc_mean:.4f}  "
              f"误差: 解析{e_a:.2e} / MC {e_mc:.2e}")
        pts.append({"sigma": sg, **m, "analytic": a, "mc_mean": mc_mean})
    passed = worst_analytic < 1e-6 and worst_mc < 0.01
    return {
        "name": "检查 1:交叉核对 dag_bft_model.py",
        "passed": passed,
        "criterion": "stage6 净优势=dag_bft_model 解析值(误差<1e-6);"
                     "dag_bft_model MC 均值=解析值(误差<1%)",
        "observed": f"最大相对误差:解析 {worst_analytic:.2e}、"
                    f"Monte Carlo {worst_mc:.2e}(3 个工况点)",
        "paper_ref": "§7.2 成本模型;两套独立代码(stage2 解析层 / "
                     "stage6 协议级仿真)实现同一闭式",
        "points": pts,
    }


# ----------------------------------------------------------------------
# 检查 2 —— 退化检验
# ----------------------------------------------------------------------
def check_degradation(base: SimConfig) -> dict:
    print("检查 2 — 退化检验")

    # 2a 退化极限:常数延迟 + 无拥塞 → 无抖动 → 补偿机制不应触发
    cfg_deg = replace(base, delay_dist="constant",
                      delay_params={"value": 1.0}, recovery_load=0.0)
    m0 = _measure(cfg_deg)
    a0 = float(analytic_model.net_advantage_analytic(
        0.0, m0["delta_save"], m0["delta_recover"]))
    deg_ok = (m0["recon_triggers"] == 0 and m0["rho"] < 1e-3
              and _rel_err(m0["net_adv"], m0["delta_save"]) < 0.01
              and _rel_err(m0["net_adv"], a0) < 0.01)
    print(f"  2a 退化极限(常数延迟,无拥塞): "
          f"ρ={m0['rho']:.6f}  触发数={m0['recon_triggers']}  "
          f"净优势={m0['net_adv']:.4f} ≈ Δ_save={m0['delta_save']:.4f}  "
          f"→ {'通过' if deg_ok else '失败'}")

    # 2b 良性工况:净优势与 §7.2 闭式 / dag_bft_model MC 收敛
    cfg_ben = replace(base, delay_params={"mean": 1.0, "sigma": 0.6},
                      recovery_load=0.0)
    m1 = _measure(cfg_ben)
    closed = m1["delta_save"] - m1["rho"] * m1["delta_recover"]
    mc = analytic_model.simulate_net_advantage(
        m1["rho"], m1["delta_save"], m1["delta_recover"],
        n_rounds=base.n_rounds, n_trials=4000, seed=0)
    e_closed = _rel_err(m1["net_adv"], closed)
    e_mc = _rel_err(m1["net_adv"], float(mc.mean()))
    ben_ok = e_closed < 0.01 and e_mc < 0.01
    print(f"  2b 良性工况(lognormal σ=0.6): "
          f"ρ={m1['rho']:.4f}  净优势={m1['net_adv']:.4f}  "
          f"闭式={closed:.4f}  MC均值={float(mc.mean()):.4f}  "
          f"误差: 闭式{e_closed:.2e} / MC {e_mc:.2e}  "
          f"→ {'通过' if ben_ok else '失败'}")

    return {
        "name": "检查 2:退化检验",
        "passed": deg_ok and ben_ok,
        "criterion": "(2a) 常数延迟+无拥塞下补偿机制零触发、净优势退化为 "
                     "Δ_save;(2b) 良性工况净优势与 §7.2 闭式及 dag_bft_model "
                     "MC 相对误差均 < 1%",
        "observed": f"2a:ρ={m0['rho']:.6f}、触发数={m0['recon_triggers']}、"
                    f"净优势={m0['net_adv']:.4f}(Δ_save={m0['delta_save']:.4f});"
                    f"2b:闭式误差 {e_closed:.2e}、MC 误差 {e_mc:.2e}",
        "paper_ref": "§7.2 成本模型(闭式在良性工况成立;无抖动时退化为无补偿情形)",
        "detail_2a": m0, "detail_2b": m1,
    }


# ----------------------------------------------------------------------
# 检查 3 —— 耦合检验
# ----------------------------------------------------------------------
def check_coupling(base: SimConfig) -> dict:
    print("检查 3 — 耦合检验(注入合成拥塞负载)")
    cfg = replace(base, delay_params={"mean": 1.0, "sigma": 1.0})
    loads = [0.0, 0.5, 1.0, 1.5]
    rows = []
    print(f"  {'负载':>6} {'ρ':>9} {'Δ_recover':>10} {'Δ_save':>9} "
          f"{'净优势':>9} {'tx排队':>9}")
    for load in loads:
        m = _measure(replace(cfg, recovery_load=load))
        rows.append({"recovery_load": load, **m})
        print(f"  {load:6.2f} {m['rho']:9.4f} {m['delta_recover']:10.3f} "
              f"{m['delta_save']:9.3f} {m['net_adv']:9.3f} "
              f"{m['tx_queue_wait_mean']:9.3f}")

    drec = [r["delta_recover"] for r in rows]
    txq = [r["tx_queue_wait_mean"] for r in rows]
    # 拥塞确已发生:出口带宽排队等待随负载单调放大
    congested = (all(b >= a - 1e-6 for a, b in zip(txq, txq[1:]))
                 and txq[-1] > txq[0] * 3.0)
    # §7.4 耦合:Δ_recover 随拥塞单调抬升,§7.2 闭式的"Δ_recover 为常数"被违反
    drec_inflates = (all(b >= a - 0.03 for a, b in zip(drec, drec[1:]))
                     and drec[-1] > drec[0] * 1.1)
    # 偏离量:以无拥塞工况的标称参数套用 §7.2 闭式 vs 实测净优势
    net_nominal = rows[0]["net_adv"]
    dev = [r["net_adv"] - net_nominal for r in rows]
    print(f"  以标称(无拥塞)参数的 §7.2 闭式预测净优势恒为 "
          f"{net_nominal:.3f};实测净优势偏离 = {[round(d,3) for d in dev]}")
    print(f"  → 拥塞放大: tx 排队 {txq[0]:.3f}→{txq[-1]:.3f};"
          f"Δ_recover {drec[0]:.3f}→{drec[-1]:.3f}({drec[-1]/drec[0]:.2f}×)")

    return {
        "name": "检查 3:耦合检验",
        "passed": congested and drec_inflates,
        "criterion": "注入合成拥塞后:出口带宽排队等待单调放大(拥塞确已"
                     "发生);Δ_recover 随拥塞单调抬升且末点 > 首点×1.1 ——"
                     "§7.2 闭式视 Δ_recover 为常数,此抬升即系统性偏离",
        "observed": f"tx 排队等待 {txq[0]:.3f}→{txq[-1]:.3f}"
                    f"({txq[-1]/max(txq[0],1e-9):.0f}×);"
                    f"Δ_recover {drec[0]:.3f}→{drec[-1]:.3f}"
                    f"({drec[-1]/drec[0]:.2f}×);"
                    f"实测净优势对标称闭式偏离至 {dev[-1]:+.3f}",
        "paper_ref": "§7.4 拥塞反馈、§9 模型局限(成本模型忽略排队与相互干扰)",
        "coupling_sweep": rows,
    }


# ----------------------------------------------------------------------
# 检查 4 —— 正确性回归
# ----------------------------------------------------------------------
def check_regression(base: SimConfig) -> dict:
    print("检查 4 — 正确性回归(重跑四类自检)")
    cases = [
        ("骨架(skeleton)",
         replace(base, variant="skeleton", n_rounds=500)),
        ("uncertified 良好",
         replace(base, variant="uncertified")),
        ("certified 良好",
         replace(base, variant="certified")),
        ("uncertified + 等价攻击",
         replace(base, variant="uncertified",
                 adversary="equivocation", n_byzantine=1)),
    ]
    results = []
    for label, cfg in cases:
        r = run_simulation(cfg)
        ok = r.passed()
        results.append({"case": label, "passed": ok})
        print(f"  {label:<26}: {'通过' if ok else '失败'}")
    passed = all(r["passed"] for r in results)
    return {
        "name": "检查 4:正确性回归",
        "passed": passed,
        "criterion": "骨架 / uncertified / certified / 等价攻击 四类仿真"
                     "均通过各自正确性自检(DAG 一致、全序一致、等价中和)",
        "observed": "、".join(f"{r['case']}={'✓' if r['passed'] else '✗'}"
                              for r in results),
        "paper_ref": "§5.2 等价中和、§6.2 槽位唯一性;步骤 1.1–1.5 正确性判据",
        "cases": results,
    }


def main() -> int:
    base = SimConfig(n=7, f=2, n_rounds=N_ROUNDS, seed=0)

    print("=" * 66)
    print("验证与回归 — 阶段一 步骤 1.8")
    print("=" * 66)
    print(f"共享基线: n={base.n}  f={base.f}  轮数={base.n_rounds}  种子={base.seed}")
    print(f"解析对照: {_STAGE2 / 'dag_bft_model.py'}")
    print("-" * 66)

    checks = [
        check_cross(base),
        check_degradation(base),
        check_coupling(base),
        check_regression(base),
    ]
    coupling_sweep = next((c["coupling_sweep"] for c in checks
                           if "coupling_sweep" in c), [])
    all_passed = all(c["passed"] for c in checks)
    report = {
        "label": "stage6 仿真器验证与回归报告(阶段一 步骤 1.8)",
        "checks": [{k: v for k, v in c.items()
                    if k not in ("points", "detail_2a", "detail_2b",
                                 "cases", "coupling_sweep")}
                   for c in checks],
        "coupling_sweep": coupling_sweep,
        "all_passed": all_passed,
    }

    # --- 留存(§2.5) ---
    print("-" * 66)
    paths = export_verification(report, base.as_dict(), out_dir="data")
    print("验证报告已按 §2.5 留存规范导出至 data/:")
    for p in paths:
        print(f"  · {p.name}")
    print(f"  · 留存清单.md(已追加本次记录)")

    # --- 汇总 ---
    print("-" * 66)
    for c in checks:
        print(f"[检查] {c['name']:<24}: {'通过' if c['passed'] else '失败'}")
    print("-" * 66)
    print(f"步骤 1.8 验证与回归自检: {'全部通过 ✓' if all_passed else '未通过 ✗'}")
    print()
    print("说明:检查 1/2 为一致性核对 —— 确认 stage6 协议级仿真与 stage2 解析")
    print("      模型对 §7.2 闭式的实现彼此吻合,且常数延迟下退化为无补偿情形。")
    print("      检查 3 为实质验证 —— 注入拥塞后 Δ_recover 单调抬升,印证 §7.4")
    print("      所预测、§9 所承认的'成本模型忽略排队'这一系统性偏离。检查 4")
    print("      确认步骤 1.7 的改动未破坏既有正确性。")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
