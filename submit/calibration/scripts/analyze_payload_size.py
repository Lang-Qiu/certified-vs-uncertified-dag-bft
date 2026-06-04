"""P1-3 Payload Size analysis — physical vs logical invariant scaling (§4.5)."""
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
    "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage7_deployment/multivalidator/data/runs/payload_size_summary.csv"
rows = [r for r in load(path) if r['status'] == 'ok']
data = []
for r in rows:
    data.append({
        'pad': int(r['padding_bytes']), 'commits': int(r['commits']),
        'cad': float(r['cadence_eff']), 't_resume': float(r['t_resume_s']),
        'recFetch': int(r['recFetch']),
        'eq': int(r['eqChk']), 'caus': int(r['causDec']),
    })
pads = sorted(set(d['pad'] for d in data))

print("="*70)
print(f"P1-3 PAYLOAD SIZE — N={len(data)} runs, pads={pads}")
print("="*70)

def pad_label(b):
    if b == 0: return '0'
    if b < 10240: return f'{b//1024}KB'
    if b < 1048576: return f'{b//1024}KB'
    return f'{b//1048576}MB'

print("\n1. CELL MEANS")
print("-"*68)
print(f"   {'padding':>10s} | {'t_resume':>12s} | {'recFetch':>10s} | {'cadence':>10s} | {'eqChk/cm':>10s} | {'causDec/cm':>12s}")
for pad in pads:
    sub = [d for d in data if d['pad'] == pad]
    tr = mean(d['t_resume'] for d in sub)
    rf = mean(d['recFetch'] for d in sub)
    cd = mean(d['cad'] for d in sub)
    eq = mean(d['eq']/d['commits'] for d in sub)
    ca = mean(d['caus']/d['commits'] for d in sub)
    print(f"   {pad_label(pad):>10s} | {tr:9.1f}s | {rf:10.0f} | {cd:10.3f} | {eq:10.2f} | {ca:12.2f}")

print("\n2. t_resume vs padding_bytes (PHYSICAL — should scale)")
print("-"*68)
xs = [d['pad'] for d in data]; ys = [d['t_resume'] for d in data]
s, b, r, r2 = ols(xs, ys)
per_kb = s * 1024  # slope per KB
print(f"   t_resume = {b:.2f} + {per_kb*1e3:+.2f}s/MB   r={r:+.3f}  R2={r2:.3f}")
print(f"   Per 1KB padding: +{s*1024*1000:.1f}us per block fetch cost")

print("\n3. recFetch vs padding_bytes (should be FLAT — same # blocks)")
print("-"*68)
xs2 = [d['pad'] for d in data]; ys2 = [d['recFetch'] for d in data]
s2, b2, r2v, r22 = ols(xs2, ys2)
print(f"   recFetch = {b2:.1f} {s2:+.4f}*bytes   r={r2v:+.3f}  R2={r22:.3f}")

print("\n4. eqChk/commit & causDec/commit vs padding (LOGICAL — should be FLAT)")
print("-"*68)
for label, key in [("eqChk/commit", "eq"), ("causDec/commit", "caus")]:
    xs3 = [d['pad'] for d in data]; ys3 = [d[key]/d['commits'] for d in data]
    s3, b3, r3, r23 = ols(xs3, ys3)
    print(f"   {label:18s}: intercept={b3:.2f}  slope/MB={s3*1e6:+.2f}  r={r3:+.3f}  R2={r23:.3f}")

print("\n5. VERDICT")
print("="*68)
print("   Physical (t_resume): ", end="")
if r2 > 0.5 and s > 0:
    print(f"SCALES with payload (R²={r2:.3f}, +{per_kb*1000:.1f}us/KB) → §4.5 confirmed")
else:
    print(f"UNCLEAR (R²={r2:.3f}) — may need more reps or larger padding")

print("   Logical (eqChk/causDec): ", end="")
if r23 < 0.3:
    print(f"FLAT (R²={r23:.3f}) → §4.5 confirmed")
else:
    print(f"check (R²={r23:.3f})")
