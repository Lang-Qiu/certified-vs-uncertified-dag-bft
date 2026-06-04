# Phase 1 results — Route A1 certified arm validated on real Sui/Mysticeti (n=7)

**Date:** 2026-05-31 · **Image:** `stage9-sui-certgate:local` (rebuilt with the certificate-gate, id
`afe825da667f`) · **Knobs:** `SUI_CONSENSUS_CERTIFICATE_GATE` (gate on/off) +
`SUI_CONSENSUS_CERTIFICATE_PROBER_INTERVAL_MS` (fast independent ack channel) · **Δ_recover held at 0.**

## Headline — the faithful certificate-gate works in deployment

Fault-free n=7, both arms on the same fast prober (75 ms), steady-state checkpoint cadence over 90 s:

| arm | cert_gate | cadence (ckpt/s) | mean latency (ms/ckpt) | status |
|---|---|---:|---:|---|
| OFF | 0 | **4.633** | 215.8 | ok |
| ON  | 1 | **3.144** | 318.0 | ok |

- **Δ_save > 0 (real):** cert ON is **−32.1 %** cadence (≈ **+102 ms / commit**). The gate forces a
  parent-round ancestor to wait for a 2f+1 stake quorum to *independently* (probe-channel) accept it
  before it can be referenced — a genuine certification round, paid in latency. This is the §7.2
  Δ_save, measured on real deployment for the first time.
- **Liveness holds — no deadlock:** ON cadence is 68 % of OFF, a *healthy* rate. The circular
  dependency that deadlocks a naive reference-gate (PHASE0_SPIKE §8.2) is broken because the
  certificate comes from the RoundProber (`get_latest_rounds`), which observes block *delivery*, not
  future-round references. Validated end-to-end, not just in the type system.
- **Both arms `ok`** (warmup cleared, RPC reads clean).

## Why this is faithful (and its honest limit)

Unlike an injected sleep, the cost here flows through a **real independent network channel** doing
**real 2f+1 stake aggregation** over **real block-acceptance reports** — the availability-enforcement
semantics the paper cares about. At a fixed prober interval the Δ_save is the genuine latency of that
confirmation round. **Honest limit (must restate in any backfill, gated):** it is an *availability*
certificate (2f+1 accepted), not a cryptographic 2f+1 signature aggregation, and the magnitude is
tuned via the certification-channel latency (prober interval) rather than being a specific real
protocol's RBC cost. Same epistemic status as the §7.6.2 Δ_recover knob.

## Δ_save magnitude knob

`certificate_prober_interval_ms` doubles as the Δ_save knob: a block is referenceable only after the
prober confirms quorum-acceptance, so certification latency ≈ up to one prober interval. Sweeping it
(next: 75/150/300/500 ms) yields a Δ_save dose-response — directly parallel to the §7.6.2 Δ_recover
calibration, on the same binary. → enables the joint §7.2 test `net_advantage ≈ Δ_save − ρ·Δ_recover`.

## Artifacts

- Harness: `scripts/phase1_certgate_pilot.ps1` (fault-free A/B); calibration sweep next.
- Data: `stage7_deployment/multivalidator/data/runs/phase1_certgate_pilot_summary.csv`.
- Code (against `62ee6ada`, all behind `certificate_gate`, OFF ≡ byte-identical stock):
  `parameters.rs` (knobs), `round_tracker.rs::compute_probed_accepted_quorum_rounds` (probe-only
  certificate), `round_prober.rs` (effective interval), `proposer.rs::smart_ancestors_to_propose`
  (the gate). Unit + regression tests green (6 passed). Design: `PHASE0_ROUTE_A1_DESIGN.md`.

## Phase 1b — prober-interval sweep (2026-05-31, n=7, 2 reps each, `phase1b_dsave_calibration_summary.csv`)

Means over 2 reps (cadence in ckpt/s; latency = 1/cadence):

| prober I (ms) | OFF cadence | ON cadence | lat_OFF | lat_ON | Δ_save (ms/commit) | cadence drop |
|---:|---:|---:|---:|---:|---:|---:|
| 75  | 4.583 | 2.989 | 218.2 | 334.6 | **+116.4** | 34.8 % |
| 250 | 4.589 | 3.939 | 217.9 | 253.9 | +36.0 | 14.2 % |
| 500 | 4.572 | 4.650 | 218.7 | 215.1 | −3.6 (≈0) | ~0 % |

**OFF is rock-stable (~4.58 ckpt/s) across all intervals** → prober overhead on OFF negligible; OFF ≈ stock
baseline confirmed. Both reps agree tightly (ON@75: 3.17/2.81; ON@250: 3.94/3.93; ON@500: 4.66/4.64).

### Interpretation — the prober interval is a GATE-FIDELITY knob, not a Δ_save magnitude knob

Δ_save is **maximal at the fastest prober** and decays to ~0 as the prober slows — inverse of the naive
"slower channel → more latency" guess. Mechanism: the gate excludes a parent-round ancestor until the
**probe-only** certificate (`compute_probed_accepted_quorum_rounds`, refreshed every I) shows a quorum
accepted it.
- **Fast prober (75 ms):** the probe-certificate tracks the latest round closely; the proposer waits a
  short, real certification interval on the *smart* path → genuine Δ_save (≈116 ms ≈ ½ commit interval =
  one quorum-acceptance round).
- **Slow prober (500 ms):** the probe-certificate lags the latest round by ~(round_rate × I); the
  proposer can't find certified parents → leader-timeout → **force-propose → gate bypassed** (the
  `&& smart_select` liveness escape hatch) → cadence reverts to stock.

→ There is essentially **one faithful Δ_save (~116 ms)**, realized only when the ack channel is fast
enough to bind on the smart path. Slowing the channel disengages the gate rather than raising the cost.
**Caveat to verify:** confirm the fast-prober (75 ms) regime is NOT itself partly force-bypassed (which
would mean even 116 ms understates the faithful Δ_save). Needs a force-proposal / smart-wait log count.

## Next

1. **Verify the mechanism**: instrument/grep force-proposal & smart-select-wait rates at 75 vs 500 ms to
   confirm "slow prober → force bypass" and that 75 ms is a clean (low-force) faithful regime.
2. Confirm OFF ≡ stock vs stage7-sui:local baseline cadence (OFF here ≈4.58 stable — looks equivalent).
3. (Bigger, EXPERIMENT_PLAN) joint net-advantage: with Δ_save≈116 ms fixed + Δ_recover knob, sweep ρ
   (fault frequency) → ρ* crossover of `net_advantage ≈ Δ_save − ρ·Δ_recover`, H1–H4.
4. (Gated) backfill §7.2/§7.6/§9/§10 only after the approval gate.
