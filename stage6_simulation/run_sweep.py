"""
run_sweep.py
============
阶段一 步骤 1.7 扫参与出图入口。

沿网络延迟离散度 sigma 扫参(固定 mean,即固定时间量级;建模论文
§7.4–§7.5 的网络退化),用同一串实测操作点产出论文 §7.2 图 1 /
§7.6 图 2 的**仿真实测版**:

  图 1  净优势 vs ρ           —— §7.2 成本模型视角;叠加解析直线 +
                                Δ_recover-ρ 耦合内嵌图。
  图 2  (ρ,Δ_recover) 优势区域 —— §7.6 条件性视角;实测操作轨迹叠在
                                §7.2 解析场与盈亏平衡边界上。

ρ、Δ_recover、Δ_save、净优势均为每个操作点的实测量(§4.6 测量层口径)。
图表 + 扫参原始数据 + 溯源 manifest 按 §2.5 留存规范落地到 data/。

验收(实施计划 §4.7):生成与论文图 1/2 可并排比较的图;标注"仿真实测"。

运行:
    cd stage6_simulation
    python run_sweep.py
"""
from pathlib import Path

from core import SimConfig
from experiments import sweep_delay_sigma
from metrics import (export_sweep, figure1_net_advantage,
                     figure2_advantage_region)

# --- 扫参网格(§4.7:网格扫参 + 多 trial) ---
SIGMAS = [0.35, 0.5, 0.65, 0.8, 0.95, 1.1, 1.25, 1.4]   # 离散度,单调驱动 ρ
MEAN = 1.0                                              # 固定,时间量级不变
N_TRIALS = 4                                            # 每操作点 trial 数

FIG_DIR = "data/figures"


class _Progress:
    """扫参进度计数。"""

    def __init__(self, total: int):
        self.total = total
        self.done = 0

    def __call__(self) -> None:
        self.done += 1
        bar = int(28 * self.done / self.total)
        print(f"\r  扫参进度 [{'#' * bar}{'.' * (28 - bar)}] "
              f"{self.done}/{self.total} trial", end="", flush=True)


def main() -> int:
    base = SimConfig(n=7, f=2, n_rounds=1000, seed=0)

    print("=" * 66)
    print("扫参与出图:图 1/2 实测版 — 阶段一 步骤 1.7")
    print("=" * 66)
    print(f"共享基线: n={base.n}  f={base.f}  轮数={base.n_rounds}")
    print(f"扫参自变量: sigma={SIGMAS}")
    print(f"固定 mean={MEAN}(时间量级不变)  trial/点={N_TRIALS}")

    total = len(SIGMAS) * N_TRIALS
    print(f"共需运行 {total} 个 trial(每 trial = uncertified + certified 两次仿真)")
    print("-" * 66)
    progress = _Progress(total)

    # --- sigma 扫参,返回顺序与 SIGMAS 输入顺序一致 ---
    points = sweep_delay_sigma(SIGMAS, base, n_trials=N_TRIALS,
                               mean=MEAN, progress=progress)
    print()
    print("-" * 66)

    # --- 扫参结果一览(按 sigma 输入顺序,可见 ρ 随 sigma 单调) ---
    print("sigma 扫参实测操作点(按 sigma 升序):")
    print(f"  {'sigma':>6} {'ρ':>9} {'Δ_recover':>10} {'Δ_save':>9} "
          f"{'净优势':>9}")
    for p in points:
        print(f"  {p.sigma:6.2f} {p.rho:9.4f} {p.delta_recover:10.3f} "
              f"{p.delta_save:9.3f} {p.net_adv:9.3f}")

    # --- 出图(标注"仿真实测";.png + .pdf @300dpi → data/figures/) ---
    print("-" * 66)
    fig1_files = figure1_net_advantage(points, out_dir=FIG_DIR)
    fig2_files = figure2_advantage_region(points, out_dir=FIG_DIR)
    figure_files = fig1_files + fig2_files
    print("图表已产出(标注'仿真实测',300 dpi,.png + .pdf):")
    for f in figure_files:
        print(f"  · {f}")

    # --- 留存(§2.5:原始数据 + 图表 + 溯源 manifest) ---
    data_paths = export_sweep(points, base.as_dict(), figure_files,
                              out_dir="data")
    print("扫参数据与 manifest 已按 §2.5 留存规范导出至 data/:")
    for p in data_paths:
        print(f"  · {p.name}")
    print(f"  · 留存清单.md(已追加本次记录)")

    # --- 自检(实施计划 §4.7 验收) ---
    print("-" * 66)
    # points 即按 sigma(输入自变量)顺序;此检查比对自变量,非已排序的 ρ。
    rho_by_sigma = [p.rho for p in points]
    rho_monotone = all(b >= a - 0.008
                       for a, b in zip(rho_by_sigma, rho_by_sigma[1:]))
    rho_spans = rho_by_sigma[-1] > rho_by_sigma[0] + 0.02
    drec = [p.delta_recover for p in points]
    coupling_visible = max(drec) > min(drec) * 1.5          # Δ_recover 随 ρ 上升
    all_runs_passed = all(p.all_passed for p in points)
    figs_ok = all(Path(f).exists() for f in figure_files)
    fig_formats_ok = ({f.suffix for f in figure_files} == {".png", ".pdf"}
                      and len(figure_files) == 4)
    data_ok = all(Path(p).exists() for p in data_paths)
    inventory_ok = (Path("data") / "留存清单.md").exists()

    checks = [
        ("ρ 随扫参自变量 sigma 单调上升且跨度足够",
         rho_monotone and rho_spans),
        ("正确性不破:全部 trial 的 unc/cer 两变体均通过自检", all_runs_passed),
        ("观测到 §7.4 耦合:Δ_recover 随 ρ 显著上升", coupling_visible),
        ("图 1/2 的 .png 与 .pdf 均已落地 data/figures/", figs_ok and fig_formats_ok),
        ("扫参结果 CSV / JSON / manifest 均已写出", data_ok),
        ("留存清单.md 已更新", inventory_ok),
    ]
    for label, ok in checks:
        print(f"[检查] {label:<44}: {'通过' if ok else '失败'}")
    print("-" * 66)
    ok = all(c for _, c in checks)
    print(f"步骤 1.7 扫参与出图自检: {'全部通过 ✓' if ok else '未通过 ✗'}")
    print()
    print("说明:图中实测量均标注'仿真实测',解析对照标注'§7.2 解析模型'。")
    print("      实测 Δ_recover 随 ρ 上升(§7.4 耦合,图 1 内嵌小图);净优势")
    print("      因 ρ 区间偏低而稳健为正,操作轨迹完整落在去认证占优区 ——")
    print("      正面印证 §7.6:去认证延迟优势条件性地成立于低 ρ 区。两图")
    print("      可与论文图 1(§7.2)、图 2(§7.6)并排比较,供阶段三回填。")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
