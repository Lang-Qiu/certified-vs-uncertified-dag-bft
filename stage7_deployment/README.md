# stage7_deployment - Real DAG-BFT Deployment Harness

This directory contains Stage 2 of `仿真与部署_实施计划.md`: a local real-protocol deployment harness for measuring latency, recovery cost, and fault effects in a DAG-BFT implementation.

## Scope

- Primary target: MystenLabs `sui`, because current Narwhal/Bullshark/Mysticeti development lives there.
- Legacy fallback: archived `MystenLabs/narwhal`, only for build/benchmark comparison if the Sui path is infeasible locally.
- Outputs: raw logs, derived latency/cost data, calibration records against `stage6_simulation/`, and a findings summary.

## Honest Boundary

Stage 2 measures mixed real-protocol behavior. It does not isolate the certification variable by itself. Controlled isolation remains the responsibility of `stage6_simulation/`.

## Required Tools

- Docker Desktop with Linux containers
- Docker Compose v2
- Git
- Python 3.9+
- Rust/Cargo for local source inspection and optional native builds
- `tc netem` inside Linux containers for delay and loss injection

## Common Commands

```powershell
.\scripts\check_prereqs.ps1
.\scripts\fetch_targets.ps1
.\scripts\build_sui_image.ps1
.\scripts\run_local_testnet.ps1
```

## Fault Injection Notes

The current smoke target runs the Sui `sui start` local validator/fullnode/faucet path. Fault injection on this single-container target validates recovery behavior and real-deployment log capture only. Multi-validator consensus conclusions require a later Compose profile with separate validator containers.

## Current Execution Scope

The current harness runs the Sui local validator smoke target through `sui start --with-faucet --force-regenesis`. It proves buildability, logging, netem injection, process restart capture, and Stage 1/Stage 2 data plumbing. Multi-validator consensus conclusions require a separate `multinode` profile once a stable local multi-node entrypoint is selected.

## Retention

Every experiment must write raw output under `data/raw/`, derived output under `data/derived/`, figures under `figures/`, and a manifest entry in `data/manifest.json`.
