# Additivity stress test (Tests 0/1/2)

- Generated (UTC): 2026-05-25T10:15:24+00:00
- Metric source: `consensus_metrics_true.json` (log-derived)
- n=10 per cell

## Coverage

- **baseline**: n=10
- **delay_only_v1**: n=10
- **loss_only_v2**: n=10
- **two_validator_pressure**: n=10
- **loss_only_v1**: n=10
- **delay_loss_same_v1**: n=10
- **loss_high_v2**: n=10
- **pressure_high_loss**: n=10

## Per-cell aggregate (median [p25, p75])

| metric | baseline | delay_only_v1 | loss_only_v2 | two_validator_pressure | loss_only_v1 | delay_loss_same_v1 | loss_high_v2 | pressure_high_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint_interval_ms_p50_true | 215.0 [214.7, 215.4] | 215.0 [214.9, 215.3] | 214.6 [214.5, 215.6] | 216.4 [216.2, 216.9] | 214.1 [213.4, 215.1] | 214.7 [214.5, 215.0] | 214.4 [213.9, 215.0] | 215.1 [214.8, 215.2] |
| checkpoint_interval_ms_p95_true | 263.2 [220.5, 265.0] | 257.4 [254.7, 261.7] | 264.3 [223.3, 265.8] | 267.5 [266.3, 279.9] | 265.6 [259.8, 266.1] | 241.8 [220.7, 264.1] | 221.6 [220.5, 265.4] | 290.9 [289.4, 300.5] |
| checkpoint_interval_ms_max_true | 1945.2 [1930.6, 2034.0] | 2224.4 [2185.2, 2462.1] | 1962.8 [1910.8, 2050.6] | 2325.7 [2275.1, 2679.6] | 1991.2 [1927.7, 2026.1] | 1956.0 [1863.6, 2004.5] | 1972.1 [1880.8, 2019.0] | 2297.5 [2148.2, 2518.1] |
| checkpoint_count_true | 637.0 [632.0, 654.0] | 669.0 [648.0, 675.0] | 667.0 [654.0, 680.0] | 739.0 [712.0, 833.0] | 664.0 [654.0, 673.0] | 654.0 [652.0, 669.0] | 666.0 [652.0, 688.0] | 660.0 [645.0, 682.0] |
| n_intervals_gt_2000ms | 0.0 [0.0, 1.0] | 2.0 [2.0, 2.0] | 0.0 [0.0, 1.0] | 2.0 [2.0, 4.0] | 0.0 [0.0, 1.0] | 0.0 [0.0, 1.0] | 0.0 [0.0, 1.0] | 2.0 [2.0, 2.0] |
| n_intervals_500_to_2000ms | 4.0 [3.0, 4.0] | 3.0 [2.0, 4.0] | 4.0 [3.0, 4.0] | 6.0 [5.0, 7.0] | 4.0 [3.0, 4.0] | 4.0 [3.0, 4.0] | 4.0 [3.0, 4.0] | 9.0 [8.0, 11.0] |

## Additivity tests

**Definition**: expected_additive(X) = X(single_A) + X(single_B) − X(baseline); ratio = observed / expected; Δ_excess = observed − expected.
- ratio ≈ 1: additive
- ratio > 1: super-additive (synergistic)
- ratio < 1: sub-additive (combined < sum)

### Test 0 — diff-validator 2% loss (canonical, n=7)

- single_A = `delay_only_v1`
- single_B = `loss_only_v2`
- observed = `two_validator_pressure`

| metric | baseline | single_A | single_B | observed | expected_additive | ratio | Δ_excess |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| checkpoint_interval_ms_p50_true | 215.0 | 215.0 | 214.6 | 216.4 | 214.6 | 1.01 | +1.8 |
| checkpoint_interval_ms_p95_true | 263.2 | 257.4 | 264.3 | 267.5 | 258.5 | 1.03 | +9.0 |
| checkpoint_interval_ms_max_true | 1945.2 | 2224.4 | 1962.8 | 2325.7 | 2242.0 | 1.04 | +83.7 |
| checkpoint_count_true | 637.0 | 669.0 | 667.0 | 739.0 | 699.0 | 1.06 | +40.0 |
| n_intervals_gt_2000ms | 0.0 | 2.0 | 0.0 | 2.0 | 2.0 | 1.00 | +0.0 |
| n_intervals_500_to_2000ms | 4.0 | 3.0 | 4.0 | 6.0 | 3.0 | 2.00 | +3.0 |

### Test 1 — same-validator stacking (delay+loss both on v1)

- single_A = `delay_only_v1`
- single_B = `loss_only_v1`
- observed = `delay_loss_same_v1`

| metric | baseline | single_A | single_B | observed | expected_additive | ratio | Δ_excess |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| checkpoint_interval_ms_p50_true | 215.0 | 215.0 | 214.1 | 214.7 | 214.1 | 1.00 | +0.6 |
| checkpoint_interval_ms_p95_true | 263.2 | 257.4 | 265.6 | 241.8 | 259.8 | 0.93 | -17.9 |
| checkpoint_interval_ms_max_true | 1945.2 | 2224.4 | 1991.2 | 1956.0 | 2270.4 | 0.86 | -314.4 |
| checkpoint_count_true | 637.0 | 669.0 | 664.0 | 654.0 | 696.0 | 0.94 | -42.0 |
| n_intervals_gt_2000ms | 0.0 | 2.0 | 0.0 | 0.0 | 2.0 | 0.00 | -2.0 |
| n_intervals_500_to_2000ms | 4.0 | 3.0 | 4.0 | 4.0 | 3.0 | 1.33 | +1.0 |

### Test 2 — higher loss extreme (delay v1 + 5% loss v2)

- single_A = `delay_only_v1`
- single_B = `loss_high_v2`
- observed = `pressure_high_loss`

| metric | baseline | single_A | single_B | observed | expected_additive | ratio | Δ_excess |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| checkpoint_interval_ms_p50_true | 215.0 | 215.0 | 214.4 | 215.1 | 214.4 | 1.00 | +0.7 |
| checkpoint_interval_ms_p95_true | 263.2 | 257.4 | 221.6 | 290.9 | 215.8 | 1.35 | +75.1 |
| checkpoint_interval_ms_max_true | 1945.2 | 2224.4 | 1972.1 | 2297.5 | 2251.3 | 1.02 | +46.2 |
| checkpoint_count_true | 637.0 | 669.0 | 666.0 | 660.0 | 698.0 | 0.95 | -38.0 |
| n_intervals_gt_2000ms | 0.0 | 2.0 | 0.0 | 2.0 | 2.0 | 1.00 | +0.0 |
| n_intervals_500_to_2000ms | 4.0 | 3.0 | 4.0 | 9.0 | 3.0 | 3.00 | +6.0 |

## Per-rep raw (new cells only)

| scenario | rep | p50_true | p95_true | max | n_>2000 | n_500_2000 | ckpt_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| loss_only_v1 | 1 | 212.7 | 267.5 | 1876.6 | 0 | 4 | 664 |
| loss_only_v1 | 2 | 215.9 | 259.8 | 5193.8 | 3 | 3 | 802 |
| loss_only_v1 | 3 | 215.1 | 219.9 | 1927.7 | 0 | 4 | 692 |
| loss_only_v1 | 4 | 215.0 | 219.3 | 2026.1 | 1 | 3 | 655 |
| loss_only_v1 | 5 | 214.0 | 265.6 | 2011.0 | 1 | 3 | 652 |
| loss_only_v1 | 6 | 213.4 | 265.9 | 1856.6 | 0 | 4 | 668 |
| loss_only_v1 | 7 | 214.9 | 266.1 | 2055.6 | 1 | 3 | 647 |
| loss_only_v1 | 8 | 213.0 | 266.6 | 1991.2 | 0 | 4 | 654 |
| loss_only_v1 | 9 | 214.1 | 265.7 | 1934.0 | 0 | 4 | 673 |
| loss_only_v1 | 10 | 215.5 | 263.6 | 1992.8 | 0 | 4 | 666 |
| delay_loss_same_v1 | 1 | 214.7 | 219.6 | 1968.9 | 0 | 4 | 669 |
| delay_loss_same_v1 | 2 | 215.0 | 220.7 | 1863.6 | 0 | 4 | 654 |
| delay_loss_same_v1 | 3 | 215.1 | 224.3 | 2146.2 | 1 | 3 | 748 |
| delay_loss_same_v1 | 4 | 214.7 | 264.1 | 2001.5 | 1 | 3 | 669 |
| delay_loss_same_v1 | 5 | 214.0 | 264.5 | 1859.2 | 0 | 4 | 654 |
| delay_loss_same_v1 | 6 | 214.5 | 263.4 | 1882.1 | 0 | 4 | 652 |
| delay_loss_same_v1 | 7 | 215.0 | 263.7 | 2004.5 | 1 | 3 | 658 |
| delay_loss_same_v1 | 8 | 214.6 | 266.3 | 1859.6 | 0 | 4 | 651 |
| delay_loss_same_v1 | 9 | 215.0 | 219.5 | 1956.0 | 0 | 4 | 665 |
| delay_loss_same_v1 | 10 | 214.4 | 241.8 | 2051.0 | 1 | 3 | 638 |
| loss_high_v2 | 1 | 215.5 | 220.5 | 1873.7 | 0 | 4 | 696 |
| loss_high_v2 | 2 | 215.0 | 266.2 | 2019.0 | 1 | 3 | 666 |
| loss_high_v2 | 3 | 214.5 | 241.3 | 2044.7 | 1 | 3 | 662 |
| loss_high_v2 | 4 | 213.7 | 265.4 | 1991.7 | 0 | 4 | 641 |
| loss_high_v2 | 5 | 215.1 | 219.6 | 1880.8 | 0 | 4 | 680 |
| loss_high_v2 | 6 | 214.4 | 219.9 | 1866.4 | 0 | 4 | 652 |
| loss_high_v2 | 7 | 214.3 | 221.1 | 2020.7 | 3 | 1 | 694 |
| loss_high_v2 | 8 | 214.8 | 221.6 | 1972.1 | 0 | 4 | 688 |
| loss_high_v2 | 9 | 213.9 | 266.3 | 1914.6 | 0 | 4 | 635 |
| loss_high_v2 | 10 | 213.5 | 264.4 | 1982.4 | 0 | 4 | 667 |
| pressure_high_loss | 1 | 215.1 | 291.5 | 2393.9 | 2 | 11 | 682 |
| pressure_high_loss | 2 | 215.2 | 299.2 | 2530.2 | 2 | 8 | 645 |
| pressure_high_loss | 3 | 215.1 | 290.9 | 2148.2 | 2 | 9 | 646 |
| pressure_high_loss | 4 | 215.3 | 289.4 | 2105.1 | 3 | 6 | 682 |
| pressure_high_loss | 5 | 215.1 | 277.5 | 2459.1 | 2 | 10 | 670 |
| pressure_high_loss | 6 | 216.7 | 379.8 | 13034.8 | 3 | 22 | 892 |
| pressure_high_loss | 7 | 214.9 | 300.5 | 2263.4 | 2 | 8 | 660 |
| pressure_high_loss | 8 | 214.8 | 288.2 | 2518.1 | 2 | 10 | 703 |
| pressure_high_loss | 9 | 214.5 | 290.8 | 2044.0 | 2 | 7 | 610 |
| pressure_high_loss | 10 | 214.2 | 360.7 | 2297.5 | 2 | 11 | 596 |
