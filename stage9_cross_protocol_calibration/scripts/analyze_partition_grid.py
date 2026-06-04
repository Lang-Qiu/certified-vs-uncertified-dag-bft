"""P0-1 partition grid analysis: the §5.4 contingent-liability boundary.

Three things to establish:
  1. PULL activation (recFetch>0) under DISCONNECTION at every gap level
     -> contrast with the Chapter-5 loss scan where recFetch=0 at 0-10% loss.
  2. t_resume dose-response to Delta_recover (the cost, once PULL is on the critical path).
  3. Fetch-count INVERSE response to Delta_recover (more per-fetch delay -> fewer RPCs
     issued before catch-up completes), cross-checked against Phase A.
"""
import csv, sys
from statistics import mean, stdev
from math import sqrt

def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs)
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    syy = sum((y-my)**2 for y in ys)
    slope = sxy/sxx if sxx else 0
    intercept = my - slope*mx
    r = sxy/sqrt(sxx*syy) if sxx*syy > 0 else 0
    return slope, intercept, r, r*r

path = sys.argv[1] if len(sys.argv) > 1 else \
    "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage7_deployment/multivalidator/data/runs/partition_grid_summary.csv"
rows = [r for r in load(path) if r['status'] == 'ok']
data = []
for r in rows:
    data.append({
        'gap': int(r['disconnect_s']),
        'ms': int(r['recover_ms']),
        'rep': int(r['rep']),
        't_resume': float(r['t_resume_s']),
        'fetch': int(r['v1_fetches']) + int(r['v2_fetches']),
        'missed': int(r['cp_gap']) - int(r['cp_before']),
        'eq': int(r['eqChk']),
        'caus': int(r['causDec']),
    })

gaps = sorted(set(d['gap'] for d in data))
mss = sorted(set(d['ms'] for d in data))

print("="*78)
print(f"P0-1 PARTITION GRID — N={len(data)} runs ({len(gaps)} gaps x {len(mss)} Delta_recover x reps)")
print("="*78)

# ---- 1. PULL activation check ----
print("\n1. PULL ACTIVATION (recFetch = v1+v2) — does disconnection cross the cliff?")
print("-"*70)
all_pos = all(d['fetch'] > 0 for d in data)
print(f"   Every run recFetch>0: {'YES' if all_pos else 'NO'}  "
      f"(min={min(d['fetch'] for d in data)}, max={max(d['fetch'] for d in data)})")
print("   -> Contrast: Chapter-5 loss scan (0-10% indep. loss) had recFetch=0 in ALL 40 runs.")
print("   -> The cliff is DISCONNECTION, not loss; even a 30s partition activates PULL.")

# ---- 2. cell means ----
print("\n2. CELL MEANS  (t_resume seconds / fetch count / missed ckpts)")
print("-"*70)
print(f"   {'gap':>4s} {'dRec':>6s} | {'t_resume':>16s} | {'fetch(v1+v2)':>18s} | {'missed':>8s}")
for g in gaps:
    for m in mss:
        sub = [d for d in data if d['gap'] == g and d['ms'] == m]
        if not sub: continue
        tr = [d['t_resume'] for d in sub]; fe = [d['fetch'] for d in sub]
        ms_ = [d['missed'] for d in sub]
        tr_sd = stdev(tr) if len(tr) > 1 else 0
        fe_sd = stdev(fe) if len(fe) > 1 else 0
        print(f"   {g:4d} {m:6d} | {mean(tr):8.1f} +/-{tr_sd:5.1f} | {mean(fe):9.0f} +/-{fe_sd:6.0f} | {mean(ms_):8.0f}")

# ---- 3. t_resume vs Delta_recover ----
print("\n3. OLS  t_resume  vs  Delta_recover  (the contingent-liability dose-response)")
print("-"*70)
xs = [d['ms'] for d in data]; ys = [d['t_resume'] for d in data]
s, b, r, r2 = ols(xs, ys)
print(f"   POOLED: t_resume = {b:.1f} + {s*1000:+.1f}*(Delta_recover/1000ms)   "
      f"r={r:+.3f}  R2={r2:.3f}")
print(f"           => +{s*1000:.1f} s of recovery stall per +1000ms Delta_recover")
for g in gaps:
    xs = [d['ms'] for d in data if d['gap'] == g]
    ys = [d['t_resume'] for d in data if d['gap'] == g]
    s, b, r, r2 = ols(xs, ys)
    print(f"   gap={g:2d}s: slope={s*1000:+.1f} s/1000ms  intercept={b:.1f}s  r={r:+.3f}  R2={r2:.3f}")

# ---- 4. fetch vs Delta_recover (inverse) ----
print("\n4. OLS  fetch_count  vs  Delta_recover  (inverse: slower RPCs -> fewer issued)")
print("-"*70)
xs = [d['ms'] for d in data]; ys = [d['fetch'] for d in data]
s, b, r, r2 = ols(xs, ys)
print(f"   POOLED: slope={s*1000:+.1f} fetches/1000ms  r={r:+.3f}  R2={r2:.3f}")
for g in gaps:
    xs = [d['ms'] for d in data if d['gap'] == g]
    ys = [d['fetch'] for d in data if d['gap'] == g]
    s, b, r, r2 = ols(xs, ys)
    print(f"   gap={g:2d}s: slope={s*1000:+.1f} fetches/1000ms  r={r:+.3f}  R2={r2:.3f}")

# ---- 5. gap-duration effect at Delta_recover=0 ----
print("\n5. GAP-DURATION EFFECT at Delta_recover=0 (does longer partition cost more?)")
print("-"*70)
for g in gaps:
    sub = [d for d in data if d['gap'] == g and d['ms'] == 0]
    print(f"   gap={g:2d}s: t_resume={mean(d['t_resume'] for d in sub):5.1f}s  "
          f"fetch={mean(d['fetch'] for d in sub):6.0f}  missed={mean(d['missed'] for d in sub):5.0f} ckpts")

# ---- 6. enforcement-path controls ----
print("\n6. ENFORCEMENT-PATH CONTROLS (eqChk / causDec — should track commits, not fault)")
print("-"*70)
for g in gaps:
    sub = [d for d in data if d['gap'] == g]
    print(f"   gap={g:2d}s: eqChk={mean(d['eq'] for d in sub):6.0f}  causDec={mean(d['caus'] for d in sub):6.0f}")
print("   (decline with gap = fewer commits during longer stall; paths themselves never gated off)")
