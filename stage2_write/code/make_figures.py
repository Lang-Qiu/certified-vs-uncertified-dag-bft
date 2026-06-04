"""
make_figures.py
===============
生成论文《认证之为结构》的三张图(Figure 1-3)。

依赖:dag_bft_model.py(同目录)、numpy、matplotlib。
运行:  python make_figures.py
输出:  ./figures/ 下的 figure_1/2/3 的 .png(预览)与 .pdf(LaTeX 嵌入)。

声明:三张图均为论文【解析模型】的图示。Figure 1/2 可视化第 7 章成本模型;
Figure 3 是按第 8 章深层轴框架对协议的【定性定位】,不代表实测坐标。
"""

from __future__ import annotations
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")                       # 无显示环境下渲染
import matplotlib.pyplot as plt

from dag_bft_model import (net_advantage_analytic, rho_star,
                           simulate_net_advantage)

# --------------------------------------------------------------------------
# APA 7.0 图形设置(摘自 visualization_agent 规范)
# --------------------------------------------------------------------------
# CJK 字体:论文为中文,图表轴标签含中文。优先 Windows 自带中文字体,
# 回退到常见 Linux/Mac CJK 字体;均不可用时由 matplotlib 给出缺字警告。
from matplotlib import font_manager as _fm
_CJK_CANDIDATES = ['Microsoft YaHei', 'SimHei', 'Microsoft JhengHei',
                   'Source Han Sans SC', 'Noto Sans CJK SC', 'PingFang SC']
_available = {f.name for f in _fm.fontManager.ttflist}
_cjk = next((f for f in _CJK_CANDIDATES if f in _available), None)
_sans = ([_cjk] if _cjk else []) + ['Arial', 'Helvetica', 'DejaVu Sans']
if _cjk:
    print(f"  [字体] 使用 CJK 字体:{_cjk}")
else:
    print("  [字体] 警告:未找到 CJK 字体,中文标签可能显示为方框")

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': _sans,
    'axes.unicode_minus': False,        # 避免 CJK 字体下负号缺字
    'font.size': 9,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# 色盲友好分类调色板
CB = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(OUTDIR, exist_ok=True)

DELTA_SAVE = 2.0          # uncertified 每轮节省的消息延迟(说明性取值)


def _save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUTDIR, f"{name}.{ext}"))
    plt.close(fig)
    print(f"  saved figures/{name}.png  &  figures/{name}.pdf")


# ==========================================================================
# Figure 1 — 净延迟优势随恢复频率 ρ 的变化
# ==========================================================================
def figure_1():
    rho = np.linspace(0.0, 1.0, 200)
    fig, ax = plt.subplots(figsize=(5.4, 3.8))

    # 每条曲线的 ρ* 标签偏移(像素),错开以免重叠
    star_offsets = {4.0: (7, 9), 8.0: (6, 10), 16.0: (-34, -15)}
    for i, d_rec in enumerate((4.0, 8.0, 16.0)):
        na = net_advantage_analytic(rho, DELTA_SAVE, d_rec)
        ax.plot(rho, na, color=CB[i], lw=2,
                label=fr"$\Delta_{{recover}}$ = {d_rec:.0f}")
        rs = rho_star(DELTA_SAVE, d_rec)
        ax.plot(rs, 0, marker='o', color=CB[i], ms=6, zorder=5)
        ax.annotate(fr"$\rho^*$ = {rs:.2f}", (rs, 0),
                    textcoords="offset points", xytext=star_offsets[d_rec],
                    fontsize=7.5, color=CB[i])

    ax.axhline(0, color='#000000', lw=0.9, ls='--')
    ax.fill_between(rho, 0, 3, color='#0077BB', alpha=0.05)
    ax.fill_between(rho, -16, 0, color='#CC3311', alpha=0.07)
    ax.text(0.50, 1.6, "净优势 > 0:uncertified 占优", fontsize=7.5,
            color='#11447A', ha='center')
    ax.text(0.62, -11.6, "净优势 < 0:优势被补偿成本吞噬", fontsize=7.5,
            color='#7A1A11', ha='center')

    ax.set_xlabel(r"恢复触发频率 $\rho$")
    ax.set_ylabel("净延迟优势(消息延迟数)")
    ax.set_xlim(0, 1)
    ax.set_ylim(-14, 3)
    ax.legend(title=r"$\Delta_{save}$ = 2", loc='upper right', frameon=True,
              framealpha=1.0, facecolor='white', edgecolor='0.8')
    _save(fig, "figure_1_net_advantage")


# ==========================================================================
# Figure 2 — (ρ, Δ_recover) 空间中的优势区域热力图
# ==========================================================================
def figure_2():
    rho = np.linspace(0.0, 1.0, 240)
    d_rec = np.linspace(1.0, 20.0, 240)
    RHO, DREC = np.meshgrid(rho, d_rec)
    NA = DELTA_SAVE - RHO * DREC                       # 净优势曲面

    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    vmax = np.abs(NA).max()
    im = ax.pcolormesh(RHO, DREC, NA, cmap='coolwarm_r',
                       vmin=-vmax, vmax=vmax, shading='auto')
    # 临界边界 ρ* = Δ_save / Δ_recover(净优势为零的等高线)
    boundary = DELTA_SAVE / d_rec
    ax.plot(boundary, d_rec, color='#000000', lw=1.8,
            label=r"$\rho^*=\Delta_{save}/\Delta_{recover}$(净优势=0)")

    ax.set_xlabel(r"恢复触发频率 $\rho$")
    ax.set_ylabel(r"单次恢复成本 $\Delta_{recover}$(消息延迟数)")
    ax.set_xlim(0, 1)
    ax.set_ylim(1, 20)
    ax.legend(loc='upper right', frameon=True, framealpha=0.9)
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("净延迟优势(>0:uncertified 占优)")
    ax.text(0.05, 17, "uncertified 占优", fontsize=8, color='#11447A')
    ax.text(0.55, 4.5, "优势被抵消 / 反转", fontsize=8, color='#7A1A11')
    _save(fig, "figure_2_advantage_region")


# ==========================================================================
# Figure 3 — 深层设计轴上的协议定位(论文第 8 章)
# ==========================================================================
def figure_3():
    # 按第 8 章深层轴框架的【定性】定位:
    # x = availability-enforcement 时机;y = 单次 reconciliation 开销
    fig, ax = plt.subplots(figsize=(6.2, 4.2))

    # 中部 / 右侧协议:点 + 偏移标签(彼此 y 间距足够,直接标注)
    spread = [
        ("Cordial Miners [42]", 1.33, 0.52, CB[3], (9, -3)),
        ("Mysticeti [43]",      1.63, 0.60, CB[3], (9, 3)),
        ("Mahi-Mahi [44]",      1.82, 0.68, CB[3], (9, 3)),
        ("Adelie [45]",         1.70, 0.34, CB[2], (9, 3)),
        ("DispersedLedger [47]", 2.02, 0.18, CB[1], (-14, -16)),
    ]
    for name, x, y, c, off in spread:
        ax.scatter(x, y, s=80, color=c, edgecolor='black', lw=0.6, zorder=5)
        ax.annotate(name, (x, y), textcoords="offset points",
                    xytext=off, fontsize=7.5)

    # 左侧 certified 簇:三点密集,用引线把标签引到上方空白处错开排列
    cluster = [
        ("DAG-Rider [31]",    0.03, 0.05, 0.64),
        ("Narwhal/Tusk [32]", 0.13, 0.09, 0.50),
        ("Bullshark [33]",    0.24, 0.05, 0.36),
    ]
    for name, x, y, label_y in cluster:
        ax.scatter(x, y, s=80, color=CB[0], edgecolor='black', lw=0.6, zorder=5)
        ax.annotate(name, xy=(x, y), xytext=(0.44, label_y), fontsize=7.5,
                    va='center',
                    arrowprops=dict(arrowstyle='-', lw=0.6, color='#999999'))

    ax.axvspan(-0.15, 0.45, color='#0077BB', alpha=0.06)
    ax.axvspan(1.55, 2.18, color='#EE7733', alpha=0.06)
    ax.text(0.00, 0.90, "传统 certified 端", fontsize=7.5, color='#11447A')
    ax.text(1.60, 0.90, "传统 uncertified 端", fontsize=7.5, color='#7A3A11')

    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["引用前\n(pre-reference)", "提交前\n(pre-commit)",
                        "提交后\n(post-commit)"])
    ax.set_xlabel("维度一:availability-enforcement 时机")
    ax.set_ylabel("维度二:单次 reconciliation 开销(定性)")
    ax.set_xlim(-0.25, 2.75)
    ax.set_ylim(-0.05, 1.0)
    _save(fig, "figure_3_design_axis")


if __name__ == "__main__":
    print("生成论文图表 …")
    figure_1()
    figure_2()
    figure_3()
    print("完成。三张图已输出至 figures/(png 预览 + pdf 供 LaTeX 嵌入)。")
