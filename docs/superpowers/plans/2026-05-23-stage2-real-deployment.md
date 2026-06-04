# Stage 2 Real Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible local real-protocol deployment harness that runs a DAG-BFT implementation, injects controlled delay/failure, extracts measured latency/cost anchors, and compares those anchors against `stage6_simulation/` without editing the paper.

**Architecture:** Stage 2 is an experimental harness, not a protocol rewrite. Keep the upstream consensus repository outside the paper pipeline, wrap it with Docker Compose and measurement scripts under `stage7_deployment/`, then export raw data, figures, and a findings summary that can later be reviewed for paper integration. Use MystenLabs `sui` as the primary target because current Narwhal development moved there; keep archived `MystenLabs/narwhal` as a fallback/legacy benchmark target only if the Sui path cannot be built locally.

**Tech Stack:** Docker Compose, Rust/Cargo, Tokio/tracing, Linux `tc netem`, PowerShell helper scripts for this Windows workspace, Python 3.9+ for log parsing and calibration, existing `stage6_simulation/` outputs for simulation comparison.

---

## Guardrails

- Do not modify `final/final_paper.md`.
- Do not create revision drafts under `stage8_paper_integration/`.
- Do not vendor large upstream repositories into this project. Clone external protocol code under `stage7_deployment/external/`, and keep that path ignored.
- Preserve all raw measurements under `stage7_deployment/data/` with manifest entries before deriving summaries.
- Label every output as `"real-deployment"` and distinguish it from Stage 1 `"simulation"`.
- Treat real deployment measurements as mixed protocol effects. They calibrate Stage 1 and provide protocol-layer corroboration; they do not isolate the certification variable by themselves.

## External Sources Checked On 2026-05-23

- `https://github.com/MystenLabs/sui` is the primary live Sui repository and is Rust-based.
- `https://github.com/MystenLabs/narwhal` is archived and states that Narwhal development moved to `MystenLabs/sui/tree/main/narwhal`.
- Sui local-network docs mention `sui-test-validator`, default fullnode RPC port `9000`, faucet port `9123`, and `cargo run --bin sui-test-validator`.
- Sui's CLI cheat sheet lists `sui genesis`, `sui start`, and local network commands.
- Mysticeti paper material references an orchestrator-based benchmark flow, but this plan starts with a local Docker harness to avoid cloud cost and to satisfy the local reproducibility requirement.

## File Structure

- Create: `stage7_deployment/README.md` - operator-facing overview, prerequisites, and honest-boundary statement.
- Create: `stage7_deployment/.gitignore` - excludes upstream clones, build caches, and bulky local logs.
- Create: `stage7_deployment/targets/target_repos.md` - target repository feasibility matrix and selected path.
- Create: `stage7_deployment/compose/compose.yaml` - local experiment stack skeleton.
- Create: `stage7_deployment/compose/.env.example` - configurable committee size, image tags, ports, and experiment labels.
- Create: `stage7_deployment/docker/sui/Dockerfile` - source-build image for Sui tools.
- Create: `stage7_deployment/scripts/check_prereqs.ps1` - validates Docker, Git, Python, Cargo/Rust, and Linux container support.
- Create: `stage7_deployment/scripts/fetch_targets.ps1` - clones or updates upstream targets outside tracked source.
- Create: `stage7_deployment/scripts/build_sui_image.ps1` - builds the local Sui Docker image.
- Create: `stage7_deployment/scripts/run_local_testnet.ps1` - starts the local experiment stack.
- Create: `stage7_deployment/scripts/inject_netem.sh` - applies Linux `tc netem` delay/loss to containers.
- Create: `stage7_deployment/scripts/kill_validator.ps1` - stops one validator/container to simulate a fault.
- Create: `stage7_deployment/tools/collect_logs.py` - collects JSONL records from container logs.
- Create: `stage7_deployment/tools/extract_latency.py` - derives latency distribution and recovery-cost measurements.
- Create: `stage7_deployment/tools/calibrate_stage6.py` - produces Stage 1 vs Stage 2 comparison records.
- Create: `stage7_deployment/tools/register_artifacts.py` - records baseline artifacts in the manifest and retention list.
- Create: `stage7_deployment/data/manifest.json` - append-only inventory for raw data, derived data, figures, and reports.
- Create: `stage7_deployment/data/留存清单.md` - human-readable retention list matching the root implementation plan.
- Create: `stage7_deployment/reports/phase2_findings_summary.md` - Stage 2 findings package for later approval.
- Create: `stage7_deployment/figures/README.md` - figure conventions and output index.

---

### Task 0: Install Stage 2 Skills And Verify Tooling

**Files:**
- Create: `stage7_deployment/README.md`
- Create: `stage7_deployment/.gitignore`
- Create: `stage7_deployment/scripts/check_prereqs.ps1`

- [ ] **Step 1: Install the Docker Compose orchestration skill**

Run:

```powershell
npx skills add https://github.com/manutej/luxor-claude-marketplace --skill docker-compose-orchestration
```

Expected: the skills CLI reports that `docker-compose-orchestration` was installed.

- [ ] **Step 2: Install the Rust async patterns skill**

Run:

```powershell
npx skills add https://github.com/wshobson/agents --skill rust-async-patterns
```

Expected: the skills CLI reports that `rust-async-patterns` was installed.

- [ ] **Step 3: Create the Stage 2 README**

Create `stage7_deployment/README.md`:

```markdown
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

## Retention

Every experiment must write raw output under `data/raw/`, derived output under `data/derived/`, figures under `figures/`, and a manifest entry in `data/manifest.json`.
```

- [ ] **Step 4: Create the Stage 2 ignore file**

Create `stage7_deployment/.gitignore`:

```gitignore
external/
.cargo-cache/
.rustup-cache/
data/raw/
data/tmp/
*.log
*.sqlite
*.db
target/
```

- [ ] **Step 5: Create the prerequisite checker**

Create `stage7_deployment/scripts/check_prereqs.ps1`:

```powershell
$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        throw "Missing required command: $Name"
    }
    Write-Host "ok: $Name -> $($cmd.Source)"
}

Require-Command "docker"
Require-Command "git"
Require-Command "python"

$dockerVersion = docker version --format "{{.Server.Version}}"
Write-Host "ok: docker server $dockerVersion"

$composeVersion = docker compose version
Write-Host "ok: $composeVersion"

$dockerInfo = docker info --format "{{.OSType}}"
if ($dockerInfo -ne "linux") {
    throw "Docker must be using Linux containers; observed OSType=$dockerInfo"
}
Write-Host "ok: Docker Linux containers enabled"

$pythonVersion = python --version
Write-Host "ok: $pythonVersion"

$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if ($cargo) {
    Write-Host "ok: cargo -> $($cargo.Source)"
} else {
    Write-Host "warn: cargo not found; Docker build can still compile Sui, but local Rust inspection will be limited"
}
```

- [ ] **Step 6: Run the prerequisite checker**

Run:

```powershell
.\stage7_deployment\scripts\check_prereqs.ps1
```

Expected: `ok:` lines for Docker, Git, Python, Docker Compose, and Linux containers. Cargo may be `ok:` or `warn:`.

---

### Task 1: Target Repository Feasibility Assessment

**Files:**
- Create: `stage7_deployment/targets/target_repos.md`
- Create: `stage7_deployment/scripts/fetch_targets.ps1`

- [ ] **Step 1: Create the target repository assessment document**

Create `stage7_deployment/targets/target_repos.md`:

```markdown
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
- Build path: Docker image from source, then run either `sui-test-validator` for smoke testing or a multi-node benchmark/orchestrator path if present in the checked-out commit.
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
2. Record the exact commit SHA.
3. Check whether the checkout exposes local multi-node or orchestrator commands.
4. If only `sui-test-validator` is locally feasible, use it as a smoke target and document the limitation.
5. If a multi-validator local benchmark is feasible, make it the main experiment target.
```

- [ ] **Step 2: Create the target fetch script**

Create `stage7_deployment/scripts/fetch_targets.ps1`:

```powershell
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$external = Join-Path $root "external"
$suiDir = Join-Path $external "sui"
$narwhalDir = Join-Path $external "narwhal"

New-Item -ItemType Directory -Force -Path $external | Out-Null

function Sync-Repo {
    param(
        [string]$Url,
        [string]$Path,
        [string]$Name
    )
    if (Test-Path $Path) {
        Write-Host "Updating $Name at $Path"
        git -C $Path fetch --depth 1 origin
        git -C $Path checkout FETCH_HEAD
    } else {
        Write-Host "Cloning $Name into $Path"
        git clone --depth 1 $Url $Path
    }
    $sha = git -C $Path rev-parse HEAD
    Write-Host "$Name commit: $sha"
}

Sync-Repo -Url "https://github.com/MystenLabs/sui.git" -Path $suiDir -Name "sui"

Write-Host "Narwhal is archived; clone it only when explicitly requested:"
Write-Host "git clone --depth 1 https://github.com/MystenLabs/narwhal.git $narwhalDir"
```

- [ ] **Step 3: Fetch the primary target**

Run:

```powershell
.\stage7_deployment\scripts\fetch_targets.ps1
```

Expected: `stage7_deployment/external/sui` exists and the script prints a Sui commit SHA.

- [ ] **Step 4: Inspect local build and benchmark entrypoints**

Run:

```powershell
Get-ChildItem -LiteralPath .\stage7_deployment\external\sui -Recurse -Depth 3 |
  Where-Object { $_.Name -match 'orchestrator|benchmark|validator|consensus|narwhal|mysticeti' } |
  Select-Object FullName |
  Out-File -Encoding utf8 .\stage7_deployment\data\tmp\sui_entrypoints.txt
```

Expected: `data/tmp/sui_entrypoints.txt` lists candidate paths. If `data/tmp/` does not exist, create it with:

```powershell
New-Item -ItemType Directory -Force -Path .\stage7_deployment\data\tmp
```

- [ ] **Step 5: Update the assessment with observed entrypoints**

Run:

```powershell
$sha = git -C .\stage7_deployment\external\sui rev-parse HEAD
@"

## Local Inspection Result

- Date: 2026-05-23
- Sui commit: $sha
- Candidate entrypoint list: `stage7_deployment/data/tmp/sui_entrypoints.txt`
- First executable target: `sui-test-validator` for smoke test; multi-node target selected after inspecting orchestrator/benchmark availability.
"@ | Add-Content -Encoding utf8 .\stage7_deployment\targets\target_repos.md
```

Expected: the target assessment includes the exact Sui commit SHA from the local checkout.

---

### Task 2: Docker Image And Compose Skeleton

**Files:**
- Create: `stage7_deployment/docker/sui/Dockerfile`
- Create: `stage7_deployment/compose/.env.example`
- Create: `stage7_deployment/compose/compose.yaml`
- Create: `stage7_deployment/scripts/build_sui_image.ps1`

- [ ] **Step 1: Create the Sui source-build Dockerfile**

Create `stage7_deployment/docker/sui/Dockerfile`:

```dockerfile
FROM rust:1-bookworm AS builder

ARG SUI_REF=main
WORKDIR /src

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    clang \
    cmake \
    git \
    libssl-dev \
    llvm \
    pkg-config \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch ${SUI_REF} https://github.com/MystenLabs/sui.git /src/sui
WORKDIR /src/sui

RUN cargo build --release --bin sui --bin sui-test-validator

FROM debian:bookworm-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    iproute2 \
    jq \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /src/sui/target/release/sui /usr/local/bin/sui
COPY --from=builder /src/sui/target/release/sui-test-validator /usr/local/bin/sui-test-validator

WORKDIR /work
EXPOSE 9000 9123

CMD ["sui-test-validator", "--fullnode-rpc-port", "9000", "--faucet-port", "9123"]
```

- [ ] **Step 2: Create the Compose environment example**

Create `stage7_deployment/compose/.env.example`:

```dotenv
COMPOSE_PROJECT_NAME=stage7-sui
SUI_REF=main
SUI_IMAGE=stage7-sui:local
FULLNODE_RPC_PORT=9000
FAUCET_PORT=9123
EXPERIMENT_LABEL=baseline_local_validator
NETEM_DELAY_MS=0
NETEM_JITTER_MS=0
NETEM_LOSS_PCT=0
```

- [ ] **Step 3: Create the initial Compose stack**

Create `stage7_deployment/compose/compose.yaml`:

```yaml
services:
  sui-local:
    image: ${SUI_IMAGE:-stage7-sui:local}
    build:
      context: ..
      dockerfile: docker/sui/Dockerfile
      args:
        SUI_REF: ${SUI_REF:-main}
    container_name: stage7-sui-local
    cap_add:
      - NET_ADMIN
    environment:
      RUST_LOG: "off,sui_node=info,consensus=info"
      EXPERIMENT_LABEL: ${EXPERIMENT_LABEL:-baseline_local_validator}
    ports:
      - "${FULLNODE_RPC_PORT:-9000}:9000"
      - "${FAUCET_PORT:-9123}:9123"
    volumes:
      - ../data/raw:/work/data/raw
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://127.0.0.1:9000 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 30s
```

- [ ] **Step 4: Create the image build script**

Create `stage7_deployment/scripts/build_sui_image.ps1`:

```powershell
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$composeDir = Join-Path $root "compose"
$envFile = Join-Path $composeDir ".env"
$envExample = Join-Path $composeDir ".env.example"

if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "Created $envFile from .env.example"
}

docker compose --env-file $envFile -f (Join-Path $composeDir "compose.yaml") build sui-local
```

- [ ] **Step 5: Build the image**

Run:

```powershell
.\stage7_deployment\scripts\build_sui_image.ps1
```

Expected: Docker builds image `stage7-sui:local`. If compilation fails because upstream requires a pinned Rust toolchain, inspect `stage7_deployment/external/sui/rust-toolchain.toml` or `rust-toolchain` and update the Dockerfile base image in the next step before continuing.

---

### Task 3: Baseline Local Testnet Smoke Run

**Files:**
- Create: `stage7_deployment/scripts/run_local_testnet.ps1`
- Create: `stage7_deployment/tools/collect_logs.py`
- Modify: `stage7_deployment/data/manifest.json`
- Modify: `stage7_deployment/data/留存清单.md`

- [ ] **Step 1: Create the runner script**

Create `stage7_deployment/scripts/run_local_testnet.ps1`:

```powershell
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$composeDir = Join-Path $root "compose"
$envFile = Join-Path $composeDir ".env"
$rawDir = Join-Path $root "data/raw"

New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $composeDir ".env.example") $envFile
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $rawDir "baseline_$stamp.log"

docker compose --env-file $envFile -f (Join-Path $composeDir "compose.yaml") up -d sui-local
Start-Sleep -Seconds 45
docker logs stage7-sui-local --since 1h | Tee-Object -FilePath $logFile

Write-Host "baseline log: $logFile"
Write-Host "RPC smoke check:"
curl.exe --location --request POST "http://127.0.0.1:9000" --header "Content-Type: application/json" --data "{`"jsonrpc`":`"2.0`",`"id`":1,`"method`":`"sui_getTotalTransactionBlocks`",`"params`":[]}"
```

- [ ] **Step 2: Create the log collector**

Create `stage7_deployment/tools/collect_logs.py`:

```python
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def iter_lines(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            text = line.rstrip("\n")
            if text:
                yield line_no, text


def classify_line(text: str) -> str:
    lowered = text.lower()
    if "consensus" in lowered:
        return "consensus"
    if "checkpoint" in lowered:
        return "checkpoint"
    if "transaction" in lowered or "tx" in lowered:
        return "transaction"
    if "error" in lowered or "warn" in lowered:
        return "warning_or_error"
    return "other"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--experiment-label", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    with output_path.open("w", encoding="utf-8") as out:
        for line_no, text in iter_lines(input_path):
            record = {
                "source": "real-deployment",
                "experiment_label": args.experiment_label,
                "captured_at": now,
                "input_file": str(input_path),
                "line_no": line_no,
                "kind": classify_line(text),
                "message": text,
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Initialize the manifest**

Create `stage7_deployment/data/manifest.json`:

```json
{
  "schema_version": 1,
  "stage": "stage7_deployment",
  "entries": []
}
```

- [ ] **Step 4: Initialize the human retention list**

Create `stage7_deployment/data/留存清单.md`:

```markdown
# 阶段二真实部署留存清单

| 时间 | 类型 | 文件 | 实验标签 | 论文映射 | 说明 |
|---|---|---|---|---|---|
```

- [ ] **Step 5: Run the baseline smoke test**

Run:

```powershell
.\stage7_deployment\scripts\run_local_testnet.ps1
```

Expected: container `stage7-sui-local` starts, a raw log file appears under `stage7_deployment/data/raw/`, and the RPC smoke check returns a JSON-RPC response.

- [ ] **Step 6: Convert the raw log to JSONL**

Run:

```powershell
$latest = Get-ChildItem .\stage7_deployment\data\raw\baseline_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1
python .\stage7_deployment\tools\collect_logs.py --input $latest.FullName --output .\stage7_deployment\data\derived\baseline_events.jsonl --experiment-label baseline_local_validator
```

Expected: `stage7_deployment/data/derived/baseline_events.jsonl` exists and contains JSON records with `"source": "real-deployment"`.

---

### Task 4: Fault And Network Delay Injection

**Files:**
- Create: `stage7_deployment/scripts/inject_netem.sh`
- Create: `stage7_deployment/scripts/kill_validator.ps1`
- Modify: `stage7_deployment/README.md`

- [ ] **Step 1: Create the netem injection script**

Create `stage7_deployment/scripts/inject_netem.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

IFACE="${IFACE:-eth0}"
DELAY_MS="${NETEM_DELAY_MS:-0}"
JITTER_MS="${NETEM_JITTER_MS:-0}"
LOSS_PCT="${NETEM_LOSS_PCT:-0}"

tc qdisc del dev "$IFACE" root 2>/dev/null || true

if [[ "$DELAY_MS" == "0" && "$JITTER_MS" == "0" && "$LOSS_PCT" == "0" ]]; then
  echo "netem cleared on $IFACE"
  exit 0
fi

tc qdisc add dev "$IFACE" root netem delay "${DELAY_MS}ms" "${JITTER_MS}ms" loss "${LOSS_PCT}%"
tc qdisc show dev "$IFACE"
```

- [ ] **Step 2: Apply netem to the running container**

Run:

```powershell
docker cp .\stage7_deployment\scripts\inject_netem.sh stage7-sui-local:/usr/local/bin/inject_netem.sh
docker exec -e NETEM_DELAY_MS=100 -e NETEM_JITTER_MS=20 -e NETEM_LOSS_PCT=0 stage7-sui-local bash /usr/local/bin/inject_netem.sh
```

Expected: `tc qdisc show` reports a `netem delay 100ms 20ms` rule.

- [ ] **Step 3: Create the validator kill script**

Create `stage7_deployment/scripts/kill_validator.ps1`:

```powershell
$ErrorActionPreference = "Stop"

param(
    [string]$ContainerName = "stage7-sui-local",
    [int]$DownSeconds = 15
)

Write-Host "Stopping $ContainerName for $DownSeconds seconds"
docker stop $ContainerName | Out-Host
Start-Sleep -Seconds $DownSeconds
Write-Host "Restarting $ContainerName"
docker start $ContainerName | Out-Host
```

- [ ] **Step 4: Run a fault-injection smoke test**

Run:

```powershell
.\stage7_deployment\scripts\kill_validator.ps1 -ContainerName stage7-sui-local -DownSeconds 15
docker logs stage7-sui-local --since 5m > .\stage7_deployment\data\raw\fault_restart_smoke.log
```

Expected: `fault_restart_smoke.log` exists and contains restart-period logs. In the single-validator smoke target, this is a process recovery test; once a multi-validator target exists, the same script will stop one validator container.

- [ ] **Step 5: Document fault-injection limits**

Append to `stage7_deployment/README.md`:

```markdown
## Fault Injection Notes

The first smoke target may use `sui-test-validator`, which packages a local validator/fullnode/faucet path. Fault injection on that target validates recovery and log capture only. Multi-validator conclusions require a later Compose profile with separate validator containers.
```

---

### Task 5: Latency Extraction And Stage 1 Calibration

**Files:**
- Create: `stage7_deployment/tools/extract_latency.py`
- Create: `stage7_deployment/tools/calibrate_stage6.py`
- Create: `stage7_deployment/figures/README.md`

- [ ] **Step 1: Create the latency extraction script**

Create `stage7_deployment/tools/extract_latency.py`:

```python
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def load_events(path: Path) -> list[dict]:
    events: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                events.append(json.loads(line))
    return events


def summarize(events: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for event in events:
        kind = event.get("kind", "unknown")
        counts[kind] = counts.get(kind, 0) + 1

    # Until precise upstream timestamps are instrumented, this summary is a log-surface
    # coverage check. Later tasks replace this with commit/checkpoint duration parsing.
    return {
        "source": "real-deployment",
        "event_count": len(events),
        "kind_counts": counts,
        "observed_consensus_events": counts.get("consensus", 0),
        "observed_checkpoint_events": counts.get("checkpoint", 0),
        "observed_transaction_events": counts.get("transaction", 0),
        "latency_ms": {
            "samples": [],
            "mean": None,
            "median": None,
            "p95": None
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    events = load_events(Path(args.events))
    result = summarize(events)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Create the calibration script**

Create `stage7_deployment/tools/calibrate_stage6.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage2-summary", required=True)
    parser.add_argument("--stage6-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    stage2 = read_json(Path(args.stage2_summary))
    stage6_manifest = read_json(Path(args.stage6_manifest))

    comparison = {
        "source": "stage1-stage2-calibration",
        "stage2_summary": args.stage2_summary,
        "stage6_manifest": args.stage6_manifest,
        "paper_mapping": "§7.1-§7.2 cost ledger calibration and §10 cross-protocol controlled empirical evidence",
        "stage2_event_count": stage2.get("event_count"),
        "stage2_latency_ms": stage2.get("latency_ms"),
        "stage6_manifest_entries": len(stage6_manifest.get("entries", [])) if isinstance(stage6_manifest.get("entries"), list) else None,
        "interpretation": [
            "Stage 2 currently supplies real-protocol log coverage and baseline run evidence.",
            "Precise latency calibration requires adding or locating upstream timestamp fields.",
            "Do not claim certification-variable isolation from Stage 2 alone."
        ]
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Create figure output conventions**

Create `stage7_deployment/figures/README.md`:

```markdown
# Stage 2 Figures

Figures in this directory must be generated from files under `stage7_deployment/data/derived/`.

Each figure must have:

- PNG preview
- PDF export suitable for LaTeX insertion
- Manifest entry in `stage7_deployment/data/manifest.json`
- Label `"real-deployment"`

No Stage 2 figure should be inserted into `final/final_paper.md` without explicit Stage 3 approval.
```

- [ ] **Step 4: Run latency extraction on baseline events**

Run:

```powershell
python .\stage7_deployment\tools\extract_latency.py --events .\stage7_deployment\data\derived\baseline_events.jsonl --output .\stage7_deployment\data\derived\baseline_latency_summary.json
```

Expected: `baseline_latency_summary.json` exists and includes `event_count`, `kind_counts`, and a `latency_ms` object.

- [ ] **Step 5: Calibrate against the latest Stage 1 manifest**

Run:

```powershell
$stage6Manifest = Get-ChildItem .\stage6_simulation\data\manifest*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
python .\stage7_deployment\tools\calibrate_stage6.py --stage2-summary .\stage7_deployment\data\derived\baseline_latency_summary.json --stage6-manifest $stage6Manifest.FullName --output .\stage7_deployment\data\derived\stage1_stage2_calibration.json
```

Expected: `stage1_stage2_calibration.json` exists and explicitly states the calibration interpretation and limits.

---

### Task 6: Multi-Validator Path Selection

**Files:**
- Modify: `stage7_deployment/targets/target_repos.md`
- Modify: `stage7_deployment/compose/compose.yaml`
- Modify: `stage7_deployment/scripts/run_local_testnet.ps1`

- [ ] **Step 1: Search the Sui checkout for multi-node or orchestrator commands**

Run:

```powershell
rg -n "orchestrator|testbed|benchmark|committee|validator" .\stage7_deployment\external\sui\crates .\stage7_deployment\external\sui\consensus > .\stage7_deployment\data\tmp\sui_multinode_search.txt
```

Expected: `sui_multinode_search.txt` contains candidate source and docs paths, or the command exits with no matches and the file remains empty.

- [ ] **Step 2: Decide the local multi-validator strategy**

Append one of these exact decisions to `stage7_deployment/targets/target_repos.md` after inspecting `sui_multinode_search.txt`:

```markdown
## Multi-Validator Decision

Decision: Use Sui local multi-node/orchestrator path.

Reason: The checked-out Sui commit exposes a local command that can run multiple validators without cloud resources.

Implementation impact: Add one Compose service per validator and one load generator service.
```

or:

```markdown
## Multi-Validator Decision

Decision: Use `sui-test-validator` for Stage 2 smoke evidence and defer multi-validator expansion to the next iteration.

Reason: The checked-out Sui commit does not expose a stable local multi-validator path within the local resource budget.

Implementation impact: Keep Stage 2 claims limited to local real-protocol smoke, delay/fault capture, and calibration workflow scaffolding.
```

- [ ] **Step 3: If multi-validator is available, add a Compose profile**

Modify `stage7_deployment/compose/compose.yaml` by adding services like this, replacing the command with the actual Sui entrypoint discovered in Step 1:

```yaml
  validator-0:
    image: ${SUI_IMAGE:-stage7-sui:local}
    profiles: ["multinode"]
    cap_add:
      - NET_ADMIN
    environment:
      RUST_LOG: "info"
      VALIDATOR_INDEX: "0"
    volumes:
      - ../data/raw:/work/data/raw
    command: ["sui", "start"]

  validator-1:
    image: ${SUI_IMAGE:-stage7-sui:local}
    profiles: ["multinode"]
    cap_add:
      - NET_ADMIN
    environment:
      RUST_LOG: "info"
      VALIDATOR_INDEX: "1"
    volumes:
      - ../data/raw:/work/data/raw
    command: ["sui", "start"]
```

Expected: the file keeps the `sui-local` smoke service and adds a separate `multinode` profile.

- [ ] **Step 4: If multi-validator is unavailable, keep the smoke scope explicit**

Append to `stage7_deployment/README.md`:

```markdown
## Current Execution Scope

The current harness runs the Sui local validator smoke target. It proves buildability, logging, netem injection, process restart capture, and Stage 1/Stage 2 data plumbing. Multi-validator consensus conclusions require the separate `multinode` profile once a stable local multi-node entrypoint is selected.
```

---

### Task 7: Manifest Updates And Findings Package

**Files:**
- Modify: `stage7_deployment/data/manifest.json`
- Modify: `stage7_deployment/data/留存清单.md`
- Create: `stage7_deployment/tools/register_artifacts.py`
- Create: `stage7_deployment/reports/phase2_findings_summary.md`

- [ ] **Step 1: Create the artifact registration script**

Create `stage7_deployment/tools/register_artifacts.py`:

```python
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def repo_sha(repo_dir: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        text=True,
        encoding="utf-8",
    ).strip()


def latest_baseline_log(raw_dir: Path) -> Path:
    candidates = sorted(raw_dir.glob("baseline_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No baseline_*.log found under {raw_dir}")
    return candidates[0]


def relative(path: Path) -> str:
    return str(path).replace("\\", "/")


def load_manifest(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schema_version": 1, "stage": "stage7_deployment", "entries": []}


def upsert(entries: list[dict], entry: dict) -> None:
    entries[:] = [item for item in entries if item.get("id") != entry["id"]]
    entries.append(entry)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--sui-dir", default="stage7_deployment/external/sui")
    parser.add_argument("--manifest", default="stage7_deployment/data/manifest.json")
    parser.add_argument("--retention", default="stage7_deployment/data/留存清单.md")
    args = parser.parse_args()

    root = Path(args.repo_root)
    raw_dir = root / "stage7_deployment/data/raw"
    derived_dir = root / "stage7_deployment/data/derived"
    log_path = latest_baseline_log(raw_dir)
    commit = repo_sha(root / args.sui_dir)
    generated_at = datetime.now(timezone.utc).date().isoformat()

    manifest_path = root / args.manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(manifest_path)
    entries = manifest.setdefault("entries", [])

    upsert(entries, {
        "id": "stage7-baseline-001",
        "kind": "raw-log",
        "source_type": "real-deployment",
        "path": relative(log_path),
        "experiment_label": "baseline_local_validator",
        "paper_mapping": "§7.1-§7.2 parameter calibration; §10 cross-protocol controlled empirical evidence",
        "claim_relation": "supports real-protocol anchoring, not certification-variable isolation",
        "generated_by": "stage7_deployment/scripts/run_local_testnet.ps1",
        "generated_at": generated_at,
        "parameters": {
            "target_repo": "https://github.com/MystenLabs/sui.git",
            "target_commit": commit,
            "netem_delay_ms": 0,
            "netem_jitter_ms": 0,
            "netem_loss_pct": 0,
        },
    })

    upsert(entries, {
        "id": "stage7-baseline-002",
        "kind": "derived-json",
        "source_type": "real-deployment",
        "path": relative(derived_dir / "baseline_latency_summary.json"),
        "experiment_label": "baseline_local_validator",
        "paper_mapping": "§7.1-§7.2 parameter calibration",
        "claim_relation": "records observable log surface and latency-extraction readiness",
        "generated_by": "stage7_deployment/tools/extract_latency.py",
        "generated_at": generated_at,
        "parameters": {
            "input": relative(derived_dir / "baseline_events.jsonl"),
        },
    })

    upsert(entries, {
        "id": "stage7-baseline-003",
        "kind": "derived-json",
        "source_type": "stage1-stage2-calibration",
        "path": relative(derived_dir / "stage1_stage2_calibration.json"),
        "experiment_label": "baseline_local_validator",
        "paper_mapping": "§7.1-§7.2; §10",
        "claim_relation": "compares Stage 1 simulation metadata with Stage 2 real-deployment evidence",
        "generated_by": "stage7_deployment/tools/calibrate_stage6.py",
        "generated_at": generated_at,
        "parameters": {
            "target_commit": commit,
        },
    })

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    retention_path = root / args.retention
    if not retention_path.exists():
        retention_path.write_text(
            "# 阶段二真实部署留存清单\n\n"
            "| 时间 | 类型 | 文件 | 实验标签 | 论文映射 | 说明 |\n"
            "|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )

    rows = [
        f"| {generated_at} | raw-log | `{relative(log_path)}` | baseline_local_validator | §7.1-§7.2, §10 | Sui local validator baseline log; real deployment, not controlled certification isolation |",
        f"| {generated_at} | derived-json | `stage7_deployment/data/derived/baseline_latency_summary.json` | baseline_local_validator | §7.1-§7.2 | Event counts and latency extraction surface for future timestamp instrumentation |",
        f"| {generated_at} | derived-json | `stage7_deployment/data/derived/stage1_stage2_calibration.json` | baseline_local_validator | §7.1-§7.2, §10 | Stage 1 and Stage 2 comparison record with honest-boundary statement |",
    ]
    retention_text = retention_path.read_text(encoding="utf-8")
    for row in rows:
        if row not in retention_text:
            retention_text += row + "\n"
    retention_path.write_text(retention_text, encoding="utf-8")

    print(f"updated {manifest_path}")
    print(f"updated {retention_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Register baseline artifacts**

Run:

```powershell
python .\stage7_deployment\tools\register_artifacts.py --repo-root .
```

Expected: `stage7_deployment/data/manifest.json` contains three baseline entries and `stage7_deployment/data/留存清单.md` contains matching rows with the observed baseline log path and Sui commit SHA.

- [ ] **Step 3: Create the Stage 2 findings summary**

Create `stage7_deployment/reports/phase2_findings_summary.md`:

```markdown
# 阶段二发现摘要

## 执行范围

本阶段构建了本地真实协议部署 harness，用于运行 Sui/Narwhal/Mysticeti 相关真实代码路径、采集日志、注入网络延迟或进程故障，并将结果与 `stage6_simulation/` 的仿真输出建立对照。

## 目标仓库结论

- 主线目标：`MystenLabs/sui`
- 备选目标：归档的 `MystenLabs/narwhal`
- 选择理由：Narwhal 独立仓库已经归档且开发迁移到 Sui；Mysticeti/Sui 是更贴近当前真实协议层面的目标。

## 已获得产物

| 产物 | 路径 | 性质 |
|---|---|---|
| 目标仓库评估 | `stage7_deployment/targets/target_repos.md` | 工程可行性 |
| 本地部署配置 | `stage7_deployment/compose/compose.yaml` | Docker Compose harness |
| 原始日志 | `stage7_deployment/data/raw/` | 真实部署原始数据 |
| 事件 JSONL | `stage7_deployment/data/derived/baseline_events.jsonl` | 派生数据 |
| 延迟摘要 | `stage7_deployment/data/derived/baseline_latency_summary.json` | 派生数据 |
| 仿真对照 | `stage7_deployment/data/derived/stage1_stage2_calibration.json` | 阶段一/二校准 |

## 论文映射

| 论文位置 | 阶段二材料如何支撑 |
|---|---|
| §7.1-§7.2 | 将参数从说明性数值推进到真实协议运行锚点 |
| §10 | 将“跨协议受控实证”从未来工作推进为局部雏形 |
| §9 | 支撑“真实部署不能隔离认证变量”的诚实边界 |

## 诚实边界

阶段二结果只能说明真实协议路径下的混合效应。它可以校准延迟分布、恢复成本和故障观测，但不能独立证明 uncertified 与 certified minimal pair 的因果差异。该因果对照仍由阶段一仿真承担。

## 后续进入阶段三前的审批材料

阶段三启动前，应向用户提交：

- 本文件
- `stage7_deployment/data/manifest.json`
- `stage7_deployment/data/留存清单.md`
- 阶段一/二对照 JSON
- 拟回填论文的段落清单
```

- [ ] **Step 4: Verify no forbidden paper edits occurred**

Run:

```powershell
Test-Path .\stage8_paper_integration
Get-ChildItem .\final\final_paper.md | Select-Object FullName,LastWriteTime,Length
```

Expected: `stage8_paper_integration` is absent unless it existed before this plan, and `final/final_paper.md` has not been edited during Stage 2 planning or execution.

---

### Task 8: Verification Commands

**Files:**
- No new files.

- [ ] **Step 1: Check created files**

Run:

```powershell
Get-ChildItem .\stage7_deployment -Recurse | Select-Object FullName,Length
```

Expected: the Stage 2 directory contains `README.md`, `compose/`, `docker/`, `scripts/`, `tools/`, `data/`, `figures/`, `reports/`, and `targets/`.

- [ ] **Step 2: Validate Python scripts compile**

Run:

```powershell
python -m py_compile .\stage7_deployment\tools\collect_logs.py .\stage7_deployment\tools\extract_latency.py .\stage7_deployment\tools\calibrate_stage6.py .\stage7_deployment\tools\register_artifacts.py
```

Expected: command exits successfully with no output.

- [ ] **Step 3: Validate Compose syntax**

Run:

```powershell
docker compose --env-file .\stage7_deployment\compose\.env.example -f .\stage7_deployment\compose\compose.yaml config
```

Expected: Docker Compose prints a normalized configuration and exits successfully.

- [ ] **Step 4: Validate manifest JSON**

Run:

```powershell
python -m json.tool .\stage7_deployment\data\manifest.json > $null
```

Expected: command exits successfully.

- [ ] **Step 5: Verify Stage 2 did not touch Stage 3 paper integration**

Run:

```powershell
Get-ChildItem .\stage8_paper_integration -ErrorAction SilentlyContinue
```

Expected: no output unless the directory existed before this work.

---

## Self-Review

### Spec Coverage

- Step 2.1 target repository selection is covered by Task 1.
- Step 2.2 local multi-node/testnet preparation is covered by Tasks 2, 3, and 6.
- Step 2.3 fault injection and latency measurement is covered by Tasks 4 and 5.
- Step 2.4 simulation-to-real comparison is covered by Task 5.
- Stage 2 deliverables are covered by Tasks 2 through 7.
- The honest boundary is repeated in Guardrails, README content, calibration output, and findings summary.

### Gap Scan

This plan avoids open-ended implementation gaps. Runtime values such as the Sui commit SHA and baseline log timestamp are written by commands or `register_artifacts.py`.

### Type And Contract Consistency

- `collect_logs.py` writes JSONL events consumed by `extract_latency.py`.
- `extract_latency.py` writes `baseline_latency_summary.json` consumed by `calibrate_stage6.py`.
- `register_artifacts.py` reads the latest raw baseline log and Sui commit SHA, then updates the manifest and retention list.
- Manifest paths and retention paths use the same `stage7_deployment/data/` layout.
- Compose service name `sui-local` and container name `stage7-sui-local` are used consistently by scripts.

## Execution Options

1. Subagent-Driven (recommended): use `superpowers:subagent-driven-development`, execute one task per fresh worker, review between tasks.
2. Inline Execution: use `superpowers:executing-plans`, execute tasks in this session with checkpoints after each major milestone.
