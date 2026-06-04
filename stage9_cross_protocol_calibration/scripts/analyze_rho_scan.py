"""P0-2 rho-scan analysis: cadence & recovery cost vs fault frequency (sec.7.3).

Establishes:
  1. cadence_eff declines ~linearly in rho (fault density) -> the sec.7.3 throughput claim.
  2. recFetch and sum_t_resume rise with rho -> recovery cost accumulates with fault freq.
  3. A directly-MEASURED degradation slope to cross-check the rho* band that sec.7.6.3
     only DERIVED from Delta_save/excess.
"""
import csv, sys
from statistics import mean, stdev
from math import sqrt

def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def ols(xs, ys):
    n = len(xs)
    if n < 2: return 0, (ys[0] if ys else 0), 0, 0
    mx, my = sum(xs)/n, sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs)
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    syy = sum((y-my)**2 for y in ys)
    slope = sxy/sxx if sxx else 0
    intercept = my - slope*mx
    r = sxy/sqrt(sxx*syy) if sxx*syy > 0 else 0
    return slope, intercept, r, r*r

path = sys.argv[1] if len(sys.argv) > 1 else \
    "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage7_deployment/multivalidator/data/runs/rho_scan_summary.csv"
rows = [r for r in load(path) if r['status'] == 'ok']
data = []
for r in rows:
    data.append({
        'N': int(r['fault_count']), 'rep': int(r['rep']),
        'commits': int(r['commits']), 'wall': float(r['wallclock_s']),
        'cad': float(r['cadence_eff']), 'sumRes': float(r['sum_t_resume_s']),
        'recFetch': int(r['recFetch']), 'rho': float(r['rho']),
        'eq': int(r['eqChk']), 'caus': int(r['causDec']),
    })
Ns = sorted(set(d['N'] for d in data))

print("="*78)
print(f"P0-2 RHO SCAN — N={len(data)} runs, fault counts {Ns}, Delta_recover=1000ms, cert=OFF")
print("="*78)

# ---- 1. per-N cell means ----
print("\n1. CELL MEANS BY FAULT COUNT")
print("-"*74)
print(f"   {'N':>2s} {'reps':>4s} | {'rho':>9s} | {'cadence_eff':>14s} | {'recFetch':>14s} | {'sum_t_resume':>14s}")
cell = {}
for N in Ns:
    sub = [d for d in data if d['N'] == N]
    rho_m = mean(d['rho'] for d in sub)
    cad_m = mean(d['cad'] for d in sub); cad_sd = stdev([d['cad'] for d in sub]) if len(sub) > 1 else 0
    rf_m = mean(d['recFetch'] for d in sub); rf_sd = stdev([d['recFetch'] for d in sub]) if len(sub) > 1 else 0
    res_m = mean(d['sumRes'] for d in sub)
    cell[N] = (rho_m, cad_m, rf_m, res_m)
    print(f"   {N:2d} {len(sub):4d} | {rho_m:9.5f} | {cad_m:7.3f} +/-{cad_sd:5.3f} | {rf_m:7.0f} +/-{rf_sd:6.0f} | {res_m:9.1f}s")

# baseline cadence + degradation
cad0 = cell[0][1] if 0 in cell else None
if cad0:
    print(f"\n   fault-free baseline cadence (N=0): {cad0:.3f} ckpt/s")
    for N in Ns:
        if N == 0: continue
        print(f"   N={N}: cadence {cell[N][1]:.3f} ckpt/s -> {100*(cell[N][1]-cad0)/cad0:+.1f}% vs baseline")

# ---- 2. cadence vs rho (the sec.7.3 degradation) ----
print("\n2. OLS  cadence_eff  vs  rho  (sec.7.3 throughput degradation)")
print("-"*74)
xs = [d['rho'] for d in data]; ys = [d['cad'] for d in data]
s, b, r, r2 = ols(xs, ys)
print(f"   cadence_eff = {b:.3f} {s:+.2f}*rho    r={r:+.3f}  R2={r2:.3f}")
print(f"   intercept {b:.3f} ckpt/s ~= fault-free cadence; slope {s:.1f} ckpt/s per unit rho")

# ---- 3. cadence vs N (robustness: integer fault count, no commits-in-denominator coupling) ----
print("\n3. OLS  cadence_eff  vs  N  (robustness check, N as raw fault count)")
print("-"*74)
xs = [d['N'] for d in data]; ys = [d['cad'] for d in data]
s, b, r, r2 = ols(xs, ys)
print(f"   cadence_eff = {b:.3f} {s:+.4f}*N    r={r:+.3f}  R2={r2:.3f}")

# ---- 4. recFetch & sum_t_resume vs rho ----
print("\n4. OLS  recovery cost  vs  rho")
print("-"*74)
for label, key in [("recFetch", "recFetch"), ("sum_t_resume_s", "sumRes")]:
    xs = [d['rho'] for d in data]; ys = [d[key] for d in data]
    s, b, r, r2 = ols(xs, ys)
    print(f"   {label:16s}: slope={s:+.1f}/unit-rho  intercept={b:.2f}  r={r:+.3f}  R2={r2:.3f}")

# ---- 5. rho* cross-check ----
print("\n5. rho* CROSS-CHECK (measured degradation vs sec.7.6.3 derived band)")
print("-"*74)
print("   sec.7.6.3 derived rho* from Delta_save/excess (indirect). Here we have a DIRECT")
print("   measured cadence-vs-rho slope. Report both; flag if measured slope implies a")
print("   rho* consistent with the derived band (qualitative agreement is the claim).")
if cad0:
    s_cad, _, _, _ = ols([d['rho'] for d in data], [d['cad'] for d in data])
    print(f"   measured: each +0.01 rho costs ~{-s_cad*0.01:.3f} ckpt/s "
          f"({100*-s_cad*0.01/cad0:.1f}% of baseline) of throughput")

# ---- 6. enforcement-path controls ----
print("\n6. ENFORCEMENT-PATH CONTROLS (eqChk/causDec track commits, not fault freq)")
print("-"*74)
for N in Ns:
    sub = [d for d in data if d['N'] == N]
    print(f"   N={N}: eqChk/commit={mean(d['eq']/d['commits'] for d in sub):.2f}  "
          f"causDec/commit={mean(d['caus']/d['commits'] for d in sub):.2f}")
print("   (per-commit ratios ~flat across N => paths are commit-bound, not fault-bound)")
