#!/usr/bin/env python
"""Analyze the joint net-advantage sweep -> §7.2 crossover.

net_advantage(Δr) = lat_ON - lat_OFF = 1/cadence_ON - 1/cadence_OFF  (seconds per checkpoint).
  > 0  : cert ON slower amortized => UNCERTIFIED wins (its fault-free Δ_save outweighs recovery cost)
  < 0  : cert ON faster amortized => CERTIFIED wins (uncertified's recovery liability dominates)
  Δr*  : the sign flip = the §7.2 conditional reversal, measured on real n=7 Sui.

Reads phase2b_net_advantage_summary.csv (BOM-safe). Averages over reps. OLS net_adv ~ Δr -> crossover.
Writes figures/phase2b_net_advantage.png.
"""
import csv, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(os.path.dirname(ROOT), "stage7_deployment", "multivalidator", "data", "runs",
                   "phase2b_net_advantage_summary.csv")
FIG = os.path.join(ROOT, "figures", "phase2b_net_advantage.png")

# cadence[recover_ms][cert_gate] = list of cadence_ckpt_s (status ok only)
cad = defaultdict(lambda: defaultdict(list))
with open(CSV, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row["status"] != "ok":
            continue
        try:
            ms = int(row["recover_ms"]); g = int(row["cert_gate"]); c = float(row["cadence_ckpt_s"])
        except (ValueError, KeyError):
            continue
        if c > 0:
            cad[ms][g].append(c)

def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")

rows = []
for ms in sorted(cad):
    off = cad[ms].get(0, []); on = cad[ms].get(1, [])
    if not off or not on:
        continue
    cad_off, cad_on = mean(off), mean(on)
    lat_off, lat_on = 1.0 / cad_off, 1.0 / cad_on  # s per ckpt
    netadv = lat_on - lat_off                       # >0 uncertified wins
    rows.append((ms, cad_off, cad_on, lat_off, lat_on, netadv))

print(f"{'Δr(ms)':>7} {'cad_OFF':>8} {'cad_ON':>8} {'lat_OFF':>8} {'lat_ON':>8} {'net_adv(s)':>11}")
for ms, co, cn, lo, ln, na in rows:
    print(f"{ms:>7} {co:>8.3f} {cn:>8.3f} {lo:>8.4f} {ln:>8.4f} {na:>11.4f}")

# OLS net_adv ~ Δr  -> crossover Δr* = -b0/b1
xs = [r[0] for r in rows]; ys = [r[5] for r in rows]
cross = None; b0 = b1 = float("nan")
if len(xs) >= 2:
    n = len(xs); sx = sum(xs); sy = sum(ys); sxx = sum(x*x for x in xs); sxy = sum(x*y for x, y in zip(xs, ys))
    denom = n*sxx - sx*sx
    if denom != 0:
        b1 = (n*sxy - sx*sy) / denom
        b0 = (sy - b1*sx) / n
        if b1 != 0:
            cross = -b0 / b1
        yb = sy/n; ss_tot = sum((y-yb)**2 for y in ys); ss_res = sum((y-(b0+b1*x))**2 for x,y in zip(xs,ys))
        r2 = 1 - ss_res/ss_tot if ss_tot else float("nan")
        print(f"\nOLS: net_adv = {b0:.4f} + {b1:.6e}·Δr   R²={r2:.3f}")
        if cross is not None:
            print(f"Crossover Δr* = {cross:.0f} ms  (net_advantage flips sign: uncertified->certified)")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.axhline(0, color="0.6", lw=1)
    ax.plot(xs, [y*1000 for y in ys], "o-", color="#1f77b4", lw=2, ms=8, label="net_advantage (ms/ckpt)")
    if len(xs) >= 2:
        xr = [min(xs), max(xs)]
        ax.plot(xr, [(b0+b1*x)*1000 for x in xr], "--", color="#ff7f0e",
                label=f"OLS (Δr*={cross:.0f} ms)" if cross is not None else "OLS")
    ax.set_xlabel("Δ_recover (ms per recovery fetch)")
    ax.set_ylabel("net_advantage of uncertified = lat_ON − lat_OFF  (ms/ckpt)")
    ax.set_title("§7.2 net-advantage crossover (real n=7 Sui, one critical-path fault)\n"
                 "+ = uncertified wins · − = certified wins")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); os.makedirs(os.path.dirname(FIG), exist_ok=True); fig.savefig(FIG, dpi=130)
    print(f"\nFigure -> {FIG}")
except ImportError:
    print("\n(matplotlib not available; table + crossover printed above)")
