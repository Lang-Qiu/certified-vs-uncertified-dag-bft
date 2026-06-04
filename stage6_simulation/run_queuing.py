"""
run_queuing.py
==============
阶段一 步骤 1.2 排队效应自检入口。

验收标准(实施计划 §4.2):注入恢复负载后,能观测到排队延迟随负载
非线性上升。

做法:固定区块负载,扫描递增的合成恢复负载 λ,观察区块传输在出口
带宽上的平均排队等待。若排队均值随 λ 呈 M/M/1 式 ρ/(1-ρ) 的非线性
上升,则说明排队与相互干扰已由共享带宽资源自动涌现 —— 这正是论文
§9、§7.4 指出而闭式成本模型未刻画的效应。

运行:
    cd stage6_simulation
    python run_queuing.py
"""
from core import SimConfig, run_simulation


def main() -> int:
    print("=" * 72)
    print("出口带宽排队效应 — 阶段一 步骤 1.2")
    print("=" * 72)
    print("固定区块负载,扫描递增的合成恢复负载 λ;观察区块传输的排队等待。")
    print(f"(n=7, f=2, 每点 1000 轮; tx_service=0.1, recovery_service=0.5)")
    print("-" * 72)
    print(f"{'恢复负载λ':>10} {'恢复利用率':>10} {'区块排队均值':>14} "
          f"{'区块排队最大':>14} {'恢复排队均值':>14}")
    print("-" * 72)

    base = dict(n=7, f=2, n_rounds=1000, seed=0,
                tx_service=0.1, recovery_service=0.5)
    rows = []
    for load in (0.0, 0.4, 0.8, 1.2, 1.5, 1.6):
        cfg = SimConfig(recovery_load=load, **base)
        r = run_simulation(cfg)
        rho_recovery = load * base["recovery_service"]   # 恢复负载贡献的出口利用率
        rows.append((load, r))
        print(f"{load:>10.2f} {rho_recovery:>10.2f} "
              f"{r.tx_queue_wait_mean:>14.4f} {r.tx_queue_wait_max:>14.4f} "
              f"{r.recovery_queue_wait_mean:>14.4f}")

    print("-" * 72)
    # 自检:排队均值应单调上升,且尾部增量显著大于头部(非线性)
    waits = [r.tx_queue_wait_mean for _, r in rows]
    monotonic = all(waits[i] <= waits[i + 1] + 1e-9 for i in range(len(waits) - 1))
    head_delta = waits[1] - waits[0]
    tail_delta = waits[-1] - waits[-2]
    nonlinear = tail_delta > head_delta * 2

    print(f"[检查] 排队均值随负载单调上升        : {'通过' if monotonic else '失败'}")
    print(f"[检查] 尾部增量 > 头部增量×2(非线性): "
          f"{'通过' if nonlinear else '失败'}"
          f"  (头部Δ={head_delta:.4f}, 尾部Δ={tail_delta:.4f})")
    print("-" * 72)
    ok = monotonic and nonlinear
    print(f"步骤 1.2 排队效应自检: {'全部通过 ✓' if ok else '未通过 ✗'}")
    print()
    print("解读:恢复利用率接近 1 时排队均值急剧上升 —— 排队与相互干扰由")
    print("      共享出口带宽资源自动涌现,无需闭式公式。这回应论文 §9")
    print("      「成本模型忽略排队与相互干扰」与 §7.4 拥塞反馈。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
