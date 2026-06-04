#!/usr/bin/env python
"""Phase A Δ_recover calibration figure.

Two panels telling the headline story:
  (A) Critical-path rotation: t_resume (cadence-stall) vs Δ_recover -> clean, monotonic, ~linear.
  (B) Contrast off- vs on-critical-path: single-node catch-up (flat/noisy) vs rotation t_resume (clean),
      both on the SAME Δ_recover sweep -> the contingent liability materializes ONLY on the critical path.

Inputs (BOM-tolerant):
  phaseA_criticalpath_summary.csv : recover_ms,...,t_resume_s,v1_fetches,v2_fetches,status   (on critical path)
  phaseA_calibration_summary.csv  : recover_ms,...,fetches,catchup_s,status                  (single node, off path)
Output: stage9_cross_protocol_calibration/figures/phaseA_recover_calibration.png
"""
import csv, os, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUNS = r"E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator\data\runs"
OUTDIR = r"E:\LQiu\lab_folder\Blockchain_final_pipeline\stage9_cross_protocol_calibration\figures"
os.makedirs(OUTDIR, exist_ok=True)


def load(fn):
    with open(os.path.join(RUNS, fn), encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if r.get("status") == "ok"]


def by_level(rows, ycol):
    lv = {}
    for r in rows:
        lv.setdefault(int(r["recover_ms"]), []).append(float(r[ycol]))
    xs = sorted(lv)
    means = [st.mean(lv[x]) for x in xs]
    sds = [st.pstdev(lv[x]) for x in xs]
    return xs, means, sds, lv


def ols(xs_all, ys_all):
    mx, my = st.mean(xs_all), st.mean(ys_all)
    b1 = sum((x - mx) * (y - my) for x, y in zip(xs_all, ys_all)) / sum((x - mx) ** 2 for x in xs_all)
    b0 = my - b1 * mx
    ss_res = sum((y - (b0 + b1 * x)) ** 2 for x, y in zip(xs_all, ys_all))
    ss_tot = sum((y - my) ** 2 for y in ys_all)
    return b0, b1, 1 - ss_res / ss_tot


cp = load("phaseA_criticalpath_summary.csv")      # n=7 on critical path -> t_resume_s
cp4 = load("phaseA_criticalpath_n4_summary.csv")  # n=4 on critical path -> t_resume_s
sn = load("phaseA_calibration_summary.csv")        # n=7 single node      -> catchup_s

cx, cm, cs, clv = by_level(cp, "t_resume_s")
c4x, c4m, c4s, c4lv = by_level(cp4, "t_resume_s")
sx, sm, ss, slv = by_level(sn, "catchup_s")


def pearson(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else float("nan")


def fitstats(rows):
    xs = [int(r["recover_ms"]) for r in rows]
    ys = [float(r["t_resume_s"]) for r in rows]
    b0, b1, r2 = ols(xs, ys)
    return b0, b1, r2, pearson(xs, ys)


b0, b1, r2, r_cp = fitstats(cp)
b0_4, b1_4, r2_4, r_cp4 = fitstats(cp4)
r_sn = pearson([int(r["recover_ms"]) for r in sn], [float(r["catchup_s"]) for r in sn])
xs_line = [0, 1000]

fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, 4.6))

# Panel A: cross-scale calibration (n=4 and n=7 replicate)
axA.errorbar(c4x, c4m, yerr=c4s, fmt="o-", color="#2ca02c", lw=2, ms=7, capsize=4,
             label=f"n=4: {b0_4:.0f}+{b1_4*1000:.0f}·(Δr/1k)  r={r_cp4:+.2f} R²={r2_4:.2f}", zorder=4)
axA.plot(xs_line, [b0_4 + b1_4 * x for x in xs_line], ":", color="#2ca02c", lw=1.3, zorder=2)
axA.errorbar(cx, cm, yerr=cs, fmt="s-", color="#1f77b4", lw=2, ms=7, capsize=4,
             label=f"n=7: {b0:.0f}+{b1*1000:.0f}·(Δr/1k)  r={r_cp:+.2f} R²={r2:.2f}", zorder=4)
axA.plot(xs_line, [b0 + b1 * x for x in xs_line], ":", color="#1f77b4", lw=1.3, zorder=2)
axA.set_xlabel("Δ_recover  (injected per-fetch delay, ms)")
axA.set_ylabel("cadence stall  t_resume (s)")
axA.set_title("(A) Cross-scale calibration: Δ_recover on the\ncritical path replicates at n=4 and n=7")
axA.legend(fontsize=8, loc="upper left")
axA.grid(alpha=0.3)
axA.set_xticks(cx)

# Panel B: off- vs on-critical-path contrast (normalised to each baseline so shapes compare)
axB.errorbar(cx, cm, yerr=cs, fmt="o-", color="#1f77b4", lw=2, ms=7, capsize=4,
             label=f"on critical path: t_resume (r={r_cp:+.2f})")
axB.errorbar(sx, sm, yerr=ss, fmt="s--", color="#7f7f7f", lw=2, ms=7, capsize=4,
             label=f"off critical path: single-node catch-up (r={r_sn:+.2f})")
axB.set_xlabel("Δ_recover  (injected per-fetch delay, ms)")
axB.set_ylabel("recovery cost (s)")
axB.set_title("(B) Liability materialises only on the critical path\n(same knob, same sweep)")
axB.legend(fontsize=8, loc="upper left")
axB.grid(alpha=0.3)
axB.set_xticks(cx)

fig.suptitle("Phase A: deployment calibration of the recovery-side contingent liability ρ·Δ_recover  "
             "(real Sui/Mysticeti, n=4 & n=7)", fontsize=11, y=1.02)
fig.tight_layout()
out = os.path.join(OUTDIR, "phaseA_recover_calibration.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
print("wrote", out)
print(f"n=7 critical-path: r={r_cp:+.3f}  slope={b1*1000:.1f}s/1000ms  R2={r2:.3f}")
print(f"n=4 critical-path: r={r_cp4:+.3f}  slope={b1_4*1000:.1f}s/1000ms  R2={r2_4:.3f}")
print(f"n=7 single-node:   r={r_sn:+.3f}")
