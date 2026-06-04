# Phase A results — deployment calibration of the recovery-side contingent liability ρ·Δ_recover

**Date:** 2026-05-31 · **Platform:** real Sui/Mysticeti, n=7 multi-validator (stage7 harness), pinned
commit `62ee6ada`, image `stage9-sui-certgate:local` · **Knob:** `SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS`
(injects a per-fetch-batch sleep in the consensus PULL path: `synchronizer::process_fetched_blocks` +
`commit_syncer::fetch_once`; every event logs `STAGE9_RECOVERY`, doubling as the ρ event counter).

## Headline

The recovery-side contingent liability **ρ·Δ_recover is invisible off the consensus critical path and
materialises cleanly on it.** Calibrated on identical Δ_recover sweeps:

| regime | observable | Pearson r | within-level CV | shape |
|---|---|---:|---:|---|
| **off** critical path (single briefly-partitioned node) | node catch-up `catchup_s` | **+0.43** | up to 0.31 | flat / noisy / non-monotonic |
| **on** critical path (rotation forces sub-quorum) | cadence stall `t_resume` | **+0.85** | 0.07–0.13 | clean, monotonic, ~linear |

Figure: `figures/phaseA_recover_calibration.png` (Panel A = calibration curve + OLS; Panel B = the contrast).

## Why two regimes — the experimental-design crux

Mysticeti recovers a briefly-offline node via a **mix of PUSH (peers broadcast current blocks) and PULL
(node fetches missing ancestors)**; the Δ_recover knob lives only on PULL. For a *single* node, 6 healthy
peers already form quorum, so the laggard's PULL is **off the critical path** → its delay never reaches
observable cadence, and the protocol even reroutes recovery toward PUSH as the delay grows (pull-event
count *falls* with Δ_recover). Result: no clean signal.

A **static** partition cannot fix this: to open a gap you need a progressing quorum (≥5 of 7), which by
definition *excludes* — and therefore doesn't *need* — the recoverers; a 3/7 static split instead drops
both sides below quorum → whole network halts, no gap, knob never fires.

The fix is a **rotation (churn)**: cut `{v1,v2}` to open a gap (carriers `{v3..v7}=5` progress, 90 s >
push window → forces pull), then **heal `{v1,v2}` while cutting `{v3,v4}`** so the current set `{v5,v6,v7}=3`
is sub-quorum — the network now *stalls until v1,v2 finish PULLing their gap*. Δ_recover gates that pull,
and the observable is `t_resume` = wall-clock from rotation to cadence resumption.

## Critical-path calibration (the clean curve) — n=7

| Δ_recover (ms) | t_resume mean ± sd (s) | pull events v1+v2 |
|---:|---:|---:|
| 0    | 29.1 ± 3.7 | 1347 |
| 250  | 35.1 ± 2.9 | 403 |
| 500  | 38.1 ± 2.9 | 261 |
| 1000 | 44.2 ± 2.9 | 189 |

- **OLS:** `t_resume = 30.3 + 0.0145·Δ_recover` (s), R²=0.73, slope ≈ **14.5 s per 1000 ms** injected.
- **Approximately linear, mildly saturating, no super-linearity** (marginal steps +6.0 / +3.0 / +3.0 s per
  250 ms). Holding fault intensity fixed, the liability is **linear in Δ_recover**.

## Cross-scale replication — n=4 (robustness)

Same rotation at n=4 (f=1, quorum=3): cut `{v1}` to open the gap (carriers `{v2,v3,v4}=3` progress), then
heal `{v1}` / cut `{v2}` → current `{v3,v4}=2` sub-quorum → stall until v1 pulls. Harness
`scripts/phaseA_criticalpath_partition_n4.ps1`, data `phaseA_criticalpath_n4_summary.csv`.

| Δ_recover (ms) | n=4 t_resume mean ± sd (s) | n=7 t_resume (s) |
|---:|---:|---:|
| 0    | 22.1 ± 1.4 | 29.1 ± 3.7 |
| 250  | 30.1 ± 0.0 | 35.1 ± 2.9 |
| 500  | 32.1 ± 1.4 | 38.1 ± 2.9 |
| 1000 | 42.2 ± 4.3 | 44.2 ± 2.9 |

- **The dose-response replicates** — n=4: `t_resume = 23.3 + 0.0190·Δ_recover`, **r=+0.935, R²=0.875**
  (even cleaner than n=7's r=+0.854). Not an n=7 artifact.
- **Scale-dependent magnitude (defensible mechanism):** n=4 has a *lower baseline* (intercept 23.3 vs 30.3 s
  — smaller committee reconciles faster) but a *steeper slope* (**19.0 vs 14.5 s per 1000 ms**). At n=4 a
  single node is the sole critical recoverer with zero redundancy, so Δ_recover passes through more directly;
  at n=7 two nodes recover in parallel with slight slack, diluting per-unit cost. → the recovery liability is
  **committee-structure-dependent**, tightening as the committee shrinks. Directly supports the paper thesis.
- **Separability of the two cost axes:** stall *rises* (29→44 s) while pull-event count *falls* (1347→189).
  The cost is carried by the per-event **delay (Δ_recover)**, not the event **count (ρ)** — they are
  independent axes, exactly as the cost model `net_advantage ≈ Δ_save − ρ·Δ_recover` assumes.
- **Partial-critical-path nuance:** ~189 delayed fetches × 1000 ms = 189 s of injected delay, yet only
  +15 s net stall → the strict critical path threads only a *fraction* of recovery fetches; the rest
  pipeline off-path. The pass-through is ~14 %, not 100 %.

## Implications for the paper (subject to the approval gate — NOT yet written in)

1. **Sharpens §7.3 (contingent liability):** ρ·Δ_recover is real and deployment-measurable, but its
   materialisation has a sharp **operational boundary** — recovery must be on the consensus critical path.
   This is a *more precise, more falsifiable* claim than v3's "only under faults."
2. **Sharpens §7.4 (ρ–Δ_recover decomposition):** Δ_recover enters **linearly**; the super-additivity seen
   in the stress tests is driven by the **ρ (fault-intensity)** axis, not by Δ_recover non-linearity. The
   two axes are empirically separable.
3. **Construct-validity limits (unchanged, must restate):** single **uncertified** protocol (Sui/Mysticeti),
   **no certified arm**. This calibrates the *shape* of the recovery-side liability for an uncertified
   DAG-BFT; it is **not** the §7.2 certified-vs-uncertified net-advantage comparison, and Δ_recover here is
   an *injected* emulation knob, not a measured certified-protocol recovery cost.

## Artifacts (all reproducible)

- Harness: `scripts/phaseA_criticalpath_partition.ps1` (rotation, n=7),
  `scripts/phaseA_criticalpath_partition_n4.ps1` (rotation, n=4 cross-scale),
  `scripts/phaseA_recover_calibration.ps1` (single-node), `scripts/partition_pull_test.ps1` (mechanism
  proof, 46 hits). Compose env-knob injection added to both `compose.multivalidator.yaml` and
  `compose.multivalidator.n4.yaml` (backward-compatible: unset → 0 → stock).
- Data: `stage7_deployment/multivalidator/data/runs/phaseA_criticalpath_summary.csv` (n=7),
  `phaseA_criticalpath_n4_summary.csv` (n=4), `phaseA_calibration_summary.csv` (single-node),
  `phaseA_criticalpath_smoke_validation.csv`, `phaseA_criticalpath_n4_smoke_validation.csv`.
- Figure + plotter: `figures/phaseA_recover_calibration.png`, `scripts/plot_recover_calibration.py`.
- Launcher lesson: `powershell.exe -File … -ArrayParam @(…)` does NOT evaluate `@(…)`; the value leaks
  positionally onto the first param. Use the call operator `& $script -ArrayParam @(…)` or rely on defaults.
