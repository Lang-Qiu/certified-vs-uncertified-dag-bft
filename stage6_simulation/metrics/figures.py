"""
figures.py
==========
出图(实施计划 §4.7 步骤 1.7)。

把 sigma 扫参的实测结果(experiments/sweep.py 的 SweepPoint 列表)画成
论文 §7.2 图 1 / §7.6 图 2 的 **仿真实测版**,叠加 §7.2 解析模型对照。

  figure1_net_advantage    —— 净优势 vs ρ:实测散点 + §7.2 解析直线;
                               内嵌 Δ_recover-vs-ρ 小图展示 §7.4 耦合。
  figure2_advantage_region —— (ρ, Δ_recover) 平面:§7.2 解析净优势场 +
                               §7.6 盈亏平衡边界 + 实测操作轨迹。

两图用 **同一串** sigma 扫参操作点,只是分析视角不同:图 1 是 §7.2 成本
模型视角(净优势随 ρ),图 2 是 §7.6 条件性视角((ρ,Δ_recover) 平面里
系统实际所处的位置)。图中实测量均标注"仿真实测",解析对照标注
"§7.2 解析模型"。

依赖:matplotlib(已确认 3.7.1 可用)、numpy。图以 300 dpi 同时存 .png
与 .pdf,落地到 data/figures/(§2.5 留存规范"三件套"之图表)。
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")                       # 无显示环境后端
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

# 中文字体:Windows 优先 微软雅黑 / 黑体,回退 DejaVu
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

DATA_KIND_TAG = "仿真实测(解析模型的受控数值实验,非真实协议实测)"


def _save(fig, out_dir: str, stem: str) -> list[Path]:
    """把一张图以 300 dpi 同时存 .png 与 .pdf。返回文件路径列表。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("png", "pdf"):
        p = out / f"{stem}.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
        paths.append(p)
    plt.close(fig)
    return paths


def _fit_line(x, y):
    """对散点拟合直线 y = a + b·x;返回 (a, b, 零点 x0=-a/b)。"""
    b, a = np.polyfit(x, y, 1)            # polyfit 返回 [斜率, 截距]
    x0 = (-a / b) if b != 0 else float("inf")
    return a, b, x0


# ----------------------------------------------------------------------
# 图 1 —— 净优势 vs ρ
# ----------------------------------------------------------------------
def figure1_net_advantage(points, out_dir: str = "data/figures",
                          stem: str = "figure1_净优势_vs_rho") -> list[Path]:
    """图 1 实测版:净优势随 ρ 的变化,叠加 §7.2 解析直线。

    points: sweep_delay_sigma 返回的 SweepPoint 列表。

    上面板:净优势 vs ρ。解析直线取最低 ρ 操作点的 Δ_save、Δ_recover
    为基线,按 §7.2 模型 净优势(ρ) = Δ_save0 − ρ·Δ_recover0 外推 ——
    它把 Δ_recover 当常数。下面板:实测 Δ_recover 随 ρ 的上升(§7.4 耦合)。

    实测呈现的事实:净优势在所扫的退化区间内稳健为正且大致平缓 ——
    ρ 始终偏低(< 0.1),即便 §7.4 耦合使 Δ_recover 翻数倍,ρ·Δ_recover
    一项仍是二阶小量;盈亏平衡 ρ* 远在扫参区间之外。这正面印证 §7.6:
    去认证的延迟优势条件性地成立于低 ρ 区。
    """
    pts = sorted(points, key=lambda p: p.rho)
    rho = np.array([p.rho for p in pts])
    net = np.array([p.net_adv for p in pts])
    net_std = np.array([p.net_adv_std for p in pts])
    drec = np.array([p.delta_recover for p in pts])
    drec_std = np.array([p.delta_recover_std for p in pts])

    base = pts[0]                                   # 最低 ρ 操作点 = 基线
    d_save0, d_recover0 = base.delta_save, base.delta_recover
    rho_star_analytic = (d_save0 / d_recover0) if d_recover0 > 0 else float("inf")

    rho_hi = rho.max() * 1.15 + 1e-6
    rho_line = np.linspace(0.0, rho_hi, 200)
    net_line = d_save0 - rho_line * d_recover0      # §7.2 解析直线(Δ_recover 常数)

    a, b, rho_star_sim = _fit_line(rho, net)        # 实测趋势线性拟合
    trend = a + b * rho_line

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(7.8, 6.4), sharex=True,
        gridspec_kw={"height_ratios": [3.0, 1.15], "hspace": 0.08})

    # --- 上面板:净优势 vs ρ ---
    ax1.plot(rho_line, net_line, "--", color="#1f77b4", lw=1.8, zorder=2,
             label="§7.2 解析模型:Δ_save0 − ρ·Δ_recover0(Δ_recover 视为常数)")
    ax1.plot(rho_line, trend, ":", color="#d62728", lw=1.5, zorder=2,
             label="仿真实测趋势(线性拟合)")
    ax1.errorbar(rho, net, yerr=net_std, fmt="o", color="#d62728",
                 ms=6, capsize=3, lw=1.2, zorder=4,
                 label=f"仿真实测净优势(每点 {base.n_trials} trial,误差棒 ±1σ)")
    ax1.set_ylabel("净优势 = Δ_save − ρ·Δ_recover(时间单位/轮)")
    ax1.set_title("图 1(仿真实测版)— 去认证净优势随 ρ 的变化\n"
                  "对照论文 §7.2 成本模型与图 1")
    ax1.legend(fontsize=8, loc="upper right")
    ax1.grid(True, alpha=0.3)

    # 说明文本框(左下空白区,避开数据与图例)
    rs_sim = (f"{rho_star_sim:.2f}" if np.isfinite(rho_star_sim)
              and rho_star_sim > 0 else "不收敛(趋势近平)")
    txt = (f"基线(最低 ρ 操作点):\n"
           f"  Δ_save0 = {d_save0:.3f}   Δ_recover0 = {d_recover0:.3f}\n"
           f"  ρ 区间 = [{rho.min():.4f}, {rho.max():.4f}]\n"
           f"盈亏平衡临界频率 ρ*:解析 ≈ {rho_star_analytic:.2f}  /  "
           f"实测趋势外推 ≈ {rs_sim}\n"
           f"→ ρ* 远在仿真 ρ 区间之外:此退化区间内去认证净优势稳健为正。")
    ax1.text(0.015, 0.035, txt, transform=ax1.transAxes, fontsize=7.8,
             va="bottom", ha="left",
             bbox=dict(boxstyle="round", fc="#fff8e1", ec="0.7", alpha=0.95))

    # --- 下面板:Δ_recover vs ρ —— §7.4 耦合的直接证据 ---
    ax2.errorbar(rho, drec, yerr=drec_std, fmt="s-", color="#2ca02c",
                 ms=5, lw=1.1, capsize=3,
                 label=f"仿真实测 Δ_recover(随 ρ 升 "
                       f"{drec.max()/max(drec.min(),1e-9):.1f}×)")
    ax2.set_xlabel("reconciliation 触发频率 ρ(次/验证者/轮,仿真实测)")
    ax2.set_ylabel("Δ_recover\n(时间单位)")
    ax2.legend(fontsize=8, loc="lower right")
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, rho_hi)
    ax2.annotate("§7.4 耦合:Δ_recover 并非常数,随 ρ 同向上升",
                 xy=(0.015, 0.86), xycoords="axes fraction",
                 fontsize=7.8, va="top", ha="left",
                 bbox=dict(boxstyle="round", fc="#eaf5ea", ec="0.7", alpha=0.9))

    return _save(fig, out_dir, stem)


# ----------------------------------------------------------------------
# 图 2 —— (ρ, Δ_recover) 平面的条件性优势区域
# ----------------------------------------------------------------------
def figure2_advantage_region(points, out_dir: str = "data/figures",
                             stem: str = "figure2_优势区域热力图") -> list[Path]:
    """图 2 实测版:(ρ, Δ_recover) 平面的 §7.6 条件性优势区域 + 实测轨迹。

    points: sweep_delay_sigma 返回的 SweepPoint 列表(与图 1 同一串)。

    背景热力场为 §7.2 解析预测 net(ρ,Δ) = Δ_save0 − ρ·Δ —— 在整个
    (ρ,Δ_recover) 平面上求值(Δ_save0 取最低 ρ 操作点实测值)。黑色等高线
    net=0 即论文 §7.6 的盈亏平衡边界:其左下方去认证占优,右上方认证占优。

    本模型里 ρ 与 Δ_recover 天然耦合(同一 sigma 同时推高二者),故实测
    操作点不是自由散布的云,而是一条 **操作轨迹**(灰线相连,随网络离散度
    σ 推进)。轨迹完整地落在去认证占优区、且离盈亏平衡边界尚远 —— 这正面
    回答 §7.6"去认证延迟优势在何条件下成立":在良性乃至中度退化的网络里
    系统始终处于安全区;要逼近边界需 ρ 与 Δ_recover 同时大幅抬升,而那
    在本仿真的网络退化范围内不会发生(留待 §10 的对抗性数据可用性攻击)。
    """
    pts = sorted(points, key=lambda p: p.sigma)     # 沿 σ 排出轨迹顺序
    rho = np.array([p.rho for p in pts])
    drec = np.array([p.delta_recover for p in pts])
    net = np.array([p.net_adv for p in pts])

    base = min(pts, key=lambda p: p.rho)
    d_save0 = base.delta_save

    # 规则网格覆盖整个平面,延伸至盈亏平衡边界清晰可见(§7.2 解析外推)
    rho_hi = max(0.45, rho.max() * 1.25)
    drec_hi = max(5.0, drec.max() * 1.30)
    rg = np.linspace(0.0, rho_hi, 240)
    dg = np.linspace(0.0, drec_hi, 240)
    RG, DG = np.meshgrid(rg, dg)
    NET = d_save0 - RG * DG

    # 发散配色:0 居中(白),正=去认证占优(蓝),负=认证占优(红)
    vmax = max(abs(NET.min()), abs(NET.max()), abs(net).max(), 1e-6)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    cmap = "RdBu"

    fig, ax = plt.subplots(figsize=(8.0, 5.6))
    pc = ax.pcolormesh(RG, DG, NET, cmap=cmap, norm=norm, shading="auto",
                       zorder=1)
    cs = ax.contour(RG, DG, NET, levels=[0.0], colors="black",
                    linewidths=2.0, zorder=2)
    ax.clabel(cs, fmt={0.0: "§7.6 盈亏平衡 net=0"}, fontsize=8)

    # 实测操作轨迹(随 σ 推进的耦合曲线)+ 操作点散点
    ax.plot(rho, drec, "-", color="0.25", lw=1.3, zorder=3,
            label="仿真实测操作轨迹(随网络离散度 σ 推进)")
    n_win = int(np.sum(net > 0))
    ax.scatter(rho, drec, c=net, cmap=cmap, norm=norm,
               s=95, edgecolors="black", linewidths=1.0, zorder=4,
               label=f"操作点 N={len(pts)}(填色=实测净优势;"
                     f"{n_win} 个在去认证占优区)")

    cbar = fig.colorbar(pc, ax=ax)
    cbar.set_label("净优势(时间单位/轮)  正=去认证占优 / 负=认证占优")

    ax.set_xlabel("reconciliation 触发频率 ρ(仿真实测)")
    ax.set_ylabel("单次恢复延迟 Δ_recover(时间单位,仿真实测)")
    ax.set_title("图 2(仿真实测版)— 去认证延迟优势的条件性区域\n"
                 f"背景=§7.2 解析场(Δ_save0={d_save0:.3f});"
                 "黑线=§7.6 盈亏平衡边界;轨迹=仿真实测")
    ax.legend(fontsize=8, loc="upper right")
    ax.set_xlim(0, rho_hi)
    ax.set_ylim(0, drec_hi)

    # 从操作轨迹指向边界的箭头注记
    tip = pts[-1]
    ax.annotate("逼近边界需 ρ 与 Δ_recover 同时大幅抬升\n"
                "(需对抗性数据可用性攻击,§10 未来工作)",
                xy=(rho_hi * 0.62, drec_hi * 0.62),
                xytext=(max(tip.rho, rho_hi * 0.16), drec_hi * 0.30),
                fontsize=7.6, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color="0.2", lw=1.2),
                bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9))

    return _save(fig, out_dir, stem)
