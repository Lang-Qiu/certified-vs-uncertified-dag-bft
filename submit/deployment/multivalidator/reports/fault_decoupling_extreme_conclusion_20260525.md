# Additivity stress test — conclusion synthesis (Tests 0/1/2)

- Generated (UTC): 2026-05-25T10:30:00+00:00
- Linked artifacts:
  - Numerical tables: `reports/fault_decoupling_extreme_20260525101524.md`
  - Combined true-cadence summary (120 reps): `reports/summary_true_with_extreme_20260525.md`
  - Original canonical decoupling: `reports/fault_decoupling_conclusion_20260525.md`
- Data: 120 formal reps total (60 original + 20 decoupling + 40 extreme); seed family 2026052402 / 2026052406 / 2026052501 / 20260525
- Scope: stress-test whether the additive picture from the canonical case (Test 0) survives at (i) same-validator stacking and (ii) higher loss rate

## TL;DR

| Test | scenario design | n=10 ×4 cells | additivity verdict |
|---|---|---|---|
| Test 0 | delay v1 + loss v2 @ 2% (canonical) | all valid | **additive** (ratios 1.00–1.06) ✓ |
| Test 1 | delay v1 + loss v1 (same node) @ 2% | **methodologically invalid** | inconclusive — `tc qdisc replace` overwrites the first fault |
| Test 2 | delay v1 + loss v2 @ **5%** | valid | **super-additive on p95** (ratio 1.35); +75 ms tail excess vs expected |

Test 0 re-confirms (a). Test 2 is a **genuine new finding**: combining delay with 5%-loss across validators produces non-additive tail inflation — the protocol cadence breaks out of the "lock-in" that 5% loss alone induces. Test 1 must be re-run after fixing the qdisc orchestration.

## 1. Test 0 — canonical (already established)

Confirms (a)'s result with the same 4 cells. Ratios on all metrics fall in 1.00–1.06; long-tail count exactly additive. See `fault_decoupling_conclusion_20260525.md` for the full discussion. Reproduced here for context:

| metric | expected_additive | observed | ratio |
|---|---:|---:|---:|
| p95_true | 258.5 | 267.5 | **1.03** |
| max_true | 2242.0 | 2325.7 | 1.04 |
| n>2000 ms | 2.0 | 2.0 | 1.00 |

## 2. Test 1 — same-validator stacking is methodologically invalid

### The infrastructure bug

Inspection of `scripts/run_experiment_matrix.ps1:294-302`:

```powershell
# applied for each fault sequentially:
docker exec $target tc qdisc replace dev eth0 root netem delay 150ms 30ms
docker exec $target tc qdisc replace dev eth0 root netem loss 2%
```

`tc qdisc replace ... root ...` replaces the **entire root qdisc**. The second call therefore wipes out the first. When both faults target the same container (`validator-1` in this scenario), the second-applied fault (loss) is the only one in effect — the delay disappears.

### Empirical confirmation

Comparing `delay_loss_same_v1` to its single-fault counterparts:

| cell | p95_true median | p95_true [p25, p75] |
|---|---:|---:|
| baseline | 263.2 | [220.5, 265.0] |
| delay_only_v1 | 257.4 | [254.7, 261.7] |
| **loss_only_v1** | 265.6 | [259.8, 266.1] |
| **delay_loss_same_v1** | 241.8 | [220.7, 264.1] |

The "stacked" cell's distribution lies between the loss-only and baseline ranges — consistent with it being **loss-only behavior plus the usual bimodal cadence variance**, not a genuine stacking of both faults. The 24-ms difference between `loss_only_v1` and `delay_loss_same_v1` medians is within the bimodal-driven jitter (each cell has reps clustered around 220 and 265 with the median sensitive to the boundary).

### Conclusion for Test 1

**The result table for Test 1 in `fault_decoupling_extreme_20260525101524.md` should not be cited as evidence of sub-additivity.** The orchestration cannot stack two `tc netem` actions on the same root qdisc as currently implemented.

### Fix path (recommended before re-running)

Replace the per-action stub with a per-target accumulator that issues one combined netem command:

```sh
# instead of two `tc qdisc replace` calls, issue one:
tc qdisc replace dev eth0 root netem delay 150ms 30ms loss 2%
```

This is a single-file change to `Invoke-StartFaults` in `run_experiment_matrix.ps1` (or the `inject_fault.sh` companion) that:
1. Groups all faults by `target`.
2. For each target, composes one `netem` clause string concatenating delay/loss/jitter parameters.
3. Issues one `tc qdisc replace` per target.

After the fix, Test 1 should be re-executed (10 reps, ~30 min compute).

## 3. Test 2 — higher loss extreme is super-additive on p95

### Numbers

| metric | baseline | delay_only_v1 | loss_high_v2 (5%) | observed (pressure_high_loss) | expected_additive | ratio | Δ_excess |
|---|---:|---:|---:|---:|---:|---:|---:|
| p50_true (ms) | 215.0 | 215.0 | 214.4 | 215.1 | 214.4 | 1.00 | +0.7 |
| **p95_true (ms)** | 263.2 | 257.4 | 221.6 | **290.9** | 215.8 | **1.35** | **+75.1** |
| max_true (ms) | 1945.2 | 2224.4 | 1972.1 | 2297.5 | 2251.3 | 1.02 | +46.2 |
| ckpt_count | 637 | 669 | 666 | 660 | 698 | 0.95 | −38 |
| n>2000 ms | 0 | 2 | 0 | 2 | 2 | 1.00 | 0 |
| **n_500–2000 ms** | 4 | 3 | 4 | **9** | 3 | **3.00** | **+6** |

### Three concrete observations

1. **p50 cadence remains stable** (215.1 ms, ratio 1.00). The protocol still produces checkpoints at the same nominal rate.
2. **p95 tail inflates non-additively**: observed 290.9 ms vs expected_additive 215.8 ms. The +75 ms is well outside any single-cell IQR (delay_only_v1 IQR 254.7–261.7; loss_high_v2 IQR 220.5–265.4).
3. **Mid-tail (500–2000 ms) events triple** vs expected (9 vs 3), suggesting more frequent multi-second hiccups than either fault alone would produce.

### Mechanism hypothesis

`loss_high_v2` alone has p95 = 221.6 ms — **lower** than baseline (263.2 ms). This counterintuitive tightening suggests that 5% loss on v2 pushes the protocol into a more deterministic "v2-out-of-fast-quorum" cadence: the protocol consistently waits for the same 5-of-7 set, eliminating the variance that comes from sometimes including v2.

When we add a 150-ms delay on v1, the lock-in is disturbed — sometimes the protocol must wait for v2 (if v1 is delayed enough), sometimes not. This **mode-switching cost** is what shows up as p95 inflation. It is not a single physical resource being saturated; it is a higher-order protocol effect.

### Outlier flag

`pressure_high_loss` rep06 has a max interval of **13 035 ms** (vs ~2 200 ms typical for the cell), with 22 mid-tail events and 892 checkpoints (vs ~660 typical). This rep significantly inflates the cell's `n_500_2000` mean (mean 10.1 vs median 9). The p95 and max medians are robust to this outlier; the qualitative super-additivity claim does not depend on rep06. Recommend keeping it in the published analysis with an explicit note.

### Caveat on negative expected_additive logic

When `single_B` alone produces a tighter cadence than baseline (loss_high_v2 p95 < baseline p95), the additive prediction can dip below baseline (expected_additive = 215.8 ms < baseline 263.2 ms). This is mathematically valid as a "no-interaction null" but suggests the additive model is too simplistic at extreme parameter values. A future analysis could replace the additivity-test framing with an interaction-effect ANOVA-style decomposition.

## 4. Updated picture (combined with (a))

| regime | configuration | additivity status | confidence |
|---|---|---|---|
| canonical n=7, 2% loss, diff validators | delay v1 + loss v2 | additive (1.03–1.06) | high (n=10 ×4 cells, two seed families) |
| same-validator stacking, 2% | delay v1 + loss v1 | **inconclusive** | infrastructure bug |
| extreme cross-validator, 5% loss | delay v1 + loss v2 (5%) | **super-additive on p95** (+75 ms, ratio 1.35) | medium (n=10 ×4 cells, one rep outlier) |

The additive picture from (a) holds at moderate parameters but **breaks down at higher fault intensity**. This is a more nuanced and more publishable story than (a) alone.

## 5. Recommended next steps (not auto-executed)

1. **Fix qdisc orchestration**: ~1 hour engineering work; one-target-one-netem grouping. Then re-run Test 1 (10 reps × ~3 min each = ~30 min).
2. **Replicate Test 2 with a second seed**: 10 reps with a different seed family to confirm the super-additivity is not a single-seed artifact. ~30 min.
3. **Investigate rep06 of `pressure_high_loss`**: pull the fullnode log around its max-interval event to see whether it is an epoch-boundary pileup or a different anomaly. Optional.

## 6. Items NOT changed in this analysis

Per `[[paper-integration-approval-gate]]`, no edits made to `final/final_paper.md` or `stage8_paper_integration/`. The findings above are candidates for revising the "stability under multi-fault pressure" claim; revision text will only be drafted after explicit user approval.
