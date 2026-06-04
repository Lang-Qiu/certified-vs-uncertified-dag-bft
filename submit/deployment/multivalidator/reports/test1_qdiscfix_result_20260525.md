# Test 1 (qdisc-fix) result: same-validator stacking is **additive** when measured correctly

- Generated (UTC): 2026-05-25T12:00:00+00:00
- Configuration: n=7, f=2, scenario `delay_loss_same_v1_fixed` (delay 150±30 ms + 2% loss, both on validator-1), 10 reps, seed 20260525
- Orchestration: `scripts/run_experiment_matrix_qdiscfix.ps1` (groups all netem faults per target into one combined `tc qdisc replace dev eth0 root netem delay ... loss ...` call)
- Source: `data/runs/delay_loss_same_v1_fixed_seed20260525_rep[01-10]/metrics/consensus_metrics_true.json`

## TL;DR

The original Test 1 (`delay_loss_same_v1`, broken orchestration) gave p95_true = 241.8 ms, indistinguishable from loss-only (265.6 ms) — we interpreted it as "delay disappeared because the second `tc qdisc replace` overwrote the first." That interpretation is now confirmed: with the combined-clause fix, the same scenario produces p95_true = 260.5 ms, almost exactly matching `expected_additive = delay_only + loss_only − baseline = 259.8 ms` (ratio 1.003).

**Conclusion**: same-validator stacking at moderate intensity is additive, in line with Test 0 (cross-validator). The original Test 1 "sub-additive" finding was a measurement artifact.

## Additivity table

| metric | baseline | delay_only_v1 | loss_only_v1 | observed (fixed) | expected_additive | ratio | Δ_excess |
|---|---:|---:|---:|---:|---:|---:|---:|
| p50_true | 215.0 | 215.0 | 214.1 | 216.5 | 214.1 | 1.011 | +2.4 ms |
| **p95_true** | **263.2** | **257.4** | **265.6** | **260.5** | **259.8** | **1.003** | **+0.7 ms** |
| max_true | 1945.2 | 2224.4 | 1991.2 | 2425.3 | 2270.4 | 1.068 | +154.9 ms |
| n_intervals_gt_2000ms | 0 | 2 | 0 | 2 | 2 | 1.00 | 0 |

p50 and p95 are within noise of additive. max shows ~7% inflation but max is high variance (one rep with 3.7 s tail dominates).

## Per-rep raw

| rep | p50_true | p95_true | max_true | n_>2000 | n_500_2000 |
|---:|---:|---:|---:|---:|---:|
| 1 | 215.1 | 259.6 | 2425.3 | 2 | 3 |
| 2 | 214.8 | 260.5 | 2074.8 | 2 | 4 |
| 3 | 215.2 | 255.4 | 2300.4 | 2 | 3 |
| 4 | 215.0 | 258.8 | 2157.0 | 1 | 3 |
| 5 | 216.5 | 258.2 | 2785.1 | 2 | 3 |
| 6 | 217.6 | 266.0 | 2546.7 | 2 | 2 |
| 7 | 218.7 | 266.8 | 2572.4 | 3 | 3 |
| 8 | 218.7 | 265.9 | 2916.5 | 4 | 2 |
| 9 | 218.3 | 267.4 | 2419.9 | 4 | 4 |
| 10 | 217.0 | 264.7 | 3698.0 | 4 | 3 |

CV(p50)=0.73%, CV(p95)=1.63% — much tighter than the broken-orchestration version's bimodal p95 (CV 8.83%, with rep-level p95 oscillating between ~220 ms and ~265 ms). The fix not only changes the central tendency but also collapses the bimodality, indicating that delay was indeed being silently dropped on some reps.

## Implications for the combined stress-test story

This result simplifies §1.2 of `stress_test_combined_conclusion_20260525.md`:

- ~~Test 1: sub-additive (methodology invalid)~~ → **Test 1 (corrected): additive, ratio 1.00**
- Test 0 (cross-validator, moderate intensity): additive ✓
- **Test 1 (same-validator, moderate intensity): additive ✓** (new, corrected)
- Test 2 (cross-validator, high intensity): super-additive (ratio 1.35)
- n=4 ablation (cross-validator, fault count > f): super-additive (ratio 1.16)

The four data points now form a clean 2×2 if we add the missing quadrant (G3: n=4 + high intensity, in progress):

```
              moderate intensity              high intensity
within f      ADDITIVE  (Test 0, Test 1)      SUPER-ADDITIVE  (Test 2)
                 ratio 1.00–1.03                  ratio 1.35
at/above f    SUPER-ADDITIVE  (n=4 ablation)   ???  (G3 in progress)
                 ratio 1.16                       data point landing soon
```

Test 1's correction strengthens Claim A (additivity holds across both fault placements within the additive regime) and Claim B (super-additivity is driven by intensity/fault-count escape, not by mere co-location of faults on one validator).

## Methodology footnote candidate (carried over)

The qdisc-replace bug is the canonical example for RP-3 (`paper_integration_prep/RP3_methodology_footnote.md`). With this rerun, the disclosure can now be paired with a constructive correction rather than just a flag: "The bug was identified, fixed, and the corrected Test 1 result confirms the same additivity verdict that Test 0 reaches via cross-validator measurement, eliminating the inconsistency."
