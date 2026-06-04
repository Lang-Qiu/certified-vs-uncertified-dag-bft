# True-cadence checkpoint summary (log-derived)

- Generated (UTC): 2026-05-25T10:14:18+00:00
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
| loss_only_v1_match | 214.1 | 0.51 | 265.6 | 7.54 | 1991.2 | 0 | 4 |
| delay_loss_same_v1 | 214.7 | 0.17 | 241.8 | 8.83 | 1956.0 | 0 | 4 |
| loss_high_v2 | 214.4 | 0.30 | 221.6 | 9.30 | 1972.1 | 0 | 4 |
| pressure_high_loss | 215.1 | 0.30 | 290.9 | 11.18 | 2297.5 | 2 | 9 |

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
| loss_only_v1_match | 1 | 212.7 | 267.5 | 1876.6 | 0 | 4 |
| loss_only_v1_match | 2 | 215.9 | 259.8 | 5193.8 | 3 | 3 |
| loss_only_v1_match | 3 | 215.1 | 219.9 | 1927.7 | 0 | 4 |
| loss_only_v1_match | 4 | 215.0 | 219.3 | 2026.1 | 1 | 3 |
| loss_only_v1_match | 5 | 214.0 | 265.6 | 2011.0 | 1 | 3 |
| loss_only_v1_match | 6 | 213.4 | 265.9 | 1856.6 | 0 | 4 |
| loss_only_v1_match | 7 | 214.9 | 266.1 | 2055.6 | 1 | 3 |
| loss_only_v1_match | 8 | 213.0 | 266.6 | 1991.2 | 0 | 4 |
| loss_only_v1_match | 9 | 214.1 | 265.7 | 1934.0 | 0 | 4 |
| loss_only_v1_match | 10 | 215.5 | 263.6 | 1992.8 | 0 | 4 |
| delay_loss_same_v1 | 1 | 214.7 | 219.6 | 1968.9 | 0 | 4 |
| delay_loss_same_v1 | 2 | 215.0 | 220.7 | 1863.6 | 0 | 4 |
| delay_loss_same_v1 | 3 | 215.1 | 224.3 | 2146.2 | 1 | 3 |
| delay_loss_same_v1 | 4 | 214.7 | 264.1 | 2001.5 | 1 | 3 |
| delay_loss_same_v1 | 5 | 214.0 | 264.5 | 1859.2 | 0 | 4 |
| delay_loss_same_v1 | 6 | 214.5 | 263.4 | 1882.1 | 0 | 4 |
| delay_loss_same_v1 | 7 | 215.0 | 263.7 | 2004.5 | 1 | 3 |
| delay_loss_same_v1 | 8 | 214.6 | 266.3 | 1859.6 | 0 | 4 |
| delay_loss_same_v1 | 9 | 215.0 | 219.5 | 1956.0 | 0 | 4 |
| delay_loss_same_v1 | 10 | 214.4 | 241.8 | 2051.0 | 1 | 3 |
| loss_high_v2 | 1 | 215.5 | 220.5 | 1873.7 | 0 | 4 |
| loss_high_v2 | 2 | 215.0 | 266.2 | 2019.0 | 1 | 3 |
| loss_high_v2 | 3 | 214.5 | 241.3 | 2044.7 | 1 | 3 |
| loss_high_v2 | 4 | 213.7 | 265.4 | 1991.7 | 0 | 4 |
| loss_high_v2 | 5 | 215.1 | 219.6 | 1880.8 | 0 | 4 |
| loss_high_v2 | 6 | 214.4 | 219.9 | 1866.4 | 0 | 4 |
| loss_high_v2 | 7 | 214.3 | 221.1 | 2020.7 | 3 | 1 |
| loss_high_v2 | 8 | 214.8 | 221.6 | 1972.1 | 0 | 4 |
| loss_high_v2 | 9 | 213.9 | 266.3 | 1914.6 | 0 | 4 |
| loss_high_v2 | 10 | 213.5 | 264.4 | 1982.4 | 0 | 4 |
| pressure_high_loss | 1 | 215.1 | 291.5 | 2393.9 | 2 | 11 |
| pressure_high_loss | 2 | 215.2 | 299.2 | 2530.2 | 2 | 8 |
| pressure_high_loss | 3 | 215.1 | 290.9 | 2148.2 | 2 | 9 |
| pressure_high_loss | 4 | 215.3 | 289.4 | 2105.1 | 3 | 6 |
| pressure_high_loss | 5 | 215.1 | 277.5 | 2459.1 | 2 | 10 |
| pressure_high_loss | 6 | 216.7 | 379.8 | 13034.8 | 3 | 22 |
| pressure_high_loss | 7 | 214.9 | 300.5 | 2263.4 | 2 | 8 |
| pressure_high_loss | 8 | 214.8 | 288.2 | 2518.1 | 2 | 10 |
| pressure_high_loss | 9 | 214.5 | 290.8 | 2044.0 | 2 | 7 |
| pressure_high_loss | 10 | 214.2 | 360.7 | 2297.5 | 2 | 11 |