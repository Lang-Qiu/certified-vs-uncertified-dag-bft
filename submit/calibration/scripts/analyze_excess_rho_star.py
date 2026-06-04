#!/usr/bin/env python
"""Decomposed §7.2 crossover: excess(Δr) and ρ*(Δr) from the clean t_resume sweep (phase2c).

excess(Δr) = t_resume_OFF(Δr) - t_resume_ON(Δr)   = per-fault recovery saving of certification (seconds).
ρ*(Δr)     = DSAVE_PER_COMMIT / excess(Δr)         = fault rate (faults/commit) where the §7.2 advantage
             flips uncertified -> certified. Above ρ*: certified wins; below: uncertified wins.

DSAVE_PER_COMMIT = 0.1164 s/commit, the fault-free Δ_save from PHASE1 (OFF 4.583 vs ON 2.989 ckpt/s,
lat 0.2182 vs 0.3346). Reads phase2c_excess_sweep_summary.csv (BOM-safe, status==ok), averages reps.
Writes figures/phase2c_rho_star.png.
"""
import csv, os
from collections import defaultdict

DSAVE_PER_COMMIT = 0.1164  # s/commit, PHASE1 fault-free Δ_save

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(os.path.dirname(ROOT), "stage7_deployment", "multivalidator", "data", "runs",
                   "phase2c_excess_sweep_summary.csv")
FIG = os.path.join(ROOT, "figures", "phase2c_rho_star.png")

tr = defaultdict(lambda: defaultdict(list))     # tr[recover_ms][cert_gate] = [t_resume...]
fe = defaultdict(lambda: defaultdict(list))     # fetches
with open(CSV, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row["status"] != "ok":
            continue
        try:
            ms = int(row["recover_ms"]); g = int(row["cert_gate"]); t = float(row["t_resume_s"])
            ft = int(row["v1_fetches"]) + int(row["v2_fetches"])
        except (ValueError, KeyError):
            continue
        tr[ms][g].append(t); fe[ms][g].append(ft)

def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")

print(f"{'Δr(ms)':>7} {'tR_OFF':>8} {'tR_ON':>8} {'excess(s)':>10} {'ρ*(f/commit)':>13} {'1/ρ*(commits)':>14}  fetch_OFF/ON")
rows = []
for ms in sorted(tr):
    off = tr[ms].get(0, []); on = tr[ms].get(1, [])
    if not off or not on:
        continue
    to, tn = mean(off), mean(on)
    excess = to - tn
    rho = DSAVE_PER_COMMIT / excess if excess > 0 else float("inf")
    inv = 1.0 / rho if rho not in (0, float("inf")) else float("inf")
    rows.append((ms, to, tn, excess, rho, inv))
    print(f"{ms:>7} {to:>8.1f} {tn:>8.1f} {excess:>10.2f} {rho:>13.4f} {inv:>14.1f}  "
          f"{mean(fe[ms].get(0,[])):.0f}/{mean(fe[ms].get(1,[])):.0f}")

# OLS excess ~ Δr (expect increasing: certified saves more recovery as per-event cost grows)
xs = [r[0] for r in rows]; ys = [r[3] for r in rows]
if len(xs) >= 2:
    n=len(xs); sx=sum(xs); sy=sum(ys); sxx=sum(x*x for x in xs); sxy=sum(x*y for x,y in zip(xs,ys))
    d=n*sxx-sx*sx
    if d:
        b1=(n*sxy-sx*sy)/d; b0=(sy-b1*sx)/n
        yb=sy/n; sst=sum((y-yb)**2 for y in ys); ssr=sum((y-(b0+b1*x))**2 for x,y in zip(xs,ys))
        r2=1-ssr/sst if sst else float('nan')
        print(f"\nOLS excess(Δr) = {b0:.2f} + {b1:.5e}·Δr   R²={r2:.3f}  (slope>0 => certification's recovery saving grows with Δ_recover)")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, 5))
    # Panel A: t_resume dose-response per arm
    axA.plot(xs, [r[1] for r in rows], "o-", color="#d62728", lw=2, ms=7, label="cert OFF (uncertified)")
    axA.plot(xs, [r[2] for r in rows], "s-", color="#1f77b4", lw=2, ms=7, label="cert ON (certified)")
    axA.fill_between(xs, [r[2] for r in rows], [r[1] for r in rows], color="#2ca02c", alpha=0.15,
                     label="excess = recovery saving of certification")
    axA.set_xlabel("Δ_recover (ms / recovery fetch)"); axA.set_ylabel("t_resume (s, recovery stall)")
    axA.set_title("Recovery cost per arm (critical-path fault)"); axA.legend(); axA.grid(alpha=0.3)
    # Panel B: ρ*(Δr)
    rstars = [r[4] for r in rows]
    axB.plot(xs, rstars, "o-", color="#9467bd", lw=2, ms=8)
    axB.set_xlabel("Δ_recover (ms / recovery fetch)")
    axB.set_ylabel("ρ* = Δ_save_rate / excess  (faults / commit)")
    axB.set_title("§7.2 crossover fault-rate ρ*(Δr)\nabove ρ*: certified wins · below: uncertified wins")
    axB.grid(alpha=0.3)
    for x, y in zip(xs, rstars):
        if y not in (0, float("inf")):
            axB.annotate(f"{y:.3f}", (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
    fig.suptitle(f"Decomposed §7.2 net-advantage crossover (real n=7 Sui)  ·  Δ_save={DSAVE_PER_COMMIT}s/commit",
                 fontsize=11)
    fig.tight_layout(); os.makedirs(os.path.dirname(FIG), exist_ok=True); fig.savefig(FIG, dpi=130)
    print(f"\nFigure -> {FIG}")
except ImportError:
    print("\n(matplotlib not available; table printed above)")
