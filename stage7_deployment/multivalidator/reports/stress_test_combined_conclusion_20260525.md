# Additivity stress test — combined conclusion (Tests 0/1/2 + scale ablation)

- Generated (UTC): 2026-05-25T11:00:00+00:00
- Scope: combined synthesis of (a) canonical decoupling + (b) extreme additivity stress + (c) cross-scale ablation
- Total formal reps used: 160 (60 original n=7 + 20 decoupling n=7 + 40 extreme n=7 + 40 ablation n=4)
- Linked artifacts:
  - Canonical n=7 conclusion: `reports/fault_decoupling_conclusion_20260525.md`
  - Extreme stress test (Tests 0/1/2): `reports/fault_decoupling_extreme_conclusion_20260525.md`
  - Cross-scale ablation table: `reports/scale_ablation_n4_vs_n7_20260525105002.md`
  - Combined true-cadence summary: `reports/summary_true_with_n4_20260525.md`

## TL;DR

The additivity of `delay + loss` cross-validator faults on consensus cadence is **conditional on being within the BFT tolerance bound**:

| condition | n / f | fault count | additivity verdict | p95 ratio | Δ_excess on p95 |
|---|---|---|---|---:|---:|
| canonical n=7, 2% loss | 7 / 2 | 2 (= f) | **additive** | 1.03 | +9 ms |
| **n=4 ablation, 2% loss** | **4 / 1** | **2 (> f)** | **super-additive** | **1.16** | **+52 ms** |
| n=7 + 5% loss | 7 / 2 | 2 (= f) but higher intensity | **super-additive** | 1.35 | +75 ms |

Additivity holds only when (a) fault count is at or below f, **AND** (b) per-fault intensity stays moderate. Pushing either dimension breaks additivity and produces tail inflation that cannot be predicted from single-fault measurements.

A separate methodology finding (Test 1) exposed a `tc qdisc replace` bug in the orchestration that prevents same-validator fault stacking from working as intended.

## 1. The four data points

### 1.1 Test 0 (canonical, n=7, f=2, 2 faults): additive ✓

| metric | observed | expected_additive | ratio |
|---|---:|---:|---:|
| p50_true | 216.4 | 214.6 | **1.01** |
| p95_true | 267.5 | 258.5 | **1.03** |
| max_true | 2325.7 | 2242.0 | 1.04 |
| n_>2000 ms | 2 | 2 | 1.00 |

All ratios in 1.00–1.06 across 6 metrics. (a)'s finding re-confirmed.

### 1.2 Test 1 (same-validator stacking, n=7): methodologically invalid

`run_experiment_matrix.ps1:294-302` uses `tc qdisc replace` for each fault. When two faults target the same container, the second `replace` overwrites the first — the delay disappears, leaving only the loss qdisc active. Empirically `delay_loss_same_v1` ≈ `loss_only_v1` within rep-to-rep bimodal noise.

**Recommendation**: fix by grouping faults per target and emitting one combined `netem delay … loss …` clause. ~1 hour engineering; then re-run 10 reps.

### 1.3 Test 2 (n=7 with 5% loss instead of 2%): super-additive

| metric | observed | expected_additive | ratio | Δ_excess |
|---|---:|---:|---:|---:|
| p95_true | 290.9 | 215.8 | **1.35** | **+75.1 ms** |
| max_true | 2297.5 | 2251.3 | 1.02 | +46.2 ms |
| n_500–2000 ms | 9 | 3 | **3.00** | **+6 events** |

Mechanism hypothesis: 5%-loss alone locks the protocol into a deterministic "v2-out-of-fast-quorum" cadence (p95 = 222 ms, lower than baseline 263 ms). Adding delay on v1 disturbs the lock-in, forcing the protocol to mode-switch between including and excluding v2 — the resulting jitter shows up as p95 tail inflation. One rep06 outlier (max 13 s) is flagged but does not drive the median-based conclusion.

### 1.4 Scale ablation: same canonical scenario at n=4 (f=1): super-additive

Replicating Test 0's scenario at n=4 (delay v1 + loss v2 at the same physical parameters), but where 2 faults now exceeds the BFT bound (f=1):

| metric | observed (n=4) | expected_additive (n=4) | ratio | n=7 ratio (for reference) |
|---|---:|---:|---:|---:|
| p50_true | 210.8 | 211.1 | 1.00 | 1.01 |
| **p95_true** | **372.7** | **320.2** | **1.16** | **1.03** |
| max_true | 1564.2 | 1615.8 | 0.97 | 1.04 |
| ckpt_count | 124 | 127 | 0.98 | 1.06 |

p50 stable across both scales (the cadence still ticks at ~210 ms). What breaks at n=4 is the **tail**: p95 ratio jumps from 1.03 (n=7) to 1.16 (n=4), Δ_excess from +9 ms to +52 ms.

Notable cross-scale single-fault patterns (`scale_ablation_n4_vs_n7_20260525105002.md`):
- baseline p95 drops from 263 ms (n=7) to 212 ms (n=4) — smaller committee → tighter cadence
- delay_only_v1 p95 goes UP at n=4 (318 vs 257 ms, ratio 1.24) — with f=1, delays on one validator have nowhere to "hide"; the protocol cannot route around them as it could with f=2 at n=7
- loss_only_v2 p95 stays low at n=4 (214 ms) — loss alone doesn't add a per-rep delay floor

## 2. The unifying picture

Both the higher-intensity (Test 2) and the smaller-committee (n=4) regimes exhibit the **same qualitative break**: cross-validator faults that combine cleanly under moderate stress start producing super-additive tail inflation once the protocol's slack runs out.

The slack runs out in two distinct ways:
- **Test 2**: per-fault intensity exceeds what the protocol can absorb in steady state — 5% loss is enough to push the protocol into one fragile cadence regime, and adding a delay forces it to switch between regimes.
- **n=4 ablation**: fault count exceeds the formal BFT bound (2 > f=1) — the protocol still progresses but loses its ability to absorb stragglers cleanly.

This suggests a **two-axis stability map** worth investigating further:

```
              moderate intensity              high intensity
within f      additive (canonical n=7)        super-additive (Test 2 @ n=7, 5%)
at/above f    super-additive (n=4 ablation)   ??? (untested — likely large)
```

The lower-right cell (`at/above f` × `high intensity`) was not tested and would be the natural next data point if we wanted to map out the full stability surface.

## 3. Measurement caveats

1. **ckpt_count discrepancy at n=4**: n=4 reps produce ~125 checkpoints per rep vs ~637 at n=7 — a 5× difference. This likely reflects a difference in the duration of fullnode log coverage at n=4 (shorter effective measurement window). Cadence percentiles (p50/p95) and tail counts are still comparable because they are intensive properties of the per-checkpoint interval distribution, but **absolute event counts (`n_>2000_ms`, `n_500_2000_ms`) at n=4 are not directly comparable to n=7**. Ratios in the n=4 additivity test row "n_>2000 ms" are NaN because all four cells happen to have zero events in the shorter window. The cross-scale section flags these explicitly.

2. **Test 1 invalidity**: documented above; no fix attempted, just flagged.

3. **One outlier in `pressure_high_loss_rep06`** (Test 2): max = 13 s. Does not affect the median-based super-additivity claim; flagged but kept in the dataset.

4. **Single seed family for the new cells**: (b) used seed 20260525, (c) also seed 20260525. Replicating Test 2 and the n=4 result with one independent seed (~30 min compute each) would strengthen both findings.

## 4. Two distinct findings vs one composite finding

The combined data supports two related but distinct claims:

**Claim A** (operational stability under moderate stress):
> Under typical operational conditions (n=7, f=2, fault count ≤ f, per-fault intensity at industry-standard SLA values), independent network faults combine **additively** on consensus cadence. The system has no hidden synergistic blow-up at this regime.

**Claim B** (boundary behavior near BFT and intensity limits):
> The additive property is **not** universal. At smaller committee size where fault count meets/exceeds f, OR at higher per-fault intensity, the tail latency exhibits super-additive inflation of ~+50–75 ms in p95. These boundary regimes require explicit reasoning rather than extrapolation from in-bound measurements.

Both claims are publishable; Claim B is the more interesting one for the paper's positioning.

## 5. Implications for the paper

Per `[[paper-integration-approval-gate]]`, nothing has been written to `final/final_paper.md` or `stage8_paper_integration/`. The findings above are candidates for:

1. **Strengthening the "stability under pressure" subsection**: replace any "stable across all tested conditions" wording with the more accurate "additive within BFT bound at moderate intensity; super-additive at boundaries."
2. **Adding a scale-ablation table or figure**: the n=4 vs n=7 cross-scale data is original deployment evidence not previously in the paper.
3. **Adding a methodology footnote**: the rpc-probe variance distortion (from (a)) and the `tc qdisc replace` orchestration limit (from Test 1) belong in a methodology/limitations section.
4. **Optional citation hook**: the two-axis stability map (§2) frames a natural future-work item.

No revision text drafted here — awaits user approval gate.

## 6. Recommended next steps (not auto-executed)

1. Fix `tc qdisc` orchestration bug, then re-run Test 1 (10 reps, ~30 min). Resolves the methodological hole.
2. Replicate Test 2 with a second seed (10 reps, ~30 min). Strengthens Claim B.
3. Replicate n=4 ablation with a second seed (40 reps, ~2.5 h). Strengthens scale-ablation evidence.
4. Optional: add the untested "n=4 + 5% loss" quadrant — the lower-right of §2's stability map (40 reps × ~3 min = ~2 h).

Total cost to fully back the combined claims: ~5–6 hours additional compute on the existing infrastructure.
