# Stage 7 Validity Audit

## Official Entry Decision

- `sui start --committee-size 7` is a single-process in-memory swarm and is only eligible for pre-calibration or smoke checks.
- Primary multi-validator evidence must come from independent validator containers generated through `sui genesis --committee-size 7`, followed by per-container execution with `sui-node --config-path <validator-yaml>`.
- The deterministic config generator records the intended run topology and official genesis command, but it does not fabricate Sui key material, validator yaml files, `network.yaml`, `fullnode.yaml`, `genesis.blob`, or genesis hashes.
- The Dockerfile now declares both `sui` and `sui-node`, but the local `stage7-sui:local` image must be rebuilt and verified with `command -v sui-node` before the independent-container route can produce primary evidence.
- Local genesis probes under `data/tmp/` are structure checks only. They may contain temporary key material and are not eligible for primary claims or paper evidence registration.

## Verification (2026-05-25)

The conditions stated above are satisfied for the 60 formal runs published in `reports/论文级多验证者共识实验结果_20260524.md`:

- `stage7-sui:local` image is built and recorded in `data/manifests/environment_snapshot.json` (id `ad00f9ebf187`, sui commit `62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a`).
- All 60 runs were driven by independent `validator-1..7` + `fullnode` containers (8 per run, 480 total). Container `Path` field in every `evidence/container_state/<run>-validator-*.inspect.json` is `sui-node` with args `--config-path /mvdata/runs/<run>/official-genesis/<ip>-<port>.yaml`; image digest matches `stage7-sui:local`. No run was driven by `sui start --committee-size`.
- Per-run `official-genesis/{genesis.blob, network.yaml, fullnode.yaml, client.yaml, authorities_db/*, consensus_db/*}` are produced by `sui genesis --committee-size 7` and are registered in `manifest.json` with SHA256. Re-verification on 2026-05-25 (`tools/audit_formal_60.ps1`) confirmed 60/60 manifests pass hash check with zero mismatches.
- No artifact under `data/tmp/` is referenced in any of the 60 formal `manifest.json` files; pre-calibration probes remain isolated from the primary evidence set.

Re-check artifact: `reports/audit_recheck_20260525102855.md`.
