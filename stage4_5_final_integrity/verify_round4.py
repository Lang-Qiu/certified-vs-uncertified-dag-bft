"""Stage 4.5 Round 4 — INDEPENDENT data provenance verifier.

Deliberately does NOT import or reuse analyze_*.py. Fresh implementations of
mean/stdev/OLS/Pearson/R2, reading per-rep summary CSVs directly, to cross-check
every number backfilled into final/final_paper.md (Round 4). Guards against an
analyze-script bug being faithfully copied into the paper.
"""
import csv
from math import sqrt

RUNS = "E:/LQiu/lab_folder/Blockchain_final_pipeline/stage7_deployment/multivalidator/data/runs"

def load(name):
    with open(f"{RUNS}/{name}", encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f)]

def ok(rows):
    return [r for r in rows if r.get("status") == "ok"]

def mean(xs):
    xs = list(xs); return sum(xs) / len(xs) if xs else float("nan")

def sstdev(xs):  # sample stdev, ddof=1 (matches statistics.stdev)
    xs = list(xs); n = len(xs)
    if n < 2: return 0.0
    m = mean(xs); return sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))

def ols(xs, ys):
    n = len(xs); mx = mean(xs); my = mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    r = sxy / sqrt(sxx * syy) if sxx * syy > 0 else 0.0
    return slope, intercept, r, r * r

results = []
def chk(label, paper, recomputed, tol, fmt="{:.4g}"):
    okk = abs(paper - recomputed) <= tol
    results.append(okk)
    flag = "OK " if okk else "**MISMATCH**"
    print(f"  [{flag}] {label:<46s} paper={fmt.format(paper):>12s}  recomputed={fmt.format(recomputed):>12s}  (tol {tol})")

print("=" * 88)
print("PHASE A — INDEPENDENT RECOMPUTATION FROM PER-REP CSV  (Round 4 backfilled numbers)")
print("=" * 88)

# ---- §4.5  payload (P1-3) ----
print("\n§4.5  payload_size_summary.csv")
d = ok(load("payload_size_summary.csv"))
pad = [int(r["padding_bytes"]) for r in d]
eqpc = [int(r["eqChk"]) / int(r["commits"]) for r in d]
capc = [int(r["causDec"]) / int(r["commits"]) for r in d]
tr = [float(r["t_resume_s"]) for r in d]
print(f"   N ok rows = {len(d)} (paper: 9)")
chk("eqChk/commit vs payload  R2", 0.01, ols(pad, eqpc)[3], 0.015)
chk("causDec/commit vs payload  R2", 0.04, ols(pad, capc)[3], 0.015)
chk("t_resume vs payload  R2", 0.25, ols(pad, tr)[3], 0.02)

# ---- §5.2-5.3 / §5.4 negative control  chapter5 ----
print("\n§5.2-5.4  chapter5_enforcement_summary.csv")
c5 = ok(load("chapter5_enforcement_summary.csv"))
fetches = [int(r["recovery_fetches_total"]) for r in c5]
cad5 = [float(r["cadence_ckpt_s"]) for r in c5]
print(f"   N ok rows = {len(c5)} (paper: 40)")
results.append(len(c5) == 40); print(f"  [{'OK ' if len(c5)==40 else '**MISMATCH**'}] 40-run count")
allzero = all(f == 0 for f in fetches)
results.append(allzero); print(f"  [{'OK ' if allzero else '**MISMATCH**'}] recovery_fetches_total == 0 for ALL 40 (paper: all 0)  max={max(fetches)}")
chk("cadence min (paper >=4.0)", 4.0, min(cad5), 0.05)
chk("cadence max (paper <=4.7)", 4.7, max(cad5), 0.05)

# ---- §5.4 partition grid (P0-1) ----
print("\n§5.4  partition_grid_summary.csv")
pg = ok(load("partition_grid_summary.csv"))
rf = [int(r["v1_fetches"]) + int(r["v2_fetches"]) for r in pg]
drec = [int(r["recover_ms"]) / 1000.0 for r in pg]
trp = [float(r["t_resume_s"]) for r in pg]
gap = [int(r["disconnect_s"]) for r in pg]
print(f"   N ok rows = {len(pg)} (paper: 18)")
chk("recFetch min (paper 104)", 104, min(rf), 1)
chk("recFetch max (paper 1412)", 1412, max(rf), 1)
s, b, r, r2 = ols(drec, trp)
chk("t_resume vs Drec  slope s/1000ms (paper +20.0)", 20.0, s, 0.6)
chk("t_resume vs Drec  pooled r (paper +0.71)", 0.71, r, 0.02)
g90 = [(drec[i], trp[i]) for i in range(len(pg)) if gap[i] == 90]
g30 = [(drec[i], trp[i]) for i in range(len(pg)) if gap[i] == 30]
chk("gap=90 R2 (paper 0.99)", 0.99, ols([x for x,_ in g90],[y for _,y in g90])[3], 0.02)
chk("gap=30 R2 (paper 0.92)", 0.92, ols([x for x,_ in g30],[y for _,y in g30])[3], 0.02)

# ---- §7.3 rho spacing + rho scan ----
print("\n§7.3  rho_spacing_summary.csv")
rs = ok(load("rho_spacing_summary.csv"))
rho = [float(r["rho"]) for r in rs]
cad = [float(r["cadence_eff"]) for r in rs]
s, b, r, r2 = ols(rho, cad)
print(f"   N ok rows = {len(rs)} (paper: 12)")
chk("cadence vs rho  slope (paper -265)", -265.0, s, 5)
chk("cadence vs rho  intercept (paper 3.78)", 3.78, b, 0.03)
chk("cadence vs rho  r (paper -0.95)", -0.95, r, 0.02)
chk("cadence vs rho  R2 (paper 0.90)", 0.90, r2, 0.02)
# rho level means (4 settle levels)
for sv, paper_rho in [(20, 0.0077), (40, 0.0057), (80, 0.0037), (160, 0.0022)]:
    lv = mean(float(r["rho"]) for r in rs if int(r["settle_s"]) == sv)
    chk(f"rho mean @settle={sv}s (paper {paper_rho})", paper_rho, lv, 0.0003)
# per-fault quantum (N=2)
chk("spacing recFetch/fault (paper 143)", 143, mean(int(r["recFetch"]) for r in rs) / 2, 6)
chk("spacing t_resume/fault s (paper 37.9)", 37.9, mean(float(r["sum_t_resume_s"]) for r in rs) / 2, 2)

print("\n§7.3 (cross-check)  rho_scan_summary.csv")
rsc = ok(load("rho_scan_summary.csv"))
n0 = [float(r["cadence_eff"]) for r in rsc if int(r["fault_count"]) == 0]
nf = [float(r["cadence_eff"]) for r in rsc if int(r["fault_count"]) >= 1]
chk("N0 cadence (paper 4.32)", 4.32, mean(n0), 0.03)
chk("any-fault cadence (paper ~1.6)", 1.6, mean(nf), 0.1)
pf_rf = mean(int(r["recFetch"]) / int(r["fault_count"]) for r in rsc if int(r["fault_count"]) >= 1)
pf_tr = mean(float(r["sum_t_resume_s"]) / int(r["fault_count"]) for r in rsc if int(r["fault_count"]) >= 1)
chk("scan recFetch/fault (paper 164, range 143-164)", 164, pf_rf, 8)
chk("scan t_resume/fault s (paper 40.8, range 37-41)", 40.8, pf_tr, 3)

# ---- §7.4 gst jitter ----
print("\n§7.4  gst_jitter_summary.csv")
gj = ok(load("gst_jitter_summary.csv"))
per = [int(r["jitter_period_s"]) for r in gj]
cadg = [float(r["cadence_eff"]) for r in gj]
print(f"   N ok rows = {len(gj)} (paper: 9)")
chk("cadence vs period  R2 (paper 0.09)", 0.09, ols(per, cadg)[3], 0.02)
# per-period means within 4.14-4.38
pm = {p: mean(float(r["cadence_eff"]) for r in gj if int(r["jitter_period_s"]) == p) for p in (30, 60, 90)}
chk("cadence min over periods (paper 4.14)", 4.14, min(pm.values()), 0.03)
chk("cadence max over periods (paper 4.38)", 4.38, max(pm.values()), 0.03)

# ---- §7.5 net asymmetry ----
print("\n§7.5  net_asymmetry_summary.csv")
na = ok(load("net_asymmetry_summary.csv"))
def arm(a, col, f=float):
    return [f(r[col]) for r in na if r["arm"] == a]
off_c, on_c = mean(arm("asym_off","cadence_eff")), mean(arm("asym_on","cadence_eff"))
off_t, on_t = mean(arm("asym_off","t_resume_s")), mean(arm("asym_on","t_resume_s"))
off_f, on_f = mean(arm("asym_off","recFetch",int)), mean(arm("asym_on","recFetch",int))
chk("cert OFF cadence (paper 1.06)", 1.06, off_c, 0.02)
chk("cert ON cadence (paper 1.96)", 1.96, on_c, 0.02)
chk("cadence delta %% (paper +86)", 86.0, (on_c-off_c)/off_c*100, 2)
chk("cert OFF t_resume (paper 44.4)", 44.4, off_t, 0.5)
chk("cert ON t_resume (paper 26.1)", 26.1, on_t, 0.5)
chk("t_resume delta %% (paper -41)", -41.0, (on_t-off_t)/off_t*100, 2)
chk("cert OFF recFetch (paper 188)", 188, off_f, 1)
chk("cert ON recFetch (paper 97)", 97, on_f, 1)
chk("recFetch delta %% (paper -48)", -48.0, (on_f-off_f)/off_f*100, 2)
chk("cert OFF cadence stdev (paper 0.84)", 0.84, sstdev(arm("asym_off","cadence_eff")), 0.03)

print("\n" + "=" * 88)
n_pass = sum(1 for x in results if x); n_tot = len(results)
print(f"PHASE A RESULT: {n_pass}/{n_tot} checks reconciled" + ("  ✅ ALL PASS" if n_pass == n_tot else "  ❌ SEE MISMATCHES"))
print("=" * 88)
