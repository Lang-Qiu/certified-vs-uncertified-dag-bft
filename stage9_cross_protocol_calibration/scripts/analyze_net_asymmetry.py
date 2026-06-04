"""P1-4 Network Asymmetry — cert robustness under per-validator bandwidth limits (sec.7.5)."""
import csv, sys
from statistics import mean, stdev

def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

path = sys.argv[1] if len(sys.argv) > 1 else \
    "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage7_deployment/multivalidator/data/runs/net_asymmetry_summary.csv"
rows = [r for r in load(path) if r['status'] == 'ok']
data = {}
for r in rows:
    arm = r['arm']
    if arm not in data: data[arm] = []
    data[arm].append({
        'cad': float(r['cadence_eff']), 't_resume': float(r['t_resume_s']),
        'recFetch': int(r['recFetch']), 'commits': int(r['commits']),
        'eq': int(r['eqChk']), 'caus': int(r['causDec']),
    })

print("="*68)
print(f"P1-4 NETWORK ASYMMETRY — N={len(rows)} runs")
print("="*68)
for arm_label, desc in [("asym_off","asymmetric 1Mbps cert=OFF"),
                         ("asym_on", "asymmetric 1Mbps cert=ON"),
                         ("sym_ref", "symmetric baseline cert=OFF")]:
    if arm_label not in data: continue
    d = data[arm_label]
    print(f"\n  {desc} ({len(d)} reps):")
    print(f"    cadence_eff = {mean(x['cad'] for x in d):.3f} ± {stdev([x['cad'] for x in d]):.3f} ckpt/s")
    print(f"    t_resume    = {mean(x['t_resume'] for x in d):.1f} ± {stdev([x['t_resume'] for x in d]):.1f} s")
    print(f"    recFetch    = {mean(x['recFetch'] for x in d):.0f} ± {stdev([x['recFetch'] for x in d]):.0f}")
    print(f"    commits     = {mean(x['commits'] for x in d):.0f}")
    print(f"    eqChk/commit= {mean(x['eq']/x['commits'] for x in d):.2f}")
    print(f"    causDec/commit={mean(x['caus']/x['commits'] for x in d):.2f}")

if 'asym_off' in data and 'asym_on' in data:
    off = data['asym_off']; on = data['asym_on']
    cad_off = mean(x['cad'] for x in off); cad_on = mean(x['cad'] for x in on)
    t_off = mean(x['t_resume'] for x in off); t_on = mean(x['t_resume'] for x in on)
    f_off = mean(x['recFetch'] for x in off); f_on = mean(x['recFetch'] for x in on)
    print(f"\n  Δ (cert ON - OFF):")
    print(f"    cadence: {cad_on-cad_off:+.3f} ckpt/s ({100*(cad_on-cad_off)/cad_off:+.1f}%)")
    print(f"    t_resume: {t_on-t_off:+.1f}s ({100*(t_on-t_off)/t_off:+.1f}%)")
    print(f"    recFetch: {f_on-f_off:+.0f} ({100*(f_on-f_off)/f_off:+.1f}%)")
    print(f"\n  INTERPRETATION: if cert=ON shows HIGHER cadence / LOWER t_resume / LOWER recFetch")
    print(f"  under the same 1Mbps asymmetry, certification's up-front amortization is a")
    print(f"  robustness asset — confirming the sec.7.5 claim.")

if 'sym_ref' in data and 'asym_off' in data:
    sym = data['sym_ref']; asym = data['asym_off']
    print(f"\n  Asymmetry cost (cert=OFF):")
    print(f"    cadence drop: {mean(x['cad'] for x in sym)-mean(x['cad'] for x in asym):.3f} ckpt/s")
    print(f"    t_resume add: {mean(x['t_resume'] for x in asym)-mean(x['t_resume'] for x in sym):.1f}s")
