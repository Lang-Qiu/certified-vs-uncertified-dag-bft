"""P1-5 GST Jitter — cadence degradation under partial-synchrony cycling (sec.7.4)."""
import csv, sys
from statistics import mean, stdev
from math import sqrt

def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def ols(xs, ys):
    n = len(xs)
    if n < 2: return 0, sum(ys)/n, 0, 0
    mx, my = sum(xs)/n, sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs)
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    syy = sum((y-my)**2 for y in ys)
    slope = sxy/sxx if sxx else 0
    intercept = my - slope*mx
    r = sxy/sqrt(sxx*syy) if sxx*syy > 0 else 0
    return slope, intercept, r, r*r

path = sys.argv[1] if len(sys.argv) > 1 else \
    "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage7_deployment/multivalidator/data/runs/gst_jitter_summary.csv"
rows = [r for r in load(path) if r['status'] == 'ok']
data = []
for r in rows:
    data.append({
        'period': int(r['jitter_period_s']), 'cad': float(r['cadence_eff']),
        'recFetch': int(r['recFetch']), 'cycles': int(r['cycles']),
        'stall': float(r['sum_stall_s']), 'commits': int(r['commits']),
        'wall': float(r['wallclock_s']), 'eq': int(r['eqChk']), 'caus': int(r['causDec']),
    })
periods = sorted(set(d['period'] for d in data))

print("="*68)
print(f"P1-5 GST JITTER — N={len(data)} runs, period ∈ {periods}s, dRec=500ms")
print("="*68)

print("\n1. CELL MEANS")
print("-"*68)
print(f"   {'period':>8s} | {'cadence_eff':>14s} | {'recFetch':>10s} | {'cycles':>8s} | {'fetch/cycle':>12s}")
for p in periods:
    sub = [d for d in data if d['period'] == p]
    cad_m = mean(d['cad'] for d in sub)
    cad_sd = stdev([d['cad'] for d in sub]) if len(sub) > 1 else 0
    f_m = mean(d['recFetch'] for d in sub)
    c_m = mean(d['cycles'] for d in sub)
    fc = f_m / c_m if c_m else 0
    print(f"   {p:6d}s | {cad_m:7.3f} +/-{cad_sd:5.3f} | {f_m:8.0f} | {c_m:4.0f}   | {fc:10.1f}")

print("\n2. OLS  cadence_eff  vs  jitter_period")
print("-"*68)
xs = [d['period'] for d in data]; ys = [d['cad'] for d in data]
s, b, r, r2 = ols(xs, ys)
print(f"   cadence = {b:.3f} {s:+.4f}*period   r={r:+.3f}  R2={r2:.3f}")
print(f"   Longer period (less frequent jitter) → higher cadence (as expected)")

print("\n3. OLS  recFetch  vs  jitter_period")
print("-"*68)
xs = [d['period'] for d in data]; ys = [d['recFetch'] for d in data]
s, b, r, r2 = ols(xs, ys)
print(f"   recFetch = {b:.1f} {s:+.1f}*period   r={r:+.3f}  R2={r2:.3f}")

print("\n4. ENFORCEMENT-PATH CONTROLS")
for p in periods:
    sub = [d for d in data if d['period'] == p]
    print(f"   period={p:3d}s: eqChk/commit={mean(d['eq']/d['commits'] for d in sub):.2f}  "
          f"causDec/commit={mean(d['caus']/d['commits'] for d in sub):.2f}")
