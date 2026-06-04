"""
run_uncertified.py
==================
阶段一 步骤 1.3 uncertified 变体自检入口。

验收标准(实施计划 §4.3):uncertified 变体能在无敌手下稳定提交,
且在数据缺失时触发 reconciliation。

自检判据:
  - 所有验证者推进至目标轮数;
  - 所有本地 DAG 一致(无敌手);
  - 所有验证者的全序互为前缀(共识排序一致);
  - reconciliation 已触发(提交时检出数据缺失并补偿)。

运行:
    cd stage6_simulation
    python run_uncertified.py
"""
from core import SimConfig, run_simulation


def main() -> int:
    config = SimConfig(n=7, f=2, n_rounds=2000, variant="uncertified", seed=0)

    print("=" * 64)
    print("uncertified 变体自检 — 阶段一 步骤 1.3")
    print("=" * 64)
    print(f"变体              : {config.variant}"
          f"(best-effort 广播 + 提交时可用性检查 + reconciliation)")
    print(f"验证者 n={config.n}  f={config.f}  "
          f"提交支持阈值 quorum=n-f={config.quorum}")
    print(f"网络延迟分布      : {config.delay_dist} {config.delay_params}")
    print(f"恢复服务时间      : {config.recovery_service}")
    print(f"推进轮数          : {config.n_rounds}  随机种子: {config.seed}")
    print("-" * 64)

    result = run_simulation(config)
    ok = result.report()

    print()
    print("说明:reconciliation 由网络延迟尾部自然触发 —— 锚点在部分视图上")
    print("      提交时,其因果历史中某些区块的内容尚在途中,提交被阻塞")
    print("      直至恢复完成。无敌手、近同步下触发较少,这与论文 §5.6")
    print("      『或有负债:良好情形下为零』一致;敌手与不利网络(步骤")
    print("      1.5 及之后)会显著推高触发频率 ρ。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
