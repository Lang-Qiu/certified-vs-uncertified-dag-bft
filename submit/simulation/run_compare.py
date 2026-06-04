"""
run_compare.py
==============
阶段一 步骤 1.4 受控 minimal-pair 对照入口。

以**完全相同的配置、仅 variant 不同**运行 uncertified 与 certified 两个
变体 —— 这正是论文 §3.3 的受控 minimal pair。§3.5 指出:真实世界中
这样的 minimal pair "严格意义上往往无法构造"(真实 uncertified 协议
=去认证+一批补偿机制,十余维度同时变);但在自建仿真器中,只需替换
一个可插拔的认证模块即可一键切换,其余配置逐项相同。

对照二者的每轮推进延迟、reconciliation,给出论文 §7.2 成本模型
  净优势 ≈ Δ_save − ρ·Δ_recover
的一个**实测**版本(此前 dag_bft_model.py 中这些量是假定的输入参数,
此处它们是仿真测得的输出)。

验收标准(实施计划 §4.4):两变体除认证模块外配置完全一致;切换不
影响骨架行为(两者都能推进、DAG 一致、全序一致)。

运行:
    cd stage6_simulation
    python run_compare.py
"""
from dataclasses import replace

from core import SimConfig, run_simulation


def main() -> int:
    # variant 之外的全部配置 —— 两变体共享,构成受控 minimal pair
    base = SimConfig(n=7, f=2, n_rounds=2000, seed=0)

    print("=" * 70)
    print("受控 minimal-pair 对照 — 阶段一 步骤 1.4")
    print("=" * 70)
    print(f"共享配置: n={base.n}  f={base.f}  轮数={base.n_rounds}  "
          f"延迟={base.delay_dist}{base.delay_params}  种子={base.seed}")
    print("唯一变量: variant ∈ {uncertified, certified}")
    print("-" * 70)

    results = {}
    for variant in ("uncertified", "certified"):
        cfg = replace(base, variant=variant)
        results[variant] = (cfg, run_simulation(cfg))

    unc_cfg, unc = results["uncertified"]
    cer_cfg, cer = results["certified"]

    # --- 受控性核验:两配置除 variant 外逐项相同 ---
    d_unc = {k: v for k, v in unc_cfg.as_dict().items() if k != "variant"}
    d_cer = {k: v for k, v in cer_cfg.as_dict().items() if k != "variant"}
    controlled = d_unc == d_cer

    # --- 对照表 ---
    print(f"{'指标':<26}{'uncertified':>16}{'certified':>16}")
    print("-" * 70)
    print(f"{'每轮平均推进延迟':<24}{unc.round_latency:>16.4f}{cer.round_latency:>16.4f}")
    print(f"{'已提交区块数(最小)':<22}{min(unc.committed_lens):>16}"
          f"{min(cer.committed_lens):>16}")
    print(f"{'reconciliation 触发数':<22}{unc.recon_triggers:>16}"
          f"{cer.recon_triggers:>16}")
    print(f"{'Δ_recover(单次恢复延迟)':<20}{unc.recon_latency_mean:>16.3f}"
          f"{cer.recon_latency_mean:>16.3f}")
    print(f"{'出口带宽排队均值':<24}{unc.tx_queue_wait_mean:>16.4f}"
          f"{cer.tx_queue_wait_mean:>16.4f}")
    print("-" * 70)

    # --- 论文 §7.2 成本模型的实测版本 ---
    delta_save = cer.round_latency - unc.round_latency        # 每轮 uncertified 省下的延迟
    rho = unc.recon_triggers / (base.n * base.n_rounds)       # 每验证者每轮恢复频率
    delta_recover = unc.recon_latency_mean
    net_adv = delta_save - rho * delta_recover                # 净优势(每轮)

    print("论文 §7.2 成本模型(实测):净优势 ≈ Δ_save − ρ·Δ_recover")
    print(f"  Δ_save    (certified − uncertified 每轮延迟) = {delta_save:.4f}")
    print(f"  ρ         (每验证者每轮 reconciliation 频率) = {rho:.5f}")
    print(f"  Δ_recover (单次 reconciliation 延迟)         = {delta_recover:.3f}")
    print(f"  净优势    ≈ {delta_save:.4f} − {rho:.5f}×{delta_recover:.3f} "
          f"= {net_adv:.4f}  (>0:uncertified 占优)")
    print("-" * 70)

    # --- 自检 ---
    checks = [
        ("两变体除 variant 外配置完全一致(受控 minimal pair)", controlled),
        ("uncertified 通过自身正确性判据", unc.passed()),
        ("certified 通过自身正确性判据", cer.passed()),
        ("Δ_save > 0(uncertified 每轮延迟更低)", delta_save > 0),
        ("certified 提交时无 reconciliation", cer.recon_triggers == 0),
    ]
    for label, ok in checks:
        print(f"[检查] {label:<44}: {'通过' if ok else '失败'}")
    print("-" * 70)
    ok = all(c for _, c in checks)
    print(f"步骤 1.4 受控对照自检: {'全部通过 ✓' if ok else '未通过 ✗'}")
    print()
    print("解读:无敌手、近同步下 ρ 极小,净优势 ≈ Δ_save > 0,uncertified")
    print("      占优 —— 这与论文报告的良好情形一致。Δ_save 来自 certified")
    print("      的 RBC 认证延迟(echo 往返),此前是假定参数,现为实测值。")
    print("      敌手与不利网络(步骤 1.5 及之后)将推高 ρ 与 Δ_recover,")
    print("      届时即可观察净优势被压缩乃至反转(论文第 7 章条件化结论)。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
