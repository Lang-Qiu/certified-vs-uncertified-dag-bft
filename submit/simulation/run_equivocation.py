"""
run_equivocation.py
===================
阶段一 步骤 1.5 等价攻击自检入口。

验收标准(实施计划 §4.5):等价攻击能在 uncertified 变体触发提交规则的
等价中和逻辑;能观测到对槽位唯一性的破坏。

设置:uncertified 变体,n=7、f=2,1 个拜占庭验证者。拜占庭作者每轮在
同一 (author,round) 槽位产生两个区块,向半数验证者出示其一、另半数
出示其二。

自检判据:
  - 所有验证者推进至目标轮数;
  - 检出被等价的槽位(攻击确已发生);
  - 观测到槽位唯一性破坏 —— 同一槽位在不同诚实验证者的规范 DAG 中
    被不同区块占据(论文 §6.2);
  - 等价中和逻辑已触发 —— 等价锚点被跳过、等价区块被排除出全序
    (论文 §5.2);
  - 所有诚实验证者的全序仍互为前缀 —— 中和有效,安全性得以维持。

运行:
    cd stage6_simulation
    python run_equivocation.py
"""
from core import SimConfig, run_simulation


def main() -> int:
    config = SimConfig(n=7, f=2, n_rounds=2000, variant="uncertified",
                       adversary="equivocation", n_byzantine=1, seed=0)

    print("=" * 64)
    print("等价攻击自检 — 阶段一 步骤 1.5")
    print("=" * 64)
    print(f"变体              : {config.variant}")
    print(f"敌手              : {config.adversary}"
          f"(拜占庭验证者 {config.n_byzantine} 个,每轮等价)")
    print(f"验证者 n={config.n}  f={config.f}  "
          f"诚实 {config.n_honest}  拜占庭 {config.n_byzantine}")
    print(f"推进轮数          : {config.n_rounds}  随机种子: {config.seed}")
    print("-" * 64)

    result = run_simulation(config)
    ok = result.report()

    print()
    print("说明:等价攻击使同一槽位在不同诚实验证者的本地 DAG 中被不同")
    print("      区块占据 —— 这正是论文 §6.2 论证的槽位唯一性破坏。")
    print("      uncertified 变体的提交规则据此显式中和等价(§5.2):")
    print("      等价作者占任的锚点轮被跳过、等价区块不进入全序,从而")
    print("      诚实验证者的全序仍保持一致 —— 印证 §6 的结论:非等价性")
    print("      必须被 enforce,uncertified 把它从广播层平移到了提交层。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
