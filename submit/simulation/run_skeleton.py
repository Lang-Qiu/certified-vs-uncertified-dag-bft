"""
run_skeleton.py
===============
阶段一 步骤 1.1 仿真骨架自检入口。

验收标准(实施计划 §4.1):无故障、无敌手下能稳定推进 >= 2000 轮,
且所有诚实验证者的本地 DAG 一致。

运行:
    cd stage6_simulation
    python run_skeleton.py
"""
from core import SimConfig, run_simulation


def main() -> int:
    config = SimConfig(n=7, f=2, n_rounds=2000, seed=0)

    print("=" * 64)
    print("DAG-BFT 仿真骨架自检 — 阶段一 步骤 1.1")
    print("=" * 64)
    print(f"验证者 n={config.n}  拜占庭上限 f={config.f}  "
          f"引用/推进阈值 2f+1={config.ref_threshold}")
    print(f"网络延迟分布      : {config.delay_dist} {config.delay_params}")
    print(f"推进轮数          : {config.n_rounds}")
    print(f"随机种子          : {config.seed}")
    print("-" * 64)

    result = run_simulation(config)
    ok = result.report()

    print()
    print("说明:骨架阶段只验证 DAG 推进的正确性。提交规则、认证机制、"
          "敌手、\n      测量层在步骤 1.3–1.6 加入。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
