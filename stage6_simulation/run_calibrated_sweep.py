"""
run_calibrated_sweep.py
=======================
Stage-7 → Stage-6 calibration replay (added 2026-05-25).

Reads a calibration patch JSON produced by
`stage7_deployment/multivalidator/tools/calibrate_stage6_from_real.py`,
maps each Docker scenario's measured RPC-latency distribution to a lognormal
(mean, sigma) network-delay parameterization for the SimPy simulator, and
re-runs the same sweep machinery (`experiments.sweep._measure_point`) at one
calibrated operating point per scenario.

Mapping decision (documented in the emitted report)
---------------------------------------------------
For each Docker scenario S, treat the measured `rpc_latency_ms_p50` and
`rpc_latency_ms_p95` as approximating the p50 / p95 of a lognormal
distribution and recover (mu, sigma) by:

    sigma_real = ln(p95 / p50) / 1.6448536      (z_{0.95} for a normal tail)
    mu_real    = ln(p50)
    E[X]       = exp(mu_real + sigma_real**2 / 2)

SimPy's `core.delay.DelayDistribution(kind="lognormal", params={"mean", "sigma"})`
internally converts `mean` to its underlying `mu` via `mu = ln(mean) - sigma**2/2`,
so passing `mean = E[X]` and `sigma = sigma_real` reproduces the calibrated
distribution.

Bridge limitation (also written into the report)
------------------------------------------------
- Docker `rpc_latency_ms_*` is the client-observed read-RPC latency against
  the fullnode. Stage-6 `delay.py` parameterizes inter-validator message
  delivery delay. These are physically distinct quantities; the calibration
  here is a first-order proxy, not a measurement-level identification.
- The stage6 sweep's "fixed mean = 1.0" assumption (`run_sweep.py`) is
  intentionally relaxed in this script: each Docker scenario gets its own
  time scale. As a result, **stage6 outputs across scenarios in this replay
  are not on a common time axis**; only within-scenario comparisons against
  Docker observations are meaningful.

Usage
-----
    cd stage6_simulation
    python run_calibrated_sweep.py \
        --patch ../stage7_deployment/multivalidator/data/calibration_patch_20260525.json \
        --output-dir ../stage7_deployment/multivalidator/data \
        --report ../stage7_deployment/multivalidator/reports/sweep_calibrated_replay_20260525.md
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from core import SimConfig
from experiments.sweep import _measure_point, DATA_KIND

Z_95 = 1.6448536269514722

DOCKER_SCENARIOS = [
    "baseline",
    "delay_low",
    "delay_high",
    "loss_low",
    "crash_one_validator",
    "two_validator_pressure",
]


def load_patch(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def index_patch(patch: dict) -> dict:
    """Group patch parameters by scenario into a {scenario: {field: value}} map."""
    out = defaultdict(dict)
    for item in patch["parameters"]:
        scenario, _, field = item["parameter"].partition(".")
        out[scenario][field] = item["after"]
    return dict(out)


def lognormal_params_from_p50_p95(p50: float, p95: float) -> tuple[float, float, float]:
    """Recover (mu, sigma, E[X]) from p50 and p95 under a lognormal assumption.

    Returns:
        mu: underlying normal location
        sigma: underlying normal scale (== SimPy `sigma`)
        mean_E_X: E[X] (== SimPy `mean`)
    """
    if p50 <= 0 or p95 <= 0 or p95 < p50:
        raise ValueError(f"invalid p50={p50}, p95={p95}")
    sigma = math.log(p95 / p50) / Z_95
    mu = math.log(p50)
    mean_E_X = math.exp(mu + sigma * sigma / 2.0)
    return mu, sigma, mean_E_X


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--patch", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="Directory for csv/json outputs (mirrors stage6 export style)")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--n-rounds", type=int, default=1000)
    parser.add_argument("--n-trials", type=int, default=4)
    parser.add_argument("--n", type=int, default=7, help="validator count (matches Docker N=7)")
    parser.add_argument("--f", type=int, default=2, help="fault tolerance (matches Docker f=2)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    patch = load_patch(args.patch)
    scenarios = index_patch(patch)

    base = SimConfig(n=args.n, f=args.f, n_rounds=args.n_rounds, seed=0)
    print("=" * 66)
    print("Calibrated replay: Stage-6 SimPy driven by Stage-7 Docker measurements")
    print("=" * 66)
    print(f"Base: n={base.n} f={base.f} rounds={base.n_rounds} n_trials={args.n_trials}")
    print(f"Patch: {args.patch}")
    print(f"Source: {patch.get('source')}")
    print("-" * 66)

    rows = []
    for scenario in DOCKER_SCENARIOS:
        fields = scenarios.get(scenario, {})
        p50 = fields.get("rpc_latency_ms_p50")
        p95 = fields.get("rpc_latency_ms_p95")
        if p50 is None or p95 is None or p95 <= p50:
            print(f"  SKIP {scenario}: p50={p50} p95={p95} (cannot derive lognormal)")
            rows.append({
                "scenario": scenario,
                "rpc_p50_ms": p50, "rpc_p95_ms": p95,
                "mapped_sigma": None, "mapped_mean": None,
                "n_trials": 0, "rho": None, "delta_recover": None,
                "delta_save": None, "net_adv": None,
                "unc_round_latency": None, "cer_round_latency": None,
                "recon_triggers": None, "all_passed": None,
                "skipped_reason": "missing or non-monotone p50/p95",
            })
            continue
        mu, sigma, mean_E_X = lognormal_params_from_p50_p95(p50, p95)
        print(f"  {scenario}: p50={p50} p95={p95}  →  sigma={sigma:.4f} mean(E[X])={mean_E_X:.4f}")

        point = _measure_point(sigma=sigma, mean=mean_E_X, base=base, n_trials=args.n_trials)
        rows.append({
            "scenario": scenario,
            "rpc_p50_ms": p50, "rpc_p95_ms": p95,
            "mapped_sigma": sigma, "mapped_mean": mean_E_X,
            "n_trials": point.n_trials,
            "rho": point.rho, "rho_std": point.rho_std,
            "delta_recover": point.delta_recover, "delta_recover_std": point.delta_recover_std,
            "delta_save": point.delta_save, "delta_save_std": point.delta_save_std,
            "net_adv": point.net_adv, "net_adv_std": point.net_adv_std,
            "unc_round_latency": point.unc_round_latency,
            "cer_round_latency": point.cer_round_latency,
            "recon_triggers": point.recon_triggers,
            "all_passed": point.all_passed,
            "data_kind": DATA_KIND,
        })

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    csv_path  = args.output_dir / f"sweep_calibrated_{ts}.csv"
    json_path = args.output_dir / f"sweep_calibrated_{ts}.json"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        all_keys = sorted({k for r in rows for k in r.keys()})
        writer = csv.DictWriter(fh, fieldnames=all_keys)
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "patch": str(args.patch),
        "base": {"n": base.n, "f": base.f, "n_rounds": base.n_rounds, "n_trials": args.n_trials},
        "mapping": {
            "method": "lognormal_from_p50_p95",
            "formula": "sigma = ln(p95/p50)/z_{0.95}; mean = p50 * exp(sigma**2/2); z_{0.95}=1.6448536",
        },
        "rows": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    write_report(rows, base, args, patch, ts, csv_path, json_path)
    print("-" * 66)
    print(f"csv    -> {csv_path}")
    print(f"json   -> {json_path}")
    print(f"report -> {args.report}")
    return 0


def write_report(rows, base, args, patch, ts, csv_path, json_path):
    lines = [
        "# Stage 6 Calibrated Replay (driven by Stage 7 Docker measurements)",
        "",
        f"- Generated (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Patch source: `{args.patch}` ({patch.get('source')})",
        f"- Replay base: n={base.n}, f={base.f}, rounds={base.n_rounds}, n_trials={args.n_trials} per scenario",
        f"- Raw data: `{csv_path.name}`, `{json_path.name}` (same directory as patch)",
        "",
        "## Mapping (engineering → protocol)",
        "",
        "For each Docker scenario S, treat measured `rpc_latency_ms_p50` / `rpc_latency_ms_p95` as the p50 / p95 of a lognormal:",
        "",
        "```",
        "sigma = ln(p95 / p50) / z_{0.95},     z_{0.95} = 1.6448536",
        "mean  = p50 * exp(sigma**2 / 2)        (= E[X] of the lognormal)",
        "```",
        "",
        "These are then passed to `core.delay.DelayDistribution(kind='lognormal', mean, sigma)`. The SimPy delay layer converts back to underlying `mu` internally.",
        "",
        "## Bridge limitations",
        "",
        "- Docker `rpc_latency_ms_*` is **client-observed read-RPC latency against the fullnode**, not the **inter-validator message-delivery delay** modeled by `core/delay.py`. The calibration here is a first-order proxy; it does NOT identify the simulator's delay parameters with measured quantities at the physical layer.",
        "- This replay intentionally relaxes the stage6 convention of fixed `mean=1.0`. Each scenario gets its own time scale (`mean` ∝ measured p50). As a result, **across scenarios the absolute values of net_adv / Δ_recover / Δ_save in this table are NOT on a common time axis** and must not be compared directly. Within-scenario comparison against Docker observations is what this replay supports.",
        "- `recovery_time_ms` (only meaningful for `crash_one_validator`) is reported by Docker in milliseconds of wall-clock pause-to-recovery; SimPy `Δ_recover` is per-event reconciliation latency in abstract delay units. The two are not on the same dimension and are reported side-by-side for context only.",
        "",
        "## Per-scenario replay",
        "",
        "| scenario | rpc_p50(ms) | rpc_p95(ms) | mapped σ | mapped mean | ρ | Δ_recover | Δ_save | net_adv | recon_triggers | passed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for r in rows:
        def f(v, prec=4):
            if v is None:
                return "n/a"
            if isinstance(v, float):
                return f"{v:.{prec}f}"
            return str(v)
        passed = "✓" if r.get("all_passed") else ("✗" if r.get("all_passed") is False else "—")
        lines.append(
            f"| {r['scenario']} | {f(r['rpc_p50_ms'],0)} | {f(r['rpc_p95_ms'],0)} | "
            f"{f(r['mapped_sigma'],4)} | {f(r['mapped_mean'],4)} | "
            f"{f(r.get('rho'),4)} | {f(r.get('delta_recover'),4)} | {f(r.get('delta_save'),4)} | "
            f"{f(r.get('net_adv'),4)} | {f(r.get('recon_triggers'),1)} | {passed} |"
        )
    lines.append("")
    lines.append("## Side-by-side: Docker measurement vs SimPy replay")
    lines.append("")
    lines.append("This table is *not* an apples-to-apples error metric (different physical dimensions per the bridge note above); it is a co-location of what each layer reports under the same labeled scenario.")
    lines.append("")
    lines.append("| scenario | Docker rpc_p50/p95 (ms) | Docker recovery (ms) | Docker availability | SimPy ρ | SimPy Δ_recover | SimPy net_adv |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in rows:
        def f(v, prec=4):
            if v is None: return "n/a"
            if isinstance(v, float): return f"{v:.{prec}f}"
            return str(v)
        # pull docker recovery/availability from patch
        scen = r["scenario"]
        sd = {it["parameter"]: it["after"] for it in patch["parameters"]
              if it["parameter"].startswith(scen + ".")}
        rec = sd.get(f"{scen}.recovery_time_ms")
        avl = sd.get(f"{scen}.availability_ratio")
        lines.append(
            f"| {scen} | {f(r['rpc_p50_ms'],0)} / {f(r['rpc_p95_ms'],0)} | "
            f"{f(rec,0)} | {f(avl,3)} | "
            f"{f(r.get('rho'),4)} | {f(r.get('delta_recover'),4)} | {f(r.get('net_adv'),4)} |"
        )
    lines.append("")
    lines.append("## Reading guide")
    lines.append("")
    lines.append("- All SimPy quantities (ρ, Δ_recover, Δ_save, net_adv, recon_triggers) are *simulation results from an analytical-model controlled numerical experiment* (per stage6 §4.6 measurement convention); they are NOT real protocol measurements. The `data_kind` field in the CSV/JSON carries this label.")
    lines.append("- The Docker columns are real engineering measurements from 7-validator container deployments (`recovery_time_ms` only for crash_one_validator; `availability` was 1.0 across all 60 runs).")
    lines.append("- Use this table to argue: \"under each Docker-measured RPC-latency envelope mapped into the simulator, the SimPy model predicts X for protocol-level quantities Y\" — not to argue \"simulator matches reality.\"")

    args.report.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
