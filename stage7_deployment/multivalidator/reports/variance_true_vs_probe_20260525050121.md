# ckpt_interval_p95: probe-based metric vs log-derived truth

- Generated (UTC): 2026-05-25T05:01:21+00:00
- probe metric: `consensus_metrics.json.checkpoint_interval_ms_p95` (averages over 14 rpc-probe windows)
- log-derived truth: `consensus_metrics_true.json.checkpoint_interval_ms_p95_true` (true per-checkpoint intervals)
- See `reports/ckpt_p95_layer_localization_report_20260525.md` for the measurement-pipeline failure mode

| scenario | n | probe median | probe CV% | true median | true CV% | true/probe ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 10 | 226.0 | 5.82 | 263.2 | 9.24 | 1.16 |
| delay_low | 10 | 226.0 | 3.72 | 226.6 | 8.50 | 1.00 |
| delay_high | 10 | 254.0 | 0.69 | 304.4 | 1.16 | 1.20 |
| loss_low | 10 | 288.0 | 12.53 | 223.6 | 9.76 | 0.78 |
| crash_one_validator | 10 | 290.0 | 8.97 | 420.0 | 0.55 | 1.45 |
| two_validator_pressure | 10 | 290.0 | 63.23 | 267.5 | 3.57 | 0.92 |