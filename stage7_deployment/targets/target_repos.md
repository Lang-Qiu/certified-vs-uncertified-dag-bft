# Stage 2 Target Repository Assessment

## Selection Criteria

| Criterion | Why It Matters | Acceptance |
|---|---|---|
| Active upstream | Avoid building against abandoned code unless used as a legacy baseline | Repo has recent development or official migration path |
| DAG-BFT relevance | Must exercise the protocol family discussed in the paper | Contains Narwhal/Bullshark/Mysticeti or adjacent Sui consensus code |
| Local build feasibility | Stage 2 must be reproducible on a local workstation | Docker or Cargo build path can be scripted |
| Measurement surface | Need latency, recovery, and fault data | Logs, metrics, or instrumentation points are available |
| Cost boundary | Avoid cloud-only experiments for first pass | Local testnet path exists or can be approximated |

## Candidate A: MystenLabs/sui

- URL: `https://github.com/MystenLabs/sui.git`
- Role: Primary target.
- Reason: Live Sui repository; current Narwhal development moved into this repository; Mysticeti/Sui consensus implementation is maintained here.
- Build path: Docker image from source, then run `sui start --with-faucet --force-regenesis` for smoke testing because `sui-test-validator` is a deprecation stub in the pinned checkout. A multi-node benchmark/orchestrator path can be assessed later if present in the checked-out commit.
- Measurement path: container logs, tracing output, RPC timing, and benchmark/orchestrator output.
- Decision: Use first.

## Candidate B: MystenLabs/narwhal

- URL: `https://github.com/MystenLabs/narwhal.git`
- Role: Legacy fallback and benchmark reference.
- Reason: Archived repository with an explicit migration note to Sui; still useful if its local benchmark is easier to run and compare to Stage 1 assumptions.
- Build path: `benchmark` directory and Fabric-based local benchmark, if dependencies can be installed.
- Measurement path: benchmark summary output.
- Decision: Do not use as primary; use only if Sui local multi-node path is blocked.

## Candidate C: asonnino/mysticeti paper branch

- URL: `https://github.com/asonnino/mysticeti.git`
- Role: Paper-artifact reference only.
- Reason: Mysticeti paper appendix references this repository/branch for cloud orchestration. It may be useful for understanding benchmark parameters but should not be the first local implementation target.
- Build path: inspect only after Sui path is assessed.
- Measurement path: no local commitment in this plan.
- Decision: Reference only unless a later feasibility pass approves it.

## Chosen Path

1. Clone `MystenLabs/sui` under `stage7_deployment/external/sui`.
2. Check out the pinned assessed commit unless a later run intentionally overrides it.
3. Check whether the checkout exposes local multi-node or orchestrator commands.
4. If only the local `sui start` path is feasible, use it as a smoke target and document the limitation.
5. If a multi-validator local benchmark is feasible, make it the main experiment target.

## Local Inspection Result

- Date: 2026-05-23
- Sui commit: 62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a
- Fetch command: `powershell.exe -ExecutionPolicy Bypass -File stage7_deployment/scripts/fetch_targets.ps1`
- Candidate entrypoint scratch inventory: `stage7_deployment/data/tmp/sui_entrypoints.txt`
- Multi-node search scratch evidence: `stage7_deployment/data/tmp/sui_multinode_search.txt`
- Multi-node search command: `rg -n "orchestrator|testbed|benchmark|committee|validator" .\stage7_deployment\external\sui\crates .\stage7_deployment\external\sui\consensus > .\stage7_deployment\data\tmp\sui_multinode_search.txt`
- Multi-node search conclusion: the checkout exposes local swarm/test-cluster/benchmark/committee-size clues, but not a stable Docker Compose entrypoint with one independently managed validator service per container.
- First executable target: `sui start --with-faucet --force-regenesis` for smoke test because `crates/sui-test-validator/src/main.rs` only reports deprecation at this commit. Multi-node target remains a later selection after inspecting orchestrator/benchmark availability.

The entrypoint inventory is ignored scratch output, not durable evidence. Regenerate it from the checked-out Sui tree whenever needed:

```powershell
New-Item -ItemType Directory -Force stage7_deployment\data\tmp | Out-Null
Get-ChildItem stage7_deployment\external\sui -Recurse | Where-Object { $_.FullName -match 'consensus|benchmark|orchestrator|validator' } | Select-Object -ExpandProperty FullName | Sort-Object | Out-File -FilePath stage7_deployment\data\tmp\sui_entrypoints.txt -Encoding utf8
```

## Multi-Validator Decision

Decision: Use `sui start --with-faucet --force-regenesis` local smoke evidence and defer multi-validator expansion to the next iteration.

Reason: The checked-out Sui commit does not expose a stable local multi-validator path within the local resource budget. The inspected source includes local swarm/test-cluster and benchmark code, and `sui start` can generate a local network with `--committee-size`, but this is not a stable Docker Compose entrypoint with one independently managed validator service per container.

Implementation impact: Keep Stage 2 claims limited to local real-protocol smoke, delay/fault capture, and calibration workflow scaffolding.
