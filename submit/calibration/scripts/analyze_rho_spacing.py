"""P0-2 rho-spacing analysis: actual rho-vs-cadence curve (sec.7.3 standalone calibration).

This supersedes analyze_rho_scan.py. The spacing sweep FIXES the design flaw:
   N=2 fixed, settleSeconds swept → genuine rho range → real degradation curve.

Also loads the original rho_scan data for the per-fault fixed-quantum finding.
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

# --- Spacing sweep (primary) ---
spacing_path = sys.argv[1] if len(sys.argv) > 1 else \
    "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage7_deployment/multivalidator/data/runs/rho_spacing_summary.csv"
try:
    spacing_rows = [r for r in load(spacing_path) if r['status'] == 'ok']
except (FileNotFoundError, KeyError):
    spacing_rows = []

if spacing_rows:
    data = []
    for r in spacing_rows:
        data.append({
            'settle': int(r['settle_s']), 'rep': int(r['rep']),
            'commits': int(r['commits']), 'wall': float(r['wallclock_s']),
            'cad': float(r['cadence_eff']), 'sumRes': float(r['sum_t_resume_s']),
            'recFetch': int(r['recFetch']), 'rho': float(r['rho']),
            'eq': int(r['eqChk']), 'caus': int(r['causDec']),
        })
    settles = sorted(set(d['settle'] for d in data))

    print("="*78)
    print(f"P0-2 RHO SPACING SWEEP — N={len(data)} runs, N=2 faults, settle ∈ {settles} s, dRec=1000ms")
    print("="*78)

    print("\n1. CELL MEANS BY SETTLE (higher settle → lower rho → higher cadence)")
    print("-"*74)
    print(f"   {'settle':>8s} {'rep':>3s} | {'rho':>10s} | {'cadence_eff':>14s} | {'recFetch':>10s} | {'t_resume':>10s}")
    for s in settles:
        sub = [d for d in data if d['settle'] == s]
        rho_m = mean(d['rho'] for d in sub); cad_m = mean(d['cad'] for d in sub)
        f_m = mean(d['recFetch'] for d in sub); r_m = mean(d['sumRes'] for d in sub)
        cs = stdev([d['cad'] for d in sub]) if len(sub) > 1 else 0
        print(f"   {s:6d}s {len(sub):3d} | {rho_m:10.7f} | {cad_m:7.3f} +/-{cs:5.3f} | {f_m:8.0f} | {r_m:8.1f}s")

    print("\n2. OLS  cadence_eff  vs  rho  (THE sec.7.3 degradation curve)")
    print("-"*74)
    xs = [d['rho'] for d in data]; ys = [d['cad'] for d in data]
    s, b, r, r2 = ols(xs, ys)
    print(f"   cadence_eff = {b:.3f} {s:+7.1f}*rho")
    print(f"   r={r:+.4f}  R2={r2:.4f}")
    if b > 0:
        rho_list = sorted(d['rho'] for d in data)
        for pct_rho in [rho_list[0], rho_list[len(rho_list)//2], rho_list[-1]]:
            pred = b + s * pct_rho
            print(f"     at rho={pct_rho:.7f}: predicted cadence={pred:.3f} ckpt/s")

    print("\n3. REVERSE: cadence vs settle (the independent variable)")
    print("-"*74)
    for s in settles:
        sub = [d for d in data if d['settle'] == s]
        if sub:
            print(f"   settle={s:4d}s: rho={mean(d['rho'] for d in sub):.7f}  "
                  f"cadence={mean(d['cad'] for d in sub):.3f} ± {stdev([d['cad'] for d in sub]):.3f}  "
                  f"recFetch={mean(d['recFetch'] for d in sub):7.0f}")

    print("\n4. RECOVERY COST vs rho")
    print("-"*74)
    for label, key in [("recFetch", "recFetch"), ("sum_t_resume_s", "sumRes")]:
        xs = [d['rho'] for d in data]; ys = [d[key] for d in data]
        s_r, b_r, r_r, r2_r = ols(xs, ys)
        print(f"   {label:16s}: slope={s_r:+.1f}/unit-rho  r={r_r:+.3f}  R2={r2_r:.3f}")

    print("\n5. PER-FAULT QUANTUM (cross-check against original rho scan)")
    print("-"*74)
    per_fault_rec = mean(d['recFetch'] for d in data) / 2
    per_fault_res = mean(d['sumRes'] for d in data) / 2
    print(f"   recFetch/fault: {per_fault_rec:.0f}  |  t_resume/fault: {per_fault_res:.1f}s")
    print(f"   original rho_scan had recFetch/fault≈147, t_resume/fault≈37s (Delta_recover=1000ms)")

    print("\n6. ENFORCEMENT-PATH CONTROLS")
    print("-"*74)
    for s in settles:
        sub = [d for d in data if d['settle'] == s]
        print(f"   settle={s:4d}s: eqChk/commit={mean(d['eq']/d['commits'] for d in sub):.2f}  "
              f"causDec/commit={mean(d['caus']/d['commits'] for d in sub):.2f}")

else:
    print("(no spacing data yet)")

# --- Original rho scan (secondary — per-fault fixed quantum) ---
rho_path = sys.argv[2] if len(sys.argv) > 2 else \
    "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage7_deployment/multivalidator/data/runs/rho_scan_summary.csv"
try:
    rho_rows = [r for r in load(rho_path) if r['status'] == 'ok']
except (FileNotFoundError, KeyError):
    rho_rows = []

if rho_rows:
    rho_data = []
    for r in rho_rows:
        rho_data.append({
            'N': int(r['fault_count']), 'cad': float(r['cadence_eff']),
            'recFetch': int(r['recFetch']), 'sumRes': float(r['sum_t_resume_s']),
            'rho': float(r['rho']), 'commits': int(r['commits']),
        })
    Ns = sorted(set(d['N'] for d in rho_data if d['N'] > 0))
    print("\n" + "="*78)
    print(f"SUPPLEMENTARY: original rho_scan (N={len(rho_data)} runs, N={0}..{max(Ns)})")
    print("="*78)
    print("rho was ~constant across all N>=1. The per-fault quantity IS the finding.")

    if Ns:
        per_fault_recs = [d['recFetch'] / d['N'] for d in rho_data if d['N'] > 0]
        per_fault_ress = [d['sumRes'] / d['N'] for d in rho_data if d['N'] > 0]
        print(f"  recFetch/fault: {mean(per_fault_recs):.0f} (±{stdev(per_fault_recs):.0f})")
        print(f"  t_resume/fault: {mean(per_fault_ress):.1f}s (±{stdev(per_fault_ress):.1f})")
        print(f"  cadence with ANY fault: {mean(d['cad'] for d in rho_data if d['N'] > 0):.3f} ckpt/s")
        print(f"  fault-free cadence (N=0): {mean(d['cad'] for d in rho_data if d['N'] == 0):.3f} ckpt/s")
