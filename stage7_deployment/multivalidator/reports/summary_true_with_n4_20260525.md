# True-cadence checkpoint summary (log-derived)

- Generated (UTC): 2026-05-25T10:49:53+00:00
- Tool: tools/extract_ckpt_metrics_from_logs.py (parses execute_checkpoint{seq=N} from fullnode INFO log)
- Reps processed: 100 / 100

## Per-scenario aggregate (n=10)

| scenario | p50_true median(ms) | p50_true CV% | p95_true median(ms) | p95_true CV% | max median | n_epoch_gaps median | n_mid_tail median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 215.0 | 0.32 | 263.2 | 9.24 | 1945.2 | 0 | 4 |
| delay_low | 212.1 | 0.07 | 226.6 | 8.50 | 1957.1 | 0 | 4 |
| delay_high | 215.4 | 0.10 | 304.4 | 1.16 | 2194.0 | 2 | 4 |
| loss_low | 217.3 | 0.73 | 223.6 | 9.76 | 2197.3 | 3 | 1 |
| crash_one_validator | 216.3 | 0.05 | 420.0 | 0.55 | 2042.5 | 2 | 24 |
| two_validator_pressure | 216.4 | 0.38 | 267.5 | 3.57 | 2325.7 | 2 | 6 |
| baseline_n4 | 210.3 | 0.22 | 212.3 | 0.20 | 1566.1 | 0 | 2 |
| delay_only_v1_n4 | 210.7 | 0.31 | 318.4 | 16.29 | 1572.0 | 0 | 2 |
| loss_only_v2_n4 | 210.6 | 0.15 | 214.0 | 3.68 | 1609.9 | 0 | 2 |
| two_validator_pressure_n4 | 210.8 | 0.14 | 372.7 | 12.20 | 1564.2 | 0 | 2 |

## Per-rep raw

| scenario | rep | p50_true | p95_true | max | n_gt_2000 | n_500_2000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 1 | 213.7 | 223.6 | 2008.6 | 1 | 3 |
| baseline | 2 | 215.1 | 263.2 | 2034.0 | 1 | 3 |
| baseline | 3 | 215.0 | 219.6 | 1933.4 | 0 | 4 |
| baseline | 4 | 214.7 | 265.0 | 1960.9 | 0 | 4 |
| baseline | 5 | 215.8 | 263.8 | 2168.2 | 1 | 3 |
| baseline | 6 | 213.9 | 267.1 | 1886.0 | 0 | 4 |
| baseline | 7 | 215.3 | 264.7 | 1930.6 | 0 | 4 |
| baseline | 8 | 215.0 | 219.5 | 2035.2 | 1 | 3 |
| baseline | 9 | 215.6 | 265.7 | 1945.2 | 0 | 4 |
| baseline | 10 | 215.4 | 220.5 | 1858.2 | 0 | 4 |
| delay_low | 1 | 212.0 | 226.6 | 1965.1 | 0 | 4 |
| delay_low | 2 | 212.3 | 218.4 | 1953.7 | 0 | 4 |
| delay_low | 3 | 212.0 | 262.1 | 1938.1 | 0 | 5 |
| delay_low | 4 | 212.1 | 228.9 | 1883.7 | 0 | 4 |
| delay_low | 5 | 212.1 | 220.1 | 2004.6 | 1 | 3 |
| delay_low | 6 | 212.3 | 262.0 | 2093.1 | 1 | 3 |
| delay_low | 7 | 212.3 | 218.3 | 1966.5 | 0 | 3 |
| delay_low | 8 | 212.3 | 261.0 | 1957.1 | 0 | 4 |
| delay_low | 9 | 212.5 | 260.9 | 2241.2 | 2 | 1 |
| delay_low | 10 | 212.1 | 224.7 | 1920.1 | 0 | 4 |
| delay_high | 1 | 215.3 | 302.7 | 2221.6 | 2 | 4 |
| delay_high | 2 | 215.7 | 310.3 | 2537.4 | 2 | 6 |
| delay_high | 3 | 215.1 | 308.1 | 2425.2 | 2 | 3 |
| delay_high | 4 | 215.5 | 304.8 | 2113.9 | 2 | 6 |
| delay_high | 5 | 215.5 | 298.6 | 2151.3 | 2 | 2 |
| delay_high | 6 | 215.2 | 309.4 | 2196.8 | 2 | 5 |
| delay_high | 7 | 215.4 | 308.3 | 2179.1 | 2 | 4 |
| delay_high | 8 | 215.4 | 304.4 | 2178.7 | 2 | 4 |
| delay_high | 9 | 215.2 | 304.2 | 2194.0 | 2 | 3 |
| delay_high | 10 | 215.7 | 304.1 | 2521.0 | 2 | 2 |
| loss_low | 1 | 214.6 | 266.6 | 2022.5 | 1 | 3 |
| loss_low | 2 | 214.2 | 220.6 | 2053.1 | 1 | 3 |
| loss_low | 3 | 215.2 | 220.5 | 1981.6 | 0 | 4 |
| loss_low | 4 | 217.6 | 222.9 | 2165.1 | 3 | 1 |
| loss_low | 5 | 216.9 | 269.0 | 2422.3 | 4 | 0 |
| loss_low | 6 | 217.3 | 269.0 | 2409.2 | 4 | 1 |
| loss_low | 7 | 217.9 | 225.3 | 2197.3 | 3 | 0 |
| loss_low | 8 | 218.0 | 268.0 | 2291.3 | 4 | 0 |
| loss_low | 9 | 218.6 | 223.6 | 2235.0 | 3 | 1 |
| loss_low | 10 | 218.0 | 223.4 | 2445.8 | 3 | 1 |
| crash_one_validator | 1 | 216.3 | 420.4 | 2331.8 | 3 | 23 |
| crash_one_validator | 2 | 216.3 | 419.5 | 2025.8 | 2 | 24 |
| crash_one_validator | 3 | 216.1 | 421.3 | 2042.5 | 2 | 24 |
| crash_one_validator | 4 | 216.3 | 420.0 | 2085.9 | 3 | 23 |
| crash_one_validator | 5 | 216.4 | 420.1 | 2012.8 | 1 | 25 |
| crash_one_validator | 6 | 216.3 | 412.9 | 2009.6 | 1 | 25 |
| crash_one_validator | 7 | 216.1 | 419.5 | 2171.6 | 2 | 25 |
| crash_one_validator | 8 | 216.5 | 420.1 | 2057.3 | 3 | 23 |
| crash_one_validator | 9 | 216.2 | 420.2 | 2034.9 | 2 | 23 |
| crash_one_validator | 10 | 216.4 | 419.6 | 2054.8 | 2 | 24 |
| two_validator_pressure | 1 | 215.7 | 270.5 | 2174.3 | 2 | 6 |
| two_validator_pressure | 2 | 216.4 | 279.9 | 2603.0 | 2 | 6 |
| two_validator_pressure | 3 | 216.2 | 267.5 | 2259.5 | 2 | 7 |
| two_validator_pressure | 4 | 216.0 | 265.4 | 2292.4 | 3 | 7 |
| two_validator_pressure | 5 | 216.5 | 266.3 | 2275.1 | 2 | 3 |
| two_validator_pressure | 6 | 216.8 | 265.6 | 2331.1 | 2 | 5 |
| two_validator_pressure | 7 | 216.4 | 266.6 | 2325.7 | 2 | 5 |
| two_validator_pressure | 8 | 218.3 | 293.2 | 2946.4 | 4 | 9 |
| two_validator_pressure | 9 | 216.9 | 277.9 | 3018.6 | 4 | 3 |
| two_validator_pressure | 10 | 217.9 | 285.5 | 2679.6 | 4 | 8 |
| baseline_n4 | 1 | 209.5 | 211.7 | 1568.8 | 0 | 2 |
| baseline_n4 | 2 | 210.5 | 212.3 | 1548.7 | 0 | 2 |
| baseline_n4 | 3 | 210.3 | 212.3 | 1567.4 | 0 | 2 |
| baseline_n4 | 4 | 209.4 | 211.3 | 1555.7 | 0 | 2 |
| baseline_n4 | 5 | 210.3 | 211.8 | 1757.9 | 0 | 2 |
| baseline_n4 | 6 | 210.3 | 212.3 | 1728.4 | 0 | 2 |
| baseline_n4 | 7 | 209.3 | 212.2 | 1563.7 | 0 | 2 |
| baseline_n4 | 8 | 210.4 | 212.7 | 1735.3 | 0 | 2 |
| baseline_n4 | 9 | 210.4 | 212.5 | 1566.1 | 0 | 2 |
| baseline_n4 | 10 | 210.4 | 212.5 | 1549.9 | 0 | 2 |
| delay_only_v1_n4 | 1 | 210.5 | 342.0 | 1182.4 | 0 | 2 |
| delay_only_v1_n4 | 2 | 210.6 | 336.0 | 1572.6 | 0 | 2 |
| delay_only_v1_n4 | 3 | 210.2 | 318.4 | 1708.9 | 0 | 2 |
| delay_only_v1_n4 | 4 | 210.5 | 456.3 | 1557.0 | 0 | 4 |
| delay_only_v1_n4 | 5 | 210.7 | 304.1 | 1569.2 | 0 | 2 |
| delay_only_v1_n4 | 6 | 211.0 | 302.6 | 1715.7 | 0 | 2 |
| delay_only_v1_n4 | 7 | 210.9 | 293.4 | 1572.0 | 0 | 2 |
| delay_only_v1_n4 | 8 | 211.6 | 339.9 | 1546.6 | 0 | 2 |
| delay_only_v1_n4 | 9 | 211.5 | 250.3 | 4792.8 | 1 | 0 |
| delay_only_v1_n4 | 10 | 212.3 | 349.9 | 1799.7 | 0 | 3 |
| loss_only_v2_n4 | 1 | 211.4 | 214.9 | 1808.9 | 0 | 2 |
| loss_only_v2_n4 | 2 | 211.1 | 215.6 | 1609.9 | 0 | 2 |
| loss_only_v2_n4 | 3 | 211.0 | 214.0 | 1859.9 | 0 | 2 |
| loss_only_v2_n4 | 4 | 210.9 | 238.6 | 1777.3 | 0 | 2 |
| loss_only_v2_n4 | 5 | 210.8 | 214.1 | 1618.1 | 0 | 2 |
| loss_only_v2_n4 | 6 | 210.6 | 212.4 | 1595.1 | 0 | 2 |
| loss_only_v2_n4 | 7 | 210.5 | 213.4 | 1572.2 | 0 | 2 |
| loss_only_v2_n4 | 8 | 210.4 | 214.5 | 1126.3 | 0 | 3 |
| loss_only_v2_n4 | 9 | 210.6 | 212.4 | 1614.1 | 0 | 1 |
| loss_only_v2_n4 | 10 | 210.5 | 212.0 | 1563.2 | 0 | 2 |
| two_validator_pressure_n4 | 1 | 210.6 | 443.1 | 786.1 | 0 | 4 |
| two_validator_pressure_n4 | 2 | 210.6 | 429.8 | 1564.2 | 0 | 2 |
| two_validator_pressure_n4 | 3 | 211.2 | 324.7 | 1579.8 | 0 | 2 |
| two_validator_pressure_n4 | 4 | 211.0 | 372.4 | 1585.3 | 0 | 2 |
| two_validator_pressure_n4 | 5 | 210.8 | 451.9 | 1566.5 | 0 | 4 |
| two_validator_pressure_n4 | 6 | 210.8 | 334.3 | 1577.2 | 0 | 1 |
| two_validator_pressure_n4 | 7 | 210.5 | 437.8 | 1571.1 | 0 | 4 |
| two_validator_pressure_n4 | 8 | 210.6 | 350.3 | 1195.9 | 0 | 2 |
| two_validator_pressure_n4 | 9 | 211.0 | 418.5 | 1561.9 | 0 | 3 |
| two_validator_pressure_n4 | 10 | 211.3 | 372.7 | 1559.2 | 0 | 2 |