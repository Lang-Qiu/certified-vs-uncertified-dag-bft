"""Figure 7-3: corrected 2x2 cross-scale / cross-intensity stability grid.

Source data: stage7_deployment/multivalidator/reports/
             stress_test_combined_conclusion_v3_20260526.md (TL;DR table).

p95 additivity ratio = observed / expected_additive  ( >1 => super-additive ).
This grid is a presentation of real-deployment measurements (Sui n=7/n=4),
NOT an analytical model figure.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# rows: within f (n=7,f=2) on top, at/above f (n=4,f=1) on bottom
# cols: moderate (2% loss) left, high (5% loss) right
cells = {
    # (col, row): (label_lines, representative_ratio_for_color, regime)
    (0, 1): (["within f  (n=7, f=2)", "Test 0: 1.03", "Test 1: 1.00", "additive"], 1.03, "add"),
    (1, 1): (["within f  (n=7, f=2)", "Test 2: 1.08", "", "super-additive"], 1.08, "super"),
    (0, 0): (["at/above f  (n=4, f=1)", "n=4 ablation: 0.97", "(orig 1.16: false positive)", "additive"], 0.97, "add"),
    (1, 0): (["at/above f  (n=4, f=1)", "n=4 + 5%: 1.12", "", "super-additive"], 1.12, "super"),
}

ADD_COLOR = "#cdeccd"      # light green
SUPER_COLOR = "#f6c6a8"    # light orange
EDGE = "#444444"

fig, ax = plt.subplots(figsize=(8.2, 6.0))

for (cx, cy), (lines, ratio, regime) in cells.items():
    color = ADD_COLOR if regime == "add" else SUPER_COLOR
    ax.add_patch(Rectangle((cx, cy), 1, 1, facecolor=color, edgecolor=EDGE, linewidth=1.5))
    tx, ty = cx + 0.5, cy + 0.5
    # regime tag (top of cell)
    ax.text(tx, cy + 0.86, lines[0], ha="center", va="center", fontsize=10.5,
            color="#222222")
    ax.text(tx, ty + 0.10, lines[1], ha="center", va="center", fontsize=15,
            fontweight="bold", color="#111111")
    if lines[2]:
        ax.text(tx, ty - 0.14, lines[2], ha="center", va="center", fontsize=9.5,
                color="#555555")
    ax.text(tx, cy + 0.14, lines[3], ha="center", va="center", fontsize=11.5,
            fontstyle="italic",
            color=("#2e7d32" if regime == "add" else "#c0392b"))

# axes framing
ax.set_xlim(0, 2)
ax.set_ylim(0, 2)
ax.set_xticks([0.5, 1.5])
ax.set_xticklabels(["moderate intensity\n(2% loss)", "high intensity\n(5% loss)"], fontsize=12)
ax.set_yticks([0.5, 1.5])
ax.set_yticklabels(["at/above f\n(n=4)", "within f\n(n=7)"], fontsize=12, rotation=90, va="center")
ax.xaxis.set_ticks_position("none")
ax.yaxis.set_ticks_position("none")
for spine in ax.spines.values():
    spine.set_visible(False)

ax.set_xlabel("single-fault intensity axis  →  (sole driver of super-additivity)",
              fontsize=11.5, labelpad=10)
ax.set_ylabel("BFT-bound axis  (no independent effect)", fontsize=11.5, labelpad=10)
ax.set_title("Figure 7-3  Cross-scale / cross-intensity additivity stability\n"
             "(p95 cadence ratio; real Sui n=7/n=4 deployment)",
             fontsize=12.5, pad=14)

fig.tight_layout()
out = __file__.rsplit("make_figure_7_3.py", 1)[0] + "figure_7_3_stability_grid.png"
fig.savefig(out, dpi=200, bbox_inches="tight")
print("wrote", out)
