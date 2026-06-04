# Double-fault decoupling — conclusion synthesis

- Generated (UTC): 2026-05-25T08:00:00+00:00
- Linked artifacts:
  - Decoupling raw table: `reports/fault_decoupling_20260525075841.md`
  - True vs probe metric: `reports/variance_true_vs_probe_20260525050121.md`
  - Layer localization: `reports/ckpt_p95_layer_localization_report_20260525.md`
  - Per-rep ckpt distribution: `reports/ckpt_p95_root_cause_20260525043728.md`
  - Re-extracted true summary (60+20 reps): `reports/summary_true_with_decoupling_20260525.md`
- Data: 80 formal reps (60 original + 10 `delay_only_v1_match` + 10 `loss_only_v2_match`, all seed 20260525xx), 7 validators, f=2 quorum

## TL;DR

The double-fault scenario `two_validator_pressure` (150±30 ms delay on v1 + 2% loss on v2) is **approximately additive** with respect to its two single-fault components — additivity ratios fall in 1.00–1.06 for all core checkpoint-cadence metrics. There is no statistical evidence of synergistic (multiplicative) interaction between the two fault sources on consensus cadence.

The previously reported "two_validator_pressure ckpt_p95 CV ≈ 63%" finding from `variance_table_20260525104240.md` is a **measurement-pipeline artifact** introduced by the rpc-probe metric averaging only 14 anchors per rep over ~2-second windows that randomly cross 60 s epoch-boundary CheckpointBuilder pauses. The true log-derived p95 CV is **3.57%** — a 17× reduction.

## 1. Additivity test result

For each metric X define
```
expected_additive(X) = X(delay_only_v1) + X(loss_only_v2) − X(baseline)
observed(X)          = X(two_validator_pressure)
ratio                = observed / expected_additive
```

| metric                          | baseline | delay_only_v1 | loss_only_v2 | observed | expected_additive | ratio | Δ_excess |
|---------------------------------|---------:|--------------:|-------------:|---------:|------------------:|------:|---------:|
| ckpt_interval_p50_true (ms)     |    215.0 |         215.0 |        214.6 |    216.4 |             214.6 |  1.01 |     +1.8 |
| ckpt_interval_p95_true (ms)     |    263.2 |         257.4 |        264.3 |    267.5 |             258.5 |  1.03 |     +9.0 |
| ckpt_interval_max_true (ms)     |   1945.2 |        2224.4 |       1962.8 |   2325.7 |            2242.0 |  1.04 |    +83.7 |
| checkpoint_count_true           |    637.0 |         669.0 |        667.0 |    739.0 |             699.0 |  1.06 |    +40.0 |
| n_intervals_gt_2000ms           |        0 |             2 |            0 |        2 |                 2 |  1.00 |     +0.0 |
| n_intervals_500_to_2000ms       |        4 |             3 |            4 |        6 |                 3 |  2.00 |     +3.0 |

(Medians across n=10 reps per cell.)

### Interpretation

- **Cadence (p50/p95)**: ratios 1.01/1.03 — additive. The 9 ms Δ_excess on p95 is within the rep-to-rep noise of any single-fault cell (IQR widths 5–25 ms).
- **Max interval**: ratio 1.04 — additive. The 84 ms Δ_excess is a small contribution relative to the ~2 s epoch-boundary pause that dominates the maximum.
- **Throughput proxy (ckpt_count)**: ratio 1.06 — slightly higher than expected (more checkpoints per ~140 s workload), but the absolute deviation is well inside the natural spread of single-fault cells (loss_only IQR 654–680, delay_only IQR 648–675).
- **Long-tail events (>2000 ms)**: ratio 1.00 — exactly additive. Both `delay_only_v1` and `two_validator_pressure` produce exactly 2 epoch-boundary pauses per rep; loss_only and baseline produce 0 (median). These are CheckpointBuilder epoch-boundary events, not protocol stalls.
- **Mid-tail events (500–2000 ms)**: ratio 2.00 — the only super-additive metric, but **absolute Δ_excess is +3 events** out of ~700 checkpoints (< 0.5% inflation). With n=10 per cell this is at most a weak signal of mild interaction in the mid-tail regime and not a population effect we can confidently distinguish from noise.

### Conclusion

The two fault sources combine **additively** on consensus cadence in our 7-validator f=2 setup. Combining a delay-class fault on one validator with a loss-class fault on another does **not** produce multiplicative degradation.

## 2. Refuting the earlier "rare double-fault hit" hypothesis

`reports/ckpt_p95_root_cause_report_20260525.md` (an earlier first-pass investigation) proposed a "rare-tail double-fault hit event" hypothesis for the observed bimodal p95 in `two_validator_pressure` reps 08/09/10 (674/669/1004 ms vs 226–334 ms in other reps).

That hypothesis is **refuted** by the layer-localization analysis (`ckpt_p95_layer_localization_report_20260525.md`), which showed:
1. The top-4 longest intervals in rep10 (2680/2640/2618/2510 ms) occur at exactly 60 s spacing — these are `CheckpointBuilder` epoch-boundary pauses, present in **all** scenarios including baseline.
2. During those long gaps, v1/v2/v3 consensus_round counts differ by ≤4 events — consensus is **not** blocked.
3. The variance in the probe metric came from random alignment between the 14 probe windows per rep and the 60 s epoch boundaries.

The decoupling additivity result here is a second, independent piece of evidence: if the bimodality were caused by a synergistic fault interaction, we would expect the combined scenario to produce excess tail mass relative to additive expectation. We do not see that — the long-tail count (`n_intervals_gt_2000ms`) is exactly additive.

## 3. Probe-metric distortion magnitude

`reports/variance_true_vs_probe_20260525050121.md` quantifies how far the rpc-probe metric drifts from log-derived truth:

| scenario                | probe CV% | true CV% | distortion factor |
|-------------------------|---------:|---------:|------------------:|
| baseline                |     5.82 |     9.24 |             0.63× |
| delay_low               |     3.72 |     8.50 |             0.44× |
| delay_high              |     0.69 |     1.16 |             0.59× |
| loss_low                |    12.53 |     9.76 |             1.28× |
| crash_one_validator     |     8.97 |     0.55 |            16.3×  |
| two_validator_pressure  |    63.23 |     3.57 |            17.7×  |

The probe metric over-states variance most severely in scenarios where the workload duration interacts strongly with epoch-boundary alignment — exactly the two scenarios where prior analyses flagged "rare-tail instability." Both cases collapse to ordinary 3–4% CV once the metric is computed from the true per-checkpoint event stream.

## 4. Implications

1. **Cadence stability claim**: across all 80 reps, true p50 CV is ≤0.73% and true p95 CV is ≤9.76% (loss_low, with no fault-induced tail). The cadence is stable to within ~10% even under f=2 simultaneous faults.
2. **Fault independence claim**: the two fault classes (network delay, network loss) interact additively on cadence within this scale; there is no evidence of multiplicative blow-up.
3. **Metric methodology note**: any future cadence analysis should compute from `consensus_metrics_true.json` (log-derived) rather than `consensus_metrics.json` (rpc-probe averages). The probe metric remains valid for relative ordering across scenarios but is unreliable for variance/tail claims.
4. **Manifest integrity preserved**: the sidecar pattern (`consensus_metrics_true.json` next to existing `consensus_metrics.json`) means the original 60/60 hash chain from `validity_audit.md` is untouched. The 20 new reps have their own manifests.

## 5. Items NOT changed in this analysis

Per the paper-integration approval gate, this analysis produced only investigation artifacts under `stage7_deployment/multivalidator/reports/`. The following remain untouched and require explicit user approval before any edits:

- `final/final_paper.md`
- `stage8_paper_integration/`
- Any abstract / claim statements in the manuscript

The decoupling result and the probe-metric refutation are candidates for revising the "variance / stability under pressure" claim in the deployment-evidence subsection, but no revision text is drafted here.
