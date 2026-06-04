# Stage 6 Calibrated Replay (driven by Stage 7 Docker measurements)

- Generated (UTC): 2026-05-25T03:03:00.305389+00:00
- Patch source: `..\stage7_deployment\multivalidator\data\calibration_patch_20260525.json` (stage7_multivalidator_real_calibration)
- Replay base: n=7, f=2, rounds=1000, n_trials=4 per scenario
- Raw data: `sweep_calibrated_20260525_030300Z.csv`, `sweep_calibrated_20260525_030300Z.json` (same directory as patch)

## Mapping (engineering → protocol)

For each Docker scenario S, treat measured `rpc_latency_ms_p50` / `rpc_latency_ms_p95` as the p50 / p95 of a lognormal:

```
sigma = ln(p95 / p50) / z_{0.95},     z_{0.95} = 1.6448536
mean  = p50 * exp(sigma**2 / 2)        (= E[X] of the lognormal)
```

These are then passed to `core.delay.DelayDistribution(kind='lognormal', mean, sigma)`. The SimPy delay layer converts back to underlying `mu` internally.

## Bridge limitations

- Docker `rpc_latency_ms_*` is **client-observed read-RPC latency against the fullnode**, not the **inter-validator message-delivery delay** modeled by `core/delay.py`. The calibration here is a first-order proxy; it does NOT identify the simulator's delay parameters with measured quantities at the physical layer.
- This replay intentionally relaxes the stage6 convention of fixed `mean=1.0`. Each scenario gets its own time scale (`mean` ∝ measured p50). As a result, **across scenarios the absolute values of net_adv / Δ_recover / Δ_save in this table are NOT on a common time axis** and must not be compared directly. Within-scenario comparison against Docker observations is what this replay supports.
- `recovery_time_ms` (only meaningful for `crash_one_validator`) is reported by Docker in milliseconds of wall-clock pause-to-recovery; SimPy `Δ_recover` is per-event reconciliation latency in abstract delay units. The two are not on the same dimension and are reported side-by-side for context only.

## Per-scenario replay

| scenario | rpc_p50(ms) | rpc_p95(ms) | mapped σ | mapped mean | ρ | Δ_recover | Δ_save | net_adv | recon_triggers | passed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| baseline | 8 | 23 | 0.6420 | 9.8310 | 0.0311 | 5.3185 | 10.7630 | 10.5973 | 218.0 | ✓ |
| delay_low | 13 | 26 | 0.4214 | 14.2071 | 0.0059 | 4.8260 | 14.8034 | 14.7748 | 41.2 | ✓ |
| delay_high | 11 | 25 | 0.4991 | 12.4592 | 0.0134 | 5.4494 | 13.2194 | 13.1462 | 94.0 | ✓ |
| loss_low | 4 | 25 | 1.1141 | 7.4405 | 0.0909 | 4.9670 | 8.5090 | 8.0577 | 636.0 | ✓ |
| crash_one_validator | 4 | 25 | 1.1141 | 7.4405 | 0.0909 | 4.9670 | 8.5090 | 8.0577 | 636.0 | ✓ |
| two_validator_pressure | 4 | 25 | 1.1141 | 7.4405 | 0.0909 | 4.9670 | 8.5090 | 8.0577 | 636.0 | ✓ |

## Side-by-side: Docker measurement vs SimPy replay

This table is *not* an apples-to-apples error metric (different physical dimensions per the bridge note above); it is a co-location of what each layer reports under the same labeled scenario.

| scenario | Docker rpc_p50/p95 (ms) | Docker recovery (ms) | Docker availability | SimPy ρ | SimPy Δ_recover | SimPy net_adv |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 8 / 23 | n/a | 1.000 | 0.0311 | 5.3185 | 10.5973 |
| delay_low | 13 / 26 | n/a | 1.000 | 0.0059 | 4.8260 | 14.7748 |
| delay_high | 11 / 25 | n/a | 1.000 | 0.0134 | 5.4494 | 13.1462 |
| loss_low | 4 / 25 | n/a | 1.000 | 0.0909 | 4.9670 | 8.0577 |
| crash_one_validator | 4 / 25 | 130920 | 1.000 | 0.0909 | 4.9670 | 8.0577 |
| two_validator_pressure | 4 / 25 | n/a | 1.000 | 0.0909 | 4.9670 | 8.0577 |

## Reading guide

- All SimPy quantities (ρ, Δ_recover, Δ_save, net_adv, recon_triggers) are *simulation results from an analytical-model controlled numerical experiment* (per stage6 §4.6 measurement convention); they are NOT real protocol measurements. The `data_kind` field in the CSV/JSON carries this label.
- The Docker columns are real engineering measurements from 7-validator container deployments (`recovery_time_ms` only for crash_one_validator; `availability` was 1.0 across all 60 runs).
- Use this table to argue: "under each Docker-measured RPC-latency envelope mapped into the simulator, the SimPy model predicts X for protocol-level quantities Y" — not to argue "simulator matches reality."