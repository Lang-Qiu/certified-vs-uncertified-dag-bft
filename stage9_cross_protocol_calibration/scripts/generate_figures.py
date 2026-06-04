"""Generate publication-quality figures from all completed experiment CSVs.

Output: stage9_cross_protocol_calibration/figures/
Format: 300 DPI PNG (also PDF for LaTeX embedding)
Font: DejaVu Sans (free, consistent across platforms)
"""
import csv, os, sys
from statistics import mean, stdev
from math import sqrt, pi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(os.path.dirname(BASE), "stage7_deployment", "multivalidator", "data", "runs")
OUT = os.path.join(BASE, "figures")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'legend.fontsize': 9,
})

# ----- colour palette -----
C_EQ = '#1b9e77'     # green: eq path (flat)
C_CAUS = '#d95f02'   # orange: causal path (flat)
C_REC = '#e7298a'    # magenta: recovery/PULL (contingent)
C_CAD = '#7570b3'    # purple: cadence
C_CERT = '#66a61e'   # dark green: cert ON
C_UNCERT = '#e6ab02' # gold: cert OFF
C_GAP = {30: '#e41a1c', 60: '#377eb8', 90: '#4daf4a'}  # red/blue/green

def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def ols(xs, ys):
    n = len(xs); mx, my = sum(xs)/n, sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs)
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    syy = sum((y-my)**2 for y in ys)
    slope = sxy/sxx if sxx else 0
    intercept = my - slope*mx
    r = sxy/sqrt(sxx*syy) if sxx*syy > 0 else 0
    return slope, intercept, r, r*r

# ======================================================================
# FIGURE 1 — Chapter 5 Enforcement Scan: recFetch vs loss rate
# ======================================================================
def fig_ch5_recfetch():
    path = os.path.join(DATA, "chapter5_enforcement_summary.csv")
    rows = [r for r in load(path) if r['status'] == 'ok']
    loss_levels = sorted(set(int(r['loss_pct']) for r in rows))
    committees = sorted(set(int(r['committee']) for r in rows))

    fig, ax = plt.subplots(figsize=(8, 5))
    markers = {7: 'o', 4: 's'}
    for n in committees:
        xs, ys, ys_err = [], [], []
        for loss in loss_levels:
            sub = [int(r['recovery_fetches_total']) for r in rows
                   if int(r['loss_pct']) == loss and int(r['committee']) == n]
            xs.append(loss); ys.append(mean(sub))
            ys_err.append(stdev(sub) if len(sub) > 1 else 0)
        ax.errorbar(xs, ys, yerr=ys_err, marker=markers[n], color=C_REC if n==7 else C_EQ,
                     capsize=4, label=f'n={n}', markersize=8, linewidth=1.8)
    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Independent Packet Loss (%)')
    ax.set_ylabel('recFetch (PULL activation count)')
    ax.set_title('Figure 5-1: PULL Recovery Activation vs Packet Loss Rate\n(§5.3 Safety Zone — recFetch=0 at 0–10% loss)')
    ax.legend()
    ax.set_xticks(loss_levels)
    ax.annotate('PUSH absorbs loss;\nPULL never fires',
                xy=(5, 5), fontsize=10, color=C_REC, fontstyle='italic',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig5-1_recFetch_vs_loss.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 2 — Chapter 5: per-commit eqChk & causDec vs loss (flat paths)
# ======================================================================
def fig_ch5_flat_paths():
    path = os.path.join(DATA, "chapter5_enforcement_summary.csv")
    rows = [r for r in load(path) if r['status'] == 'ok']
    loss_levels = sorted(set(int(r['loss_pct']) for r in rows))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    for n, marker, label in [(7, 'o', 'n=7'), (4, 's', 'n=4')]:
        for ax, field, color, title in [
            (ax1, 'equivoc_checks_total', C_EQ, 'Path A: Non-Equivocation'),
            (ax2, 'causal_decisions_total', C_CAUS, 'Path B: Causal-History'),
        ]:
            xs, ys, ys_err = [], [], []
            for loss in loss_levels:
                sub = [(int(r[field]), float(r['cadence_ckpt_s']) * 90)  # per-90s window
                       for r in rows if int(r['loss_pct']) == loss and int(r['committee']) == n]
                vals = [v / c if c > 0 else 0 for v, c in sub]
                xs.append(loss); ys.append(mean(vals))
                ys_err.append(stdev(vals) if len(vals) > 1 else 0)
            ax.errorbar(xs, ys, yerr=ys_err, marker=marker, color=color,
                         capsize=4, label=label, markersize=8, linewidth=1.8)
        ax.set_xlabel('Loss (%)')
        ax.set_ylabel('Per-Commit Cost')
        ax.set_title(title)
        ax.legend()
        ax.set_xticks(loss_levels)

    fig.suptitle('Figure 5-2: Per-Commit Enforcement Cost — Fixed Overhead (§5.2 Paths A/B)', fontsize=13)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig5-2_flat_paths.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 3 — P0-1 Partition Grid: t_resume vs Delta_recover (dose-response)
# ======================================================================
def fig_partition_grid():
    path = os.path.join(DATA, "partition_grid_summary.csv")
    rows = [r for r in load(path) if r['status'] == 'ok']
    gaps = sorted(set(int(r['disconnect_s']) for r in rows))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: t_resume vs Delta_recover
    for g in gaps:
        subs = [(int(r['recover_ms']), float(r['t_resume_s']))
                for r in rows if int(r['disconnect_s']) == g]
        xs = sorted(set(x for x,_ in subs))
        ymeans = [mean([y for x2,y in subs if x2==x]) for x in xs]
        s, b, r, r2 = ols([s[0] for s in subs], [s[1] for s in subs])
        ax1.plot(xs, [b + s*x for x in xs], '--', color=C_GAP[g], alpha=0.4, linewidth=1)
        ax1.scatter([s[0] for s in subs], [s[1] for s in subs], color=C_GAP[g],
                     marker='o', s=50, alpha=0.7,
                     label=f'gap={g}s (R²={r2:.2f})')
    ax1.set_xlabel('Δ_recover (ms)')
    ax1.set_ylabel('t_resume (s)')
    ax1.set_title('Recovery Stall vs Δ_recover')
    ax1.legend()

    # Right: recFetch vs Delta_recover (inverse)
    for g in gaps:
        subs = [(int(r['recover_ms']), int(r['v1_fetches']) + int(r['v2_fetches']))
                for r in rows if int(r['disconnect_s']) == g]
        xs = sorted(set(x for x,_ in subs))
        ymeans = [mean([y for x2,y in subs if x2==x]) for x in xs]
        ax2.plot(xs, ymeans, 'o-', color=C_GAP[g], linewidth=1.8, markersize=7,
                 label=f'gap={g}s')
    ax2.set_xlabel('Δ_recover (ms)')
    ax2.set_ylabel('recFetch (v1+v2)')
    ax2.set_title('PULL Fetch Count vs Δ_recover (Inverse)')
    ax2.legend()

    fig.suptitle('Figure 5-3: Contingent-Liability Dose-Response — §5.4 Partition Grid', fontsize=13)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig5-3_partition_grid.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 4 — Partition Grid: eqChk / causDec controls (flat, not gated)
# ======================================================================
def fig_partition_controls():
    path = os.path.join(DATA, "partition_grid_summary.csv")
    rows = [r for r in load(path) if r['status'] == 'ok']
    gaps = sorted(set(int(r['disconnect_s']) for r in rows))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    for g in gaps:
        ms_levels = sorted(set(int(r['recover_ms']) for r in rows if int(r['disconnect_s']) == g))
        for ax, field, color, title in [
            (ax1, 'eqChk', C_EQ, 'eqChk Total'), (ax2, 'causDec', C_CAUS, 'causDec Total'),
        ]:
            yvals = [mean([int(r[field]) for r in rows
                          if int(r['disconnect_s']) == g and int(r['recover_ms']) == m])
                     for m in ms_levels]
            ax.plot(ms_levels, yvals, 'o-', color=C_GAP[g], linewidth=1.8, markersize=7,
                     label=f'gap={g}s')
        ax.set_xlabel('Δ_recover (ms)')
        ax.set_ylabel('Total Count')
        ax.set_title(title)
        ax.legend()

    fig.suptitle('Figure 5-4: Enforcement-Path Controls — eqChk/causDec Not Gated by Fault (§5.2)', fontsize=13)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig5-4_partition_controls.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 5 — P0-2 Rho Spacing: cadence_eff vs rho (sec.7.3 degradation curve)
# ======================================================================
def fig_rho_degradation():
    path = os.path.join(DATA, "rho_spacing_summary.csv")
    rows = [r for r in load(path) if r['status'] == 'ok']
    if not rows:
        print("  (no rho spacing data yet)")
        return
    data = [(float(r['rho']), float(r['cadence_eff'])) for r in rows]
    xs, ys = [d[0] for d in data], [d[1] for d in data]
    s, b, r, r2 = ols(xs, ys)

    # Also load fault-free baseline
    rho_path = os.path.join(DATA, "rho_scan_summary.csv")
    ff_rows = [r for r in load(rho_path) if r['status'] == 'ok' and int(r['fault_count']) == 0]
    ff_cad = mean(float(r['cadence_eff']) for r in ff_rows) if ff_rows else None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(xs, ys, c=C_REC, s=70, alpha=0.8, edgecolors='black', linewidth=0.5,
               label=f'N=2, spacing sweep (R²={r2:.3f})')
    x_line = np.linspace(min(xs) * 0.8, max(xs) * 1.1, 100)
    ax.plot(x_line, b + s * x_line, '--', color=C_REC, alpha=0.6, linewidth=1.5,
            label=f'OLS: cadence = {b:.2f} {s:+.1f}·ρ')

    # Mark fault-free cadence as horizontal reference
    if ff_cad:
        ax.axhline(y=ff_cad, color='gray', linestyle=':', alpha=0.6, linewidth=1)
        ax.annotate(f'fault-free λ₀={ff_cad:.2f} ckpt/s', xy=(x_line[30], ff_cad + 0.05),
                     fontsize=9, color='gray')

    # (removed an extraneous ρ* crossing annotation here: it was not referenced
    #  by the figure caption and was easily confused with the distinct §7.6.3
    #  crossover ρ*; it also overlapped the fit line.)

    ax.set_xlabel('ρ (fault density = N / commits)')
    ax.set_ylabel('cadence_eff (ckpt/s)')
    ax.set_title('Figure 7-6: Cadence Degradation vs Fault Density ρ (§7.3)\nDirect Deployment Measurement')
    ax.legend()
    ax.set_xlim(0, max(xs) * 1.1)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig7-1_rho_degradation.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 6 — Per-fault quantum cross-validation (rho_scan + rho_spacing)
# ======================================================================
def fig_per_fault_quantum():
    rho_path = os.path.join(DATA, "rho_scan_summary.csv")
    ro_rows = [r for r in load(rho_path) if r['status'] == 'ok' and int(r['fault_count']) > 0]
    sp_path = os.path.join(DATA, "rho_spacing_summary.csv")
    sp_rows = [r for r in load(sp_path) if r['status'] == 'ok']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: recFetch vs fault_count (original rho_scan)
    Ns_rec = {}
    for r in ro_rows:
        n = int(r['fault_count'])
        Ns_rec.setdefault(n, []).append(int(r['recFetch']) / n)
    xs_rec = sorted(Ns_rec.keys())
    y_rec = [mean(Ns_rec[n]) for n in xs_rec]
    y_err = [stdev(Ns_rec[n]) if len(Ns_rec[n]) > 1 else 0 for n in xs_rec]
    ax1.errorbar(xs_rec, y_rec, yerr=y_err, marker='D', color=C_REC, capsize=4,
                  linewidth=1.8, markersize=8, label='original ρ scan')

    # Also plot spacing sweep per-fault
    if sp_rows:
        sp_mean = mean((int(r['recFetch']) / 2) for r in sp_rows)
        ax1.axhline(y=sp_mean, color=C_EQ, linestyle='--', linewidth=1.2,
                     label=f'spacing sweep (mean={sp_mean:.0f})')

    ax1.set_xlabel('Fault Count (N)')
    ax1.set_ylabel('recFetch / Fault')
    ax1.set_title('Per-Fault recFetch Quantum')
    ax1.legend()

    # Right: t_resume vs fault_count
    Ns_res = {}
    for r in ro_rows:
        n = int(r['fault_count'])
        Ns_res.setdefault(n, []).append(float(r['sum_t_resume_s']) / n)
    xs_res = sorted(Ns_res.keys())
    y_res = [mean(Ns_res[n]) for n in xs_res]
    y_err2 = [stdev(Ns_res[n]) if len(Ns_res[n]) > 1 else 0 for n in xs_res]
    ax2.errorbar(xs_res, y_res, yerr=y_err2, marker='D', color=C_CAD, capsize=4,
                  linewidth=1.8, markersize=8, label='original ρ scan')

    if sp_rows:
        sp_mean_r = mean(float(r['sum_t_resume_s']) / 2 for r in sp_rows)
        ax2.axhline(y=sp_mean_r, color=C_EQ, linestyle='--', linewidth=1.2,
                     label=f'spacing sweep (mean={sp_mean_r:.1f}s)')

    ax2.set_xlabel('Fault Count (N)')
    ax2.set_ylabel('t_resume / Fault (s)')
    ax2.set_title('Per-Fault Recovery Stall Quantum')
    ax2.legend()

    fig.suptitle('Figure 7-2: Fixed Marginal Cost of Recovery Faults — §7.2 Cost Model Validation', fontsize=13)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig7-2_per_fault_quantum.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 7 — P1-4 Network Asymmetry: cert ON vs OFF under bw limit
# ======================================================================
def fig_net_asymmetry():
    path = os.path.join(DATA, "net_asymmetry_summary.csv")
    try:
        rows = [r for r in load(path) if r['status'] == 'ok']
    except (FileNotFoundError, KeyError):
        print("  (no net asymmetry data yet)")
        return
    if len(rows) < 2:
        return

    arms = ['asym_off', 'asym_on', 'sym_ref']
    labels = ['Asym cert=OFF', 'Asym cert=ON', 'Sym ref']
    colors = [C_UNCERT, C_CERT, '#888888']
    cad = []; cad_err = []; tres = []; tres_err = []; rf = []; rf_err = []
    for arm in arms:
        sub = [r for r in rows if r['arm'] == arm]
        if not sub: cad.append(0); cad_err.append(0); tres.append(0); tres_err.append(0); rf.append(0); rf_err.append(0); continue
        cads = [float(r['cadence_eff']) for r in sub]
        cad.append(mean(cads)); cad_err.append(stdev(cads) if len(cads) > 1 else 0)
        ts = [float(r['t_resume_s']) for r in sub]
        tres.append(mean(ts)); tres_err.append(stdev(ts) if len(ts) > 1 else 0)
        fs = [int(r['recFetch']) for r in sub]
        rf.append(mean(fs)); rf_err.append(stdev(fs) if len(fs) > 1 else 0)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13, 5))
    x = np.arange(len(arms))
    w = 0.5

    bars1 = ax1.bar(x, cad, w, yerr=cad_err, color=colors, capsize=5, edgecolor='black', linewidth=0.5)
    ax1.set_xticks(x); ax1.set_xticklabels(labels, rotation=15)
    ax1.set_ylabel('cadence_eff (ckpt/s)')
    ax1.set_title('Cadence')

    bars2 = ax2.bar(x, tres, w, yerr=tres_err, color=colors, capsize=5, edgecolor='black', linewidth=0.5)
    ax2.set_xticks(x); ax2.set_xticklabels(labels, rotation=15)
    ax2.set_ylabel('t_resume (s)')
    ax2.set_title('Recovery Time')

    bars3 = ax3.bar(x, rf, w, yerr=rf_err, color=colors, capsize=5, edgecolor='black', linewidth=0.5)
    ax3.set_xticks(x); ax3.set_xticklabels(labels, rotation=15)
    ax3.set_ylabel('recFetch')
    ax3.set_title('PULL Fetch Count')

    fig.suptitle('Figure 7-3: Network Asymmetry — Certification as Robustness Asset (§7.5)\n1Mbps on 2 validators, rotation fault', fontsize=13)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig7-3_net_asymmetry.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 8 — Phase A Critical Path: t_resume vs Delta_recover (historical)
# ======================================================================
def fig_phaseA_criticalpath():
    path = os.path.join(DATA, "phaseA_criticalpath_summary.csv")
    try:
        rows = [r for r in load(path) if r['status'] == 'ok']
    except (FileNotFoundError, KeyError):
        return
    if not rows: return

    data = [(int(r['recover_ms']), float(r['t_resume_s']), int(r['v1_fetches']) + int(r['v2_fetches']))
            for r in rows]
    ms_levels = sorted(set(d[0] for d in data))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    xs = [d[0] for d in data]; ys_t = [d[1] for d in data]; ys_f = [d[2] for d in data]

    for ms in ms_levels:
        tsub = [d[1] for d in data if d[0] == ms]
        fsub = [d[2] for d in data if d[0] == ms]
        ax1.scatter([ms]*len(tsub), tsub, c=C_REC, s=40, alpha=0.6)
        ax2.scatter([ms]*len(fsub), fsub, c=C_REC, s=40, alpha=0.6)

    s_t, b_t, r_t, r2_t = ols(xs, ys_t)
    s_f, b_f, r_f, r2_f = ols(xs, ys_f)
    x_line = np.linspace(0, max(xs)*1.1, 100)

    ax1.plot(x_line, b_t + s_t * x_line, '--', color=C_REC, alpha=0.7,
             label=f'OLS: +{s_t*1000:.1f}s/1000ms (R²={r2_t:.3f})')
    ax1.set_xlabel('Δ_recover (ms)'); ax1.set_ylabel('t_resume (s)')
    ax1.set_title('Phase A: t_resume vs Δ_recover')
    ax1.legend()

    ax2.plot(x_line, b_f + s_f * x_line, '--', color=C_REC, alpha=0.7,
             label=f'OLS: {s_f*1000:+.1f} fetches/1000ms (R²={r2_f:.3f})')
    ax2.set_xlabel('Δ_recover (ms)'); ax2.set_ylabel('recFetch')
    ax2.set_title('Phase A: recFetch vs Δ_recover')
    ax2.legend()

    fig.suptitle('Figure 7-4: Phase A Critical-Path Calibration — Δ_recover Dose-Response (§7.6.2)', fontsize=13)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig7-4_phaseA_criticalpath.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 9 — Phase 2c Excess Sweep: super-additivity
# ======================================================================
def fig_excess_sweep():
    path = os.path.join(DATA, "phase2c_excess_sweep_summary.csv")
    try:
        rows = [r for r in load(path) if r['status'] == 'ok']
    except (FileNotFoundError, KeyError):
        return
    if not rows: return

    # Generic: if the CSV has expected columns, plot them
    cols = list(rows[0].keys())
    numeric_cols = [c for c in cols if c not in ('status', 'run_id', 'rep')]

    fig, ax = plt.subplots(figsize=(8, 5))
    if 'fault_count' in cols and 'excess' in cols:
        # excess over additivity vs fault count
        fc_levels = sorted(set(int(r['fault_count']) for r in rows))
        xs, ys, ys_err = [], [], []
        for fc in fc_levels:
            sub = [float(r['excess']) for r in rows if int(r['fault_count']) == fc]
            xs.append(fc); ys.append(mean(sub))
            ys_err.append(stdev(sub) if len(sub) > 1 else 0)
        ax.errorbar(xs, ys, yerr=ys_err, marker='D', color=C_REC, capsize=4,
                     linewidth=1.8, markersize=8)
        ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
        ax.set_xlabel('Fault Count'); ax.set_ylabel('Excess Over Additivity')
        ax.set_title('Figure 7-5: Super-Additivity — §7.6.1 Excess Sweep')

    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig7-5_excess_sweep.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 10 — Phase 1b Δ_save calibration
# ======================================================================
def fig_dsave():
    path = os.path.join(DATA, "phase1b_dsave_calibration_summary.csv")
    try:
        rows = [r for r in load(path) if r['status'] == 'ok']
    except (FileNotFoundError, KeyError):
        return
    if not rows: return

    fig, ax = plt.subplots(figsize=(8, 5))
    # Try the expected fields
    if 'recover_ms' in rows[0] and 'delta_save' in rows[0]:
        ms_levels = sorted(set(int(r['recover_ms']) for r in rows))
        xs, ys, ys_err = [], [], []
        for ms in ms_levels:
            sub = [float(r['delta_save']) for r in rows if int(r['recover_ms']) == ms]
            xs.append(ms); ys.append(mean(sub))
            ys_err.append(stdev(sub) if len(sub) > 1 else 0)
        ax.errorbar(xs, ys, yerr=ys_err, marker='D', color=C_CERT, capsize=4,
                     linewidth=1.8, markersize=8)
        ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
        ax.set_xlabel('Δ_recover (ms)'); ax.set_ylabel('Δ_save (s)')
        ax.set_title('Figure 7-6: Δ_save — Certified Arm Net Saving (§7.6.3)')

    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig7-6_dsave.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 11 — Combined View: Safety Zone + Cliff
# ======================================================================
def fig_combined_cliff():
    """Side-by-side: Chapter-5 loss (recFetch=0 for loss) + P0-1 grid (recFetch>0 for partition)"""
    ch5_path = os.path.join(DATA, "chapter5_enforcement_summary.csv")
    pg_path = os.path.join(DATA, "partition_grid_summary.csv")
    ch5_rows = [r for r in load(ch5_path) if r['status'] == 'ok']
    pg_rows = [r for r in load(pg_path) if r['status'] == 'ok']

    fig, ax = plt.subplots(figsize=(10, 5))

    # Left side: loss scan (recFetch=0 everywhere)
    loss_vals = sorted(set(int(r['loss_pct']) for r in ch5_rows))
    for loss in loss_vals:
        subs = [int(r['recovery_fetches_total']) for r in ch5_rows if int(r['loss_pct']) == loss]
        ax.scatter([loss]*len(subs), subs, c=C_EQ, s=30, alpha=0.5, marker='o')

    # Right side: partition grid (recFetch>0)
    gap_offset = {30: 12, 60: 14, 90: 16}
    for g, gx in gap_offset.items():
        subs = [(int(r['recover_ms']), int(r['v1_fetches']) + int(r['v2_fetches']))
                for r in pg_rows if int(r['disconnect_s']) == g]
        for ms, fetches in subs:
            ax.scatter(gx, fetches, c=C_GAP[g], s=40, alpha=0.6, marker='^',
                       label=f'gap={g}s' if ms == 0 else '')
        # Remove duplicate labels
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())

    ax.axhline(y=0, color='gray', linestyle=':', alpha=0.5)
    ax.axvline(x=10.5, color=C_REC, linestyle='--', linewidth=2, alpha=0.7)
    ax.annotate('SAFETY ZONE\n(PUSH absorbs loss)\nrecFetch=0', xy=(5, 800),
                fontsize=11, fontweight='bold', color=C_EQ,
                ha='center', bbox=dict(boxstyle='round,pad=0.5', facecolor='#e8f5e9'))
    ax.annotate('CLIFF\n(partition triggers PULL)\nrecFetch>0', xy=(15, 800),
                fontsize=11, fontweight='bold', color=C_REC,
                ha='center', bbox=dict(boxstyle='round,pad=0.5', facecolor='#fce4ec'))

    ax.set_xlabel('Fault Type / Severity')
    ax.set_ylabel('recFetch (PULL Activation Count)')
    ax.set_title('Figure 5-5: The Contingent-Liability Boundary — §5.4 Safety Zone + Cliff', fontsize=13)
    ax.set_xlim(-1, 18)
    ax.set_xticks([0, 2, 5, 10, 12, 14, 16])
    ax.set_xticklabels(['loss=0%', 'loss=2%', 'loss=5%', 'loss=10%', 'gap=30s', 'gap=60s', 'gap=90s'], rotation=20)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig5-5_combined_cliff.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 12 — P1-5 GST Jitter
# ======================================================================
def fig_gst_jitter():
    path = os.path.join(DATA, "gst_jitter_summary.csv")
    try:
        rows = [r for r in load(path) if r['status'] == 'ok']
    except (FileNotFoundError, KeyError):
        return
    if len(rows) < 3: return
    periods = sorted(set(int(r['jitter_period_s']) for r in rows))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    for ax, field, color, ylabel in [
        (ax1, 'cadence_eff', C_CAD, 'cadence_eff (ckpt/s)'),
        (ax2, 'recFetch', C_REC, 'recFetch'),
    ]:
        xs, ys, ys_err = [], [], []
        for p in periods:
            sub = [float(r[field]) for r in rows if int(r['jitter_period_s']) == p]
            xs.append(p); ys.append(mean(sub))
            ys_err.append(stdev(sub) if len(sub) > 1 else 0)
        ax.errorbar(xs, ys, yerr=ys_err, marker='D', color=color, capsize=4,
                     linewidth=1.8, markersize=8)
        s, b, r, r2 = ols(xs, ys)
        if len(xs) > 1:
            x_line = np.linspace(min(xs)*0.9, max(xs)*1.1, 100)
            ax.plot(x_line, b + s*x_line, '--', color=color, alpha=0.4, label=f'R2={r2:.3f}')
        ax.set_xlabel('Jitter Period (s)'); ax.set_ylabel(ylabel)
        ax.set_title(ylabel); ax.legend()
    fig.suptitle('Figure 7-7: GST Jitter — Cadence Under Partial Synchrony (§7.4)', fontsize=13)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig7-7_gst_jitter.{fmt}'))
    plt.close(fig)

# ======================================================================
# FIGURE 13-14 — P1-3 Payload Size
# ======================================================================
def fig_payload_size():
    path = os.path.join(DATA, "payload_size_summary.csv")
    try:
        rows = [r for r in load(path) if r['status'] == 'ok']
    except (FileNotFoundError, KeyError):
        return
    if len(rows) < 3: return
    pads = sorted(set(int(r['padding_bytes']) for r in rows))
    def pl(b):
        if b == 0: return '0'
        if b < 10240: return f'{b//1024}KB'
        if b < 1048576: return f'{b//1024}KB'
        return f'{b//1048576}MB'
    labels = [pl(p) for p in pads]; xi = range(len(pads))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    for ax, field, color, title in [
        (ax1, 't_resume_s', C_REC, 'Recovery Time (Physical)'),
        (ax2, 'recFetch', C_EQ, 'PULL Fetch Count'),
    ]:
        ys, ye = [], []
        for pad in pads:
            sub = [float(r[field]) for r in rows if int(r['padding_bytes']) == pad]
            ys.append(mean(sub)); ye.append(stdev(sub) if len(sub) > 1 else 0)
        ax.errorbar(xi, ys, yerr=ye, marker='D', color=color, capsize=4, linewidth=1.8, markersize=8)
        ax.set_xticks(xi); ax.set_xticklabels(labels)
        ax.set_xlabel('Block Padding'); ax.set_title(title)
    fig.suptitle('Figure 4-1: Payload Size — Physical vs Logical Invariant (§4.5)', fontsize=13)
    fig.tight_layout()
    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(OUT, f'fig4-1_payload_size.{fmt}'))
    plt.close(fig)

    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(12, 5))
    for ax, field, color, title in [
        (ax3, 'eqChk', C_EQ, 'eqChk/commit (Logical)'),
        (ax4, 'causDec', C_CAUS, 'causDec/commit (Logical)'),
    ]:
        ys, ye = [], []
        for pad in pads:
            sub = [(int(r[field]), int(r['commits'])) for r in rows if int(r['padding_bytes']) == pad]
            vals = [v/c if c > 0 else 0 for v, c in sub]
            ys.append(mean(vals)); ye.append(stdev(vals) if len(vals) > 1 else 0)
        ax.errorbar(xi, ys, yerr=ye, marker='s', color=color, capsize=4, linewidth=1.8, markersize=8)
        ax.set_xticks(xi); ax.set_xticklabels(labels)
        ax.set_xlabel('Block Padding'); ax.set_title(title)
    fig2.suptitle('Figure 4-2: Payload Controls — Logical Paths Stay Flat (§4.5)', fontsize=13)
    fig2.tight_layout()
    for fmt in ['png', 'pdf']:
        fig2.savefig(os.path.join(OUT, f'fig4-2_payload_controls.{fmt}'))
    plt.close(fig2)

# ======================================================================
# TABLE — Experiment coverage index
# ======================================================================
def table_coverage():
    out_path = os.path.join(OUT, "experiment_index.csv")
    index_rows = [
        ("fig5-1","§5.3","recFetch vs loss rate","Chapter 5 enforcement scan",40),
        ("fig5-2","§5.2","eqChk/causDec per-commit vs loss","Chapter 5 enforcement scan",40),
        ("fig5-3","§5.4","t_resume/fetch vs Δ_recover","P0-1 partition grid",18),
        ("fig5-4","§5.2","eqChk/causDec controls vs Δ_recover","P0-1 partition grid",18),
        ("fig5-5","§5.3-5.4","Safety zone + cliff combined","Chapter 5 + P0-1 merged",58),
        ("fig7-1","§7.3","cadence vs ρ degradation curve","P0-2 ρ spacing sweep",12),
        ("fig7-2","§7.2","per-fault cost quantum","P0-2 ρ scan + spacing",27),
        ("fig7-3","§7.5","cert ON vs OFF under 1Mbps","P1-4 network asymmetry",9),
        ("fig7-4","§7.6.2","Phase A critical-path dose-response","Phase A rotation",12),
        ("fig7-5","§7.6.1","super-additivity excess sweep","Phase 2c excess sweep",20),
        ("fig7-6","§7.6.3","Δ_save certified arm calibration","Phase 1b Δ_save",12),
        ("fig7-7","§7.4","cadence vs GST jitter period","P1-5 GST jitter",9),
        ("fig4-1","§4.5","t_resume vs payload size","P1-3 payload scan",15),
        ("fig4-2","§4.5","eqChk/causDec per-commit vs payload","P1-3 payload scan",15),
        ("table-1","§9","experiment index (this table)","all experiments",285),
    ]
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(["figure","section","what","experiment","runs"])
        w.writerows(index_rows)

# ======================================================================
# Main
# ======================================================================
if __name__ == '__main__':
    print(f"Generating figures → {OUT}/")
    funcs = [
        ('fig5-1', fig_ch5_recfetch),
        ('fig5-2', fig_ch5_flat_paths),
        ('fig5-3', fig_partition_grid),
        ('fig5-4', fig_partition_controls),
        ('fig5-5', fig_combined_cliff),
        ('fig7-1', fig_rho_degradation),
        ('fig7-2', fig_per_fault_quantum),
        ('fig7-3', fig_net_asymmetry),
        ('fig7-4', fig_phaseA_criticalpath),
        ('fig7-5', fig_excess_sweep),
        ('fig7-6', fig_dsave),
        ('fig7-7', fig_gst_jitter),
        ('fig4-1', fig_payload_size),
    ]
    for name, fn in funcs:
        try:
            fn()
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
    table_coverage()
    print(f"Done — {len(funcs)} figures + coverage table.")
