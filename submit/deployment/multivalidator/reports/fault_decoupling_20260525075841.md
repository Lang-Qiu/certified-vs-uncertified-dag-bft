# Double-fault decoupling analysis (additivity vs synergy)

- Generated (UTC): 2026-05-25T07:58:41+00:00
- Metric source: `consensus_metrics_true.json` (log-derived, true per-checkpoint intervals)
- n=10 per scenario (where available)

## Coverage

- **baseline**: n=10
- **delay_only_v1_match**: n=10
- **loss_only_v2_match**: n=10
- **two_validator_pressure**: n=10

## Per-scenario aggregate (median [p25, p75])

| metric | baseline | delay_only_v1 | loss_only_v2 | two_validator_pressure |
| --- | --- | --- | --- | --- |
| checkpoint_interval_ms_p50_true | 215.0 [214.7, 215.4] | 215.0 [214.9, 215.3] | 214.6 [214.5, 215.6] | 216.4 [216.2, 216.9] |
| checkpoint_interval_ms_p95_true | 263.2 [220.5, 265.0] | 257.4 [254.7, 261.7] | 264.3 [223.3, 265.8] | 267.5 [266.3, 279.9] |
| checkpoint_interval_ms_max_true | 1945.2 [1930.6, 2034.0] | 2224.4 [2185.2, 2462.1] | 1962.8 [1910.8, 2050.6] | 2325.7 [2275.1, 2679.6] |
| checkpoint_count_true | 637.0 [632.0, 654.0] | 669.0 [648.0, 675.0] | 667.0 [654.0, 680.0] | 739.0 [712.0, 833.0] |
| n_intervals_gt_2000ms | 0.0 [0.0, 1.0] | 2.0 [2.0, 2.0] | 0.0 [0.0, 1.0] | 2.0 [2.0, 4.0] |
| n_intervals_500_to_2000ms | 4.0 [3.0, 4.0] | 3.0 [2.0, 4.0] | 4.0 [3.0, 4.0] | 6.0 [5.0, 7.0] |

## Additivity test

**Definition**: For each metric X,
- expected_additive(X) = X(delay_only_v1) + X(loss_only_v2) - X(baseline)
- observed(X) = X(two_validator_pressure)
- ratio = observed / expected_additive
- Δ_excess = observed - expected_additive (the part NOT explained by additivity)

**Interpretation**:
- ratio ≈ 1 (Δ_excess ≈ 0): additive — combining faults gives no extra cost beyond their sum
- ratio > 1 (Δ_excess > 0): synergistic / multiplicative — combined effect exceeds sum
- ratio < 1: anti-synergistic — combined effect less than sum

Using **medians** (n=10 per cell, small-sample non-parametric):

| metric | baseline med | delay_only med | loss_only med | observed med | expected_additive | ratio | Δ_excess |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| checkpoint_interval_ms_p50_true | 215.0 | 215.0 | 214.6 | 216.4 | 214.6 | 1.01 | +1.8 |
| checkpoint_interval_ms_p95_true | 263.2 | 257.4 | 264.3 | 267.5 | 258.5 | 1.03 | +9.0 |
| checkpoint_interval_ms_max_true | 1945.2 | 2224.4 | 1962.8 | 2325.7 | 2242.0 | 1.04 | +83.7 |
| checkpoint_count_true | 637.0 | 669.0 | 667.0 | 739.0 | 699.0 | 1.06 | +40.0 |
| n_intervals_gt_2000ms | 0.0 | 2.0 | 0.0 | 2.0 | 2.0 | 1.00 | +0.0 |
| n_intervals_500_to_2000ms | 4.0 | 3.0 | 4.0 | 6.0 | 3.0 | 2.00 | +3.0 |

## Per-rep raw

| scenario | rep | p50_true | p95_true | max | n_>2000 | n_500_2000 | ckpt_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 1 | 213.7 | 223.6 | 2008.6 | 1 | 3 | 639 |
| baseline | 2 | 215.1 | 263.2 | 2034.0 | 1 | 3 | 667 |
| baseline | 3 | 215.0 | 219.6 | 1933.4 | 0 | 4 | 627 |
| baseline | 4 | 214.7 | 265.0 | 1960.9 | 0 | 4 | 646 |
| baseline | 5 | 215.8 | 263.8 | 2168.2 | 1 | 3 | 654 |
| baseline | 6 | 213.9 | 267.1 | 1886.0 | 0 | 4 | 633 |
| baseline | 7 | 215.3 | 264.7 | 1930.6 | 0 | 4 | 637 |
| baseline | 8 | 215.0 | 219.5 | 2035.2 | 1 | 3 | 687 |
| baseline | 9 | 215.6 | 265.7 | 1945.2 | 0 | 4 | 632 |
| baseline | 10 | 215.4 | 220.5 | 1858.2 | 0 | 4 | 624 |
| delay_only_v1_match | 1 | 215.1 | 265.4 | 2386.8 | 2 | 4 | 632 |
| delay_only_v1_match | 2 | 214.4 | 259.7 | 2162.9 | 2 | 3 | 648 |
| delay_only_v1_match | 3 | 215.1 | 254.0 | 2496.7 | 2 | 3 | 670 |
| delay_only_v1_match | 4 | 215.3 | 261.7 | 2603.9 | 2 | 2 | 689 |
| delay_only_v1_match | 5 | 214.5 | 257.6 | 2431.1 | 2 | 2 | 675 |
| delay_only_v1_match | 6 | 215.3 | 257.4 | 2462.1 | 2 | 3 | 653 |
| delay_only_v1_match | 7 | 214.9 | 255.8 | 2185.2 | 2 | 4 | 669 |
| delay_only_v1_match | 8 | 215.0 | 254.7 | 2224.4 | 2 | 4 | 671 |
| delay_only_v1_match | 9 | 214.9 | 254.6 | 2216.0 | 2 | 4 | 691 |
| delay_only_v1_match | 10 | 215.4 | 262.9 | 2128.2 | 2 | 2 | 639 |
| loss_only_v2_match | 1 | 214.6 | 265.8 | 1899.4 | 0 | 4 | 654 |
| loss_only_v2_match | 2 | 215.3 | 266.2 | 1910.8 | 0 | 4 | 651 |
| loss_only_v2_match | 3 | 215.3 | 220.5 | 2050.6 | 1 | 3 | 660 |
| loss_only_v2_match | 4 | 214.3 | 267.1 | 1903.5 | 0 | 4 | 640 |
| loss_only_v2_match | 5 | 215.7 | 230.0 | 2107.0 | 1 | 3 | 667 |
| loss_only_v2_match | 6 | 214.5 | 264.5 | 1962.8 | 0 | 4 | 674 |
| loss_only_v2_match | 7 | 214.5 | 264.3 | 2006.0 | 1 | 3 | 680 |
| loss_only_v2_match | 8 | 216.4 | 264.3 | 1959.9 | 0 | 4 | 739 |
| loss_only_v2_match | 9 | 215.6 | 223.3 | 2281.5 | 1 | 3 | 687 |
| loss_only_v2_match | 10 | 213.9 | 220.5 | 1975.7 | 0 | 4 | 674 |
| two_validator_pressure | 1 | 215.7 | 270.5 | 2174.3 | 2 | 6 | 712 |
| two_validator_pressure | 2 | 216.4 | 279.9 | 2603.0 | 2 | 6 | 708 |
| two_validator_pressure | 3 | 216.2 | 267.5 | 2259.5 | 2 | 7 | 682 |
| two_validator_pressure | 4 | 216.0 | 265.4 | 2292.4 | 3 | 7 | 739 |
| two_validator_pressure | 5 | 216.5 | 266.3 | 2275.1 | 2 | 3 | 725 |
| two_validator_pressure | 6 | 216.8 | 265.6 | 2331.1 | 2 | 5 | 777 |
| two_validator_pressure | 7 | 216.4 | 266.6 | 2325.7 | 2 | 5 | 787 |
| two_validator_pressure | 8 | 218.3 | 293.2 | 2946.4 | 4 | 9 | 888 |
| two_validator_pressure | 9 | 216.9 | 277.9 | 3018.6 | 4 | 3 | 833 |
| two_validator_pressure | 10 | 217.9 | 285.5 | 2679.6 | 4 | 8 | 872 |
