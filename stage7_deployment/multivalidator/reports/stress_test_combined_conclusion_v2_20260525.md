# Additivity stress test — combined conclusion **v2** (full 2×2 + corrected Test 1)

- Generated (UTC): 2026-05-25T13:00:00+00:00
- Supersedes: `reports/stress_test_combined_conclusion_20260525.md` (v1)
- Scope: synthesis of (a) canonical decoupling + (b) extreme additivity stress + (c) cross-scale ablation + (d) qdisc-fix Test 1 rerun + (e) n=4 high-intensity quadrant
- Total formal reps used: 190 (60 original n=7 + 20 decoupling n=7 + 40 extreme n=7 + 40 ablation n=4 + 10 qdisc-fix Test 1 + 20 n=4 high-intensity)
- Linked artifacts:
  - Canonical n=7 conclusion: `reports/fault_decoupling_conclusion_20260525.md`
  - Extreme stress test (Tests 0/1/2): `reports/fault_decoupling_extreme_conclusion_20260525.md`
  - Cross-scale ablation table: `reports/scale_ablation_n4_vs_n7_20260525105002.md`
  - Test 1 qdisc-fix result: `reports/test1_qdiscfix_result_20260525.md`
  - n=4 high-intensity true-cadence: `reports/summary_true_n4_high_20260525.md`
  - Combined true-cadence summaries: `reports/summary_true_with_n4_20260525.md`, `reports/summary_true_qdiscfix_20260525.md`

## TL;DR

Cross-validator additivity of network faults on consensus cadence depends on **two independent stress axes**: (i) per-fault intensity and (ii) fault count relative to the BFT bound `f`. Within both axes the protocol shows clean additivity; crossing either produces super-additive p95 tail inflation. With the missing quadrant now measured, the full 2×2 stability map looks like:

| | moderate intensity (2% loss) | high intensity (5% loss) |
|---|---|---|
| **within f** (fault count ≤ f) | **additive** — Test 0 @ n=7: ratio **1.03**; Test 1 (fixed) @ n=7: ratio **1.00** | **super-additive** — Test 2 @ n=7: ratio **1.35** |
| **at/above f** (fault count ≥ f) | **super-additive** — n=4 ablation: ratio **1.16** | **super-additive** — n=4 + 5% loss: ratio **1.17** |

A separate methodology finding from the **original** Test 1 (`tc qdisc replace` overwrite bug) inflated the apparent additivity story; the **corrected** Test 1 result is now in the table and confirms the within-f / moderate-intensity additive verdict regardless of fault co-location.

## 1. The five data points

### 1.1 Test 0 (canonical, n=7, f=2, cross-validator, 2% loss): additive ✓

| metric | observed | expected_additive | ratio |
|---|---:|---:|---:|
| p50_true | 216.4 | 214.6 | **1.01** |
| p95_true | 267.5 | 258.5 | **1.03** |
| max_true | 2325.7 | 2242.0 | 1.04 |
| n_>2000 ms | 2 | 2 | 1.00 |

Re-confirmation of the canonical decoupling finding.

### 1.2 Test 1 (qdisc-fix, n=7, f=2, same-validator, 2% loss): additive ✓ (NEW, corrected)

| metric | observed | expected_additive | ratio | Δ_excess |
|---|---:|---:|---:|---:|
| p50_true | 216.5 | 214.1 | 1.011 | +2.4 ms |
| **p95_true** | **260.5** | **259.8** | **1.003** | **+0.7 ms** |
| max_true | 2425.3 | 2270.4 | 1.068 | +154.9 ms |

The original Test 1 (`delay_loss_same_v1`, broken orchestration) showed p95 = 241.8 ms, indistinguishable from loss-only (265.6 ms). With the orchestration fix (`scripts/run_experiment_matrix_qdiscfix.ps1` groups netem clauses per target into a single `tc qdisc replace`), p95 jumps to 260.5 ms — almost exactly the additive prediction. CV(p95) tightens from 8.83% (bimodal) to 1.63%, removing the spurious sub-additivity signal.

**Implication**: same-validator stacking and cross-validator placement give the same additivity verdict at moderate intensity. The original Test 1's "sub-additive" finding was an instrumentation artifact, not a protocol property.

### 1.3 Test 2 (n=7, f=2, cross-validator, 5% loss): super-additive ✗

| metric | observed | expected_additive | ratio | Δ_excess |
|---|---:|---:|---:|---:|
| p95_true | 290.9 | 215.8 | **1.35** | **+75.1 ms** |
| max_true | 2297.5 | 2251.3 | 1.02 | +46.2 ms |
| n_500–2000 ms | 9 | 3 | **3.00** | **+6 events** |

Single-seed result. Mechanism hypothesis unchanged from v1: 5% loss alone locks v2 out of the fast quorum; adding delay on v1 forces protocol mode-switching, producing tail inflation.

### 1.4 n=4 ablation, moderate intensity (2% loss): super-additive ✗

| metric | observed (n=4) | expected_additive (n=4) | ratio |
|---|---:|---:|---:|
| p50_true | 210.8 | 211.1 | 1.00 |
| **p95_true** | **372.7** | **320.2** | **1.16** |
| max_true | 1564.2 | 1615.8 | 0.97 |

Same physical fault parameters as Test 0; only n changes. Crossing the BFT bound (2 faults > f=1) breaks additivity even at moderate intensity.

### 1.5 n=4 + high intensity (5% loss on v2 + delay on v1): super-additive ✗ (NEW, missing-quadrant cell)

| metric | baseline_n4 | delay_only_v1_n4 | loss_high_v2_n4 | observed | expected | ratio | Δ_excess |
|---|---:|---:|---:|---:|---:|---:|---:|
| p50_true | 210.3 | 210.7 | 212.7 | 213.9 | 213.1 | 1.004 | +0.8 ms |
| **p95_true** | **212.3** | **318.4** | **238.8** | **402.4** | **344.9** | **1.17** | **+57.5 ms** |
| max_true | 1566.1 | 1572.0 | 1997.4 | 1941.3 | 2003.3 | 0.97 | −62.0 ms |
| n_500–2000 ms | 2 | 2 | 1 | 3 | 1 | 3.00 | +2 |

**Key cross-comparison**: at n=4, jumping intensity from 2% to 5% only nudges the ratio from 1.16 → 1.17 — i.e., **once the BFT-bound axis has already broken, additional intensity adds essentially nothing** to the breakdown signal. Whereas at n=7 within f, the same intensity jump pushes ratio 1.03 → 1.35. The two stress axes therefore do **not** compose linearly; the larger of the two effects appears to saturate the breakdown.

## 2. The unifying picture (revised)

The full 2×2 surface (§ TL;DR) reveals three qualitative findings:

1. **Within the additive cell (low/low), the protocol absorbs independent faults cleanly across both fault-placement variants** (Test 0 cross-validator: 1.03; Test 1 same-validator fixed: 1.00). Additivity is robust to placement.
2. **Crossing either axis alone produces super-additivity at the +50–75 ms p95 level** (n=4 ablation: +52 ms; Test 2: +75 ms).
3. **Crossing both axes simultaneously does not double the effect** (n=4 + 5% loss: +57 ms, comparable to crossing the BFT axis alone). The two breakdown mechanisms appear to share a common bottleneck (e.g., fast-quorum participation) that, once disturbed, cannot be doubly disturbed.

Finding 3 is the new structural insight enabled by filling the missing quadrant. It implies a single dominant breakdown mode rather than two independent ones, which constrains the mechanism hypothesis space.

## 3. Measurement caveats (updated)

1. **ckpt_count discrepancy at n=4**: n=4 reps produce ~125 checkpoints per rep vs ~637 at n=7 — a 5× difference (shorter effective measurement window at n=4). Cadence percentiles still comparable as intensive properties; absolute event counts (`n_>2000_ms`, `n_500_2000_ms`) not directly comparable across scales.
2. **Original Test 1 invalidity → corrected**: `tc qdisc replace` bug is documented in `reports/test1_qdiscfix_result_20260525.md`. Fix is in `scripts/run_experiment_matrix_qdiscfix.ps1` (groups netem clauses per target). Original numbers are kept in the dataset for transparency; v2 of this report uses the corrected numbers for the verdict.
3. **One outlier in `pressure_high_loss_rep06`** (Test 2): max = 13 s. Does not affect the median-based super-additivity claim; flagged but kept.
4. **Seed coverage**:
   - canonical n=7: seed 2026052402
   - Test 1 (fixed): seed 20260525
   - Test 2: seed 20260525
   - n=4 ablation (2% loss): seed 20260525
   - n=4 high-intensity: seed 20260525
   All non-canonical cells are single-seed. Replicating Test 2, n=4 ablation, and n=4 high-intensity with one independent seed each (~30 min compute per cell) would strengthen the four super-additive cells.

## 4. Two distinct findings vs one composite finding (updated)

**Claim A — operational stability under moderate stress** (unchanged):
> Under typical operational conditions (n=7, f=2, fault count ≤ f, per-fault intensity at industry-standard SLA values), independent network faults combine **additively** on consensus cadence — regardless of whether they target distinct validators or stack on one. The system has no hidden synergistic blow-up at this regime. [Evidence: Test 0 ratio 1.03; Test 1 (fixed) ratio 1.00.]

**Claim B — boundary behavior near BFT and intensity limits** (sharpened):
> The additive property is **not** universal. At smaller committee size where fault count meets/exceeds f, OR at higher per-fault intensity, the tail latency exhibits super-additive inflation of ~+50–75 ms in p95. These boundary regimes require explicit reasoning rather than extrapolation from in-bound measurements. **Furthermore**, crossing both axes simultaneously does not compound — the breakdown signals share a common bottleneck and saturate at one another's level. [Evidence: n=4 ablation 1.16, Test 2 1.35, n=4 + 5% loss 1.17 (saturated relative to n=4 alone).]

Both claims are publishable; Claim B (now with the saturation observation) is the more interesting one for the paper's positioning.

## 5. Implications for the paper (updated)

Per `[[paper-integration-approval-gate]]`, nothing has been written to `final/final_paper.md` or `stage8_paper_integration/`. Three candidate revision points were drafted in `paper_integration_prep/`:

1. **RP-1** (§7.6 + §7.6.1 cross-scale evidence): now stronger — the 2×2 is complete; the cell labels in `paper_integration_prep/RP1_scale_ablation_evidence.md` should be updated to use the 1.00/1.03/1.16/1.17/1.35 figures and reflect the saturation observation.
2. **RP-2** (§8.4 falsifiable prediction): now sharper — the prediction can be restated as "fault additivity holds within a single-axis stress region; crossing either axis breaks additivity by +50–75 ms at p95; crossing both does not compound." Crossing-both being non-compounding is a non-trivial, novel sub-prediction.
3. **RP-3** (§9 methodology footnote): now constructive — the qdisc bug is **fixed**, not just disclosed. The footnote should pair the disclosure with the correction outcome.

The updated prep notes will be regenerated as `paper_integration_prep/RP1_v2_*.md` etc. if the user signals approval to revise them; until then, v1 prep notes stand and v2 of this report serves as the authoritative source for any future revision.

## 6. Recommended next steps (updated)

| priority | item | cost | rationale |
|---|---|---|---|
| HIGH | Update `paper_integration_prep/RP*.md` to reflect v2 numbers | ~30 min | Keep prep memo in sync with final data |
| MEDIUM | Replicate Test 2 with one independent seed | ~30 min | Single-seed risk for Claim B's high-intensity arm |
| MEDIUM | Replicate n=4 ablation with one independent seed | ~2.5 h | Single-seed risk for Claim B's BFT-axis arm |
| LOW | Replicate n=4 + high-intensity with one independent seed | ~1 h | Confirms saturation observation |
| LOW | Test the prediction at n=10 (in-bound, moderate) to confirm baseline additivity at larger scale | ~3 h | Strengthens generality |
| OPTIONAL | Visualize the 2×2 surface as a single figure | ~15 min | Useful for §7.6.1 if RP-1 is approved |

Total cost to fully back v2 claims: ~4 h additional compute on existing infrastructure.
