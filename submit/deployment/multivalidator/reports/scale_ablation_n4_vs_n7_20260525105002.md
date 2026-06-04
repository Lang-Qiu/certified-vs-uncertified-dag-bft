# Scale ablation: n=4 vs n=7 with identical physical fault parameters

- Generated (UTC): 2026-05-25T10:50:02+00:00
- Metric source: `consensus_metrics_true.json` (log-derived)
- Fault parameters held constant across scales: delay=150±30 ms, loss=2%
- BFT bounds: n=7 → f=2; n=4 → f=1 (two_validator_pressure meets f at n=4 and is below it at n=7)

## Coverage

- **baseline (n=7)**: reps=10
- **delay_only_v1 (n=7)**: reps=10
- **loss_only_v2 (n=7)**: reps=10
- **two_validator_pressure (n=7)**: reps=10
- **baseline (n=4)**: reps=10
- **delay_only_v1 (n=4)**: reps=10
- **loss_only_v2 (n=4)**: reps=10
- **two_validator_pressure (n=4)**: reps=10

## Per-scenario, n=7 vs n=4 (median [p25, p75], CV%)

| scenario | metric | n=7 | n=4 | n=4 / n=7 (median ratio) |
| --- | --- | --- | --- | ---: |
| baseline | checkpoint_interval_ms_p50_true | 215.0 [214.7, 215.4] (CV 0.32%) | 210.3 [209.5, 210.4] (CV 0.22%) | 0.98 |
| baseline | checkpoint_interval_ms_p95_true | 263.2 [220.5, 265.0] (CV 9.24%) | 212.3 [211.8, 212.5] (CV 0.20%) | 0.81 |
| baseline | checkpoint_interval_ms_max_true | 1945.2 [1930.6, 2034.0] (CV 4.52%) | 1566.1 [1555.7, 1728.4] (CV 5.44%) | 0.81 |
| baseline | checkpoint_count_true | 637.0 [632.0, 654.0] (CV 3.06%) | 125.0 [123.0, 127.0] (CV 2.43%) | 0.20 |
| baseline | n_intervals_gt_2000ms | 0.0 [0.0, 1.0] (CV 129.10%) | 0.0 [0.0, 0.0] (CV 0.00%) | nan |
| baseline | n_intervals_500_to_2000ms | 4.0 [3.0, 4.0] (CV 14.34%) | 2.0 [2.0, 2.0] (CV 0.00%) | 0.50 |
|  |  |  |  |  |
| delay_only_v1 | checkpoint_interval_ms_p50_true | 215.0 [214.9, 215.3] (CV 0.16%) | 210.7 [210.5, 211.5] (CV 0.31%) | 0.98 |
| delay_only_v1 | checkpoint_interval_ms_p95_true | 257.4 [254.7, 261.7] (CV 1.52%) | 318.4 [302.6, 342.0] (CV 16.29%) | 1.24 |
| delay_only_v1 | checkpoint_interval_ms_max_true | 2224.4 [2185.2, 2462.1] (CV 7.12%) | 1572.0 [1557.0, 1715.7] (CV 54.11%) | 0.71 |
| delay_only_v1 | checkpoint_count_true | 669.0 [648.0, 675.0] (CV 3.02%) | 124.0 [124.0, 125.0] (CV 4.75%) | 0.19 |
| delay_only_v1 | n_intervals_gt_2000ms | 2.0 [2.0, 2.0] (CV 0.00%) | 0.0 [0.0, 0.0] (CV 316.23%) | 0.00 |
| delay_only_v1 | n_intervals_500_to_2000ms | 3.0 [2.0, 4.0] (CV 28.25%) | 2.0 [2.0, 2.0] (CV 47.35%) | 0.67 |
|  |  |  |  |  |
| loss_only_v2 | checkpoint_interval_ms_p50_true | 214.6 [214.5, 215.6] (CV 0.36%) | 210.6 [210.5, 211.0] (CV 0.15%) | 0.98 |
| loss_only_v2 | checkpoint_interval_ms_p95_true | 264.3 [223.3, 265.8] (CV 8.76%) | 214.0 [212.4, 214.9] (CV 3.68%) | 0.81 |
| loss_only_v2 | checkpoint_interval_ms_max_true | 1962.8 [1910.8, 2050.6] (CV 5.85%) | 1609.9 [1572.2, 1777.3] (CV 12.52%) | 0.82 |
| loss_only_v2 | checkpoint_count_true | 667.0 [654.0, 680.0] (CV 4.07%) | 128.0 [125.0, 129.0] (CV 2.11%) | 0.19 |
| loss_only_v2 | n_intervals_gt_2000ms | 0.0 [0.0, 1.0] (CV 129.10%) | 0.0 [0.0, 0.0] (CV 0.00%) | nan |
| loss_only_v2 | n_intervals_500_to_2000ms | 4.0 [3.0, 4.0] (CV 14.34%) | 2.0 [2.0, 2.0] (CV 23.57%) | 0.50 |
|  |  |  |  |  |
| two_validator_pressure | checkpoint_interval_ms_p50_true | 216.4 [216.2, 216.9] (CV 0.38%) | 210.8 [210.6, 211.0] (CV 0.14%) | 0.97 |
| two_validator_pressure | checkpoint_interval_ms_p95_true | 267.5 [266.3, 279.9] (CV 3.57%) | 372.7 [350.3, 437.8] (CV 12.20%) | 1.39 |
| two_validator_pressure | checkpoint_interval_ms_max_true | 2325.7 [2275.1, 2679.6] (CV 12.17%) | 1564.2 [1559.2, 1577.2] (CV 18.07%) | 0.67 |
| two_validator_pressure | checkpoint_count_true | 739.0 [712.0, 833.0] (CV 9.31%) | 124.0 [121.0, 124.0] (CV 1.96%) | 0.17 |
| two_validator_pressure | n_intervals_gt_2000ms | 2.0 [2.0, 4.0] (CV 35.14%) | 0.0 [0.0, 0.0] (CV 0.00%) | 0.00 |
| two_validator_pressure | n_intervals_500_to_2000ms | 6.0 [5.0, 7.0] (CV 33.38%) | 2.0 [2.0, 4.0] (CV 41.34%) | 0.33 |
|  |  |  |  |  |

## Additivity test, replicated at each scale

**Definition**: expected_additive = X(delay_only_v1) + X(loss_only_v2) − X(baseline)
                observed = X(two_validator_pressure)
                ratio = observed / expected; Δ = observed − expected

### n=7

| metric | baseline | delay_only_v1 | loss_only_v2 | observed | expected | ratio | Δ_excess |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| checkpoint_interval_ms_p50_true | 215.0 | 215.0 | 214.6 | 216.4 | 214.6 | 1.01 | +1.8 |
| checkpoint_interval_ms_p95_true | 263.2 | 257.4 | 264.3 | 267.5 | 258.5 | 1.03 | +9.0 |
| checkpoint_interval_ms_max_true | 1945.2 | 2224.4 | 1962.8 | 2325.7 | 2242.0 | 1.04 | +83.7 |
| checkpoint_count_true | 637.0 | 669.0 | 667.0 | 739.0 | 699.0 | 1.06 | +40.0 |
| n_intervals_gt_2000ms | 0.0 | 2.0 | 0.0 | 2.0 | 2.0 | 1.00 | +0.0 |
| n_intervals_500_to_2000ms | 4.0 | 3.0 | 4.0 | 6.0 | 3.0 | 2.00 | +3.0 |

### n=4

| metric | baseline | delay_only_v1 | loss_only_v2 | observed | expected | ratio | Δ_excess |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| checkpoint_interval_ms_p50_true | 210.3 | 210.7 | 210.6 | 210.8 | 211.1 | 1.00 | -0.3 |
| checkpoint_interval_ms_p95_true | 212.3 | 318.4 | 214.0 | 372.7 | 320.2 | 1.16 | +52.5 |
| checkpoint_interval_ms_max_true | 1566.1 | 1572.0 | 1609.9 | 1564.2 | 1615.8 | 0.97 | -51.6 |
| checkpoint_count_true | 125.0 | 124.0 | 128.0 | 124.0 | 127.0 | 0.98 | -3.0 |
| n_intervals_gt_2000ms | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | nan | +0.0 |
| n_intervals_500_to_2000ms | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 1.00 | +0.0 |

## Per-rep raw (n=4 only)

| scenario | rep | p50_true | p95_true | max | n_>2000 | n_500_2000 | ckpt_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_n4 | 1 | 209.5 | 211.7 | 1568.8 | 0 | 2 | 120 |
| baseline_n4 | 2 | 210.5 | 212.3 | 1548.7 | 0 | 2 | 125 |
| baseline_n4 | 3 | 210.3 | 212.3 | 1567.4 | 0 | 2 | 123 |
| baseline_n4 | 4 | 209.4 | 211.3 | 1555.7 | 0 | 2 | 125 |
| baseline_n4 | 5 | 210.3 | 211.8 | 1757.9 | 0 | 2 | 122 |
| baseline_n4 | 6 | 210.3 | 212.3 | 1728.4 | 0 | 2 | 127 |
| baseline_n4 | 7 | 209.3 | 212.2 | 1563.7 | 0 | 2 | 129 |
| baseline_n4 | 8 | 210.4 | 212.7 | 1735.3 | 0 | 2 | 130 |
| baseline_n4 | 9 | 210.4 | 212.5 | 1566.1 | 0 | 2 | 125 |
| baseline_n4 | 10 | 210.4 | 212.5 | 1549.9 | 0 | 2 | 126 |
| delay_only_v1_n4 | 1 | 210.5 | 342.0 | 1182.4 | 0 | 2 | 127 |
| delay_only_v1_n4 | 2 | 210.6 | 336.0 | 1572.6 | 0 | 2 | 122 |
| delay_only_v1_n4 | 3 | 210.2 | 318.4 | 1708.9 | 0 | 2 | 124 |
| delay_only_v1_n4 | 4 | 210.5 | 456.3 | 1557.0 | 0 | 4 | 124 |
| delay_only_v1_n4 | 5 | 210.7 | 304.1 | 1569.2 | 0 | 2 | 125 |
| delay_only_v1_n4 | 6 | 211.0 | 302.6 | 1715.7 | 0 | 2 | 125 |
| delay_only_v1_n4 | 7 | 210.9 | 293.4 | 1572.0 | 0 | 2 | 124 |
| delay_only_v1_n4 | 8 | 211.6 | 339.9 | 1546.6 | 0 | 2 | 125 |
| delay_only_v1_n4 | 9 | 211.5 | 250.3 | 4792.8 | 1 | 0 | 143 |
| delay_only_v1_n4 | 10 | 212.3 | 349.9 | 1799.7 | 0 | 3 | 124 |
| loss_only_v2_n4 | 1 | 211.4 | 214.9 | 1808.9 | 0 | 2 | 129 |
| loss_only_v2_n4 | 2 | 211.1 | 215.6 | 1609.9 | 0 | 2 | 129 |
| loss_only_v2_n4 | 3 | 211.0 | 214.0 | 1859.9 | 0 | 2 | 126 |
| loss_only_v2_n4 | 4 | 210.9 | 238.6 | 1777.3 | 0 | 2 | 125 |
| loss_only_v2_n4 | 5 | 210.8 | 214.1 | 1618.1 | 0 | 2 | 122 |
| loss_only_v2_n4 | 6 | 210.6 | 212.4 | 1595.1 | 0 | 2 | 130 |
| loss_only_v2_n4 | 7 | 210.5 | 213.4 | 1572.2 | 0 | 2 | 128 |
| loss_only_v2_n4 | 8 | 210.4 | 214.5 | 1126.3 | 0 | 3 | 129 |
| loss_only_v2_n4 | 9 | 210.6 | 212.4 | 1614.1 | 0 | 1 | 129 |
| loss_only_v2_n4 | 10 | 210.5 | 212.0 | 1563.2 | 0 | 2 | 124 |
| two_validator_pressure_n4 | 1 | 210.6 | 443.1 | 786.1 | 0 | 4 | 124 |
| two_validator_pressure_n4 | 2 | 210.6 | 429.8 | 1564.2 | 0 | 2 | 120 |
| two_validator_pressure_n4 | 3 | 211.2 | 324.7 | 1579.8 | 0 | 2 | 121 |
| two_validator_pressure_n4 | 4 | 211.0 | 372.4 | 1585.3 | 0 | 2 | 126 |
| two_validator_pressure_n4 | 5 | 210.8 | 451.9 | 1566.5 | 0 | 4 | 118 |
| two_validator_pressure_n4 | 6 | 210.8 | 334.3 | 1577.2 | 0 | 1 | 124 |
| two_validator_pressure_n4 | 7 | 210.5 | 437.8 | 1571.1 | 0 | 4 | 124 |
| two_validator_pressure_n4 | 8 | 210.6 | 350.3 | 1195.9 | 0 | 2 | 122 |
| two_validator_pressure_n4 | 9 | 211.0 | 418.5 | 1561.9 | 0 | 3 | 124 |
| two_validator_pressure_n4 | 10 | 211.3 | 372.7 | 1559.2 | 0 | 2 | 124 |
