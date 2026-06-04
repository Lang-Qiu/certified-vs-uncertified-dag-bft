# Chapter 5 enforcement-path scan — deploy & measure three invariant-enforcement
# paths (A=non-equivocation, B=causal-history, C=availability) under independent
# per-validator packet loss. Tests the §5.2–§5.4 prediction: paths A+B ≈ flat
# (fixed overhead), path C ≈ contingent (0 at 0% loss, spikes under faults).
#
# Grid: 2 × 4 × 5 = 40 runs
#   committee: n=7 (f=2), n=4 (f=1)
#   loss_rate: 0%, 2%, 5%, 10%
#   reps: 5 per cell
#
# Observables (per run, per validator):
#   chapter5_equivoc_checks     — Path A counter
#   chapter5_equivoc_latency_us — Path A histogram (p50/p95 via _sum/_count)
#   chapter5_causal_decisions   — Path B counter
#   chapter5_causal_latency_us  — Path B histogram
#   STAGE9_RECOVERY lines       — Path C counter (from docker logs)
#   ckpt cadence                — overall throughput control
#
# Output: data/runs/chapter5_enforcement_summary.csv
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$LossRates = @(0, 2, 5, 10),
    [int]$Reps = 5,
    [ValidateSet("n7","n4","both")]
    [string]$Committee = "both",
    [int]$WindowSeconds = 90,
    [int]$WarmupCapSeconds = 180,
    [int]$Seed = 20260601
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$csvPath = Join-Path $mv "data\runs\chapter5_enforcement_summary.csv"

# CSV header
if (-not (Test-Path $csvPath)) {
    "loss_pct,committee,rep,run_id,cp_start,cp_end,window_s,cadence_ckpt_s," +
    "equivoc_checks_total,equivoc_lat_count,equivoc_lat_sum_us," +
    "causal_decisions_total,causal_lat_count,causal_lat_sum_us," +
    "recovery_fetches_total,status" |
    Set-Content -Path $csvPath -Encoding UTF8
}

# ---------- helpers ----------
function Get-Ckpt {
    try {
        $b = '{"jsonrpc":"2.0","id":1,"method":"sui_getLatestCheckpointSequenceNumber","params":[]}'
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:9000" -Method Post -ContentType "application/json" -Body $b -TimeoutSec 5
        return [int64]$r.result
    } catch { return -1 }
}

function Get-MetricValue($lines, [string]$name) {
    # Prometheus text format with Sui prefix: consensus_<name>{labels} value
    # Filter out HELP/TYPE lines (starting with #)
    ($lines | Where-Object { $_ -notmatch '^#' } | Select-String -Pattern "${name}[{ ]") | ForEach-Object { $_.Line -replace "^.* (\S+)$",'$1' } | Select-Object -First 1
}

function Get-HistogramStats($lines, [string]$name) {
    $lines = $lines | Where-Object { $_ -notmatch '^#' }
    $sum = (Get-MetricValue $lines "${name}_sum")
    $count = (Get-MetricValue $lines "${name}_count")
    if ($sum -and $count -and [double]$count -gt 0) {
        return @{ sum = [double]$sum; count = [double]$count; mean = [double]$sum / [double]$count }
    }
    return @{ sum = 0; count = 0; mean = 0 }
}

function Collect-Metrics([string]$runId, [int]$nv) {
    # Collect chapter5 metrics from all validators via docker exec
    $totalEquivoc = 0; $totalCausal = 0
    $equivocLatSum = 0.0; $equivocLatCount = 0.0
    $causalLatSum = 0.0; $causalLatCount = 0.0
    $totalRecovery = 0

    for ($vi = 1; $vi -le $nv; $vi++) {
        $cname = "${runId}-validator-${vi}"
        $mport = 2002 + ($vi - 1) * 10
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $mlines = & docker exec $cname timeout 10 curl -s "http://localhost:$mport/metrics" 2>&1
        $ErrorActionPreference = $prev
        if (-not $mlines) { continue }

        $ec = Get-MetricValue $mlines "chapter5_equivoc_checks"
        if ($ec) { $totalEquivoc += [int64]$ec }
        $eh = Get-HistogramStats $mlines "chapter5_equivoc_latency_us"
        $equivocLatSum += $eh.sum; $equivocLatCount += $eh.count

        $cd = Get-MetricValue $mlines "chapter5_causal_decisions"
        if ($cd) { $totalCausal += [int64]$cd }
        $ch = Get-HistogramStats $mlines "chapter5_causal_latency_us"
        $causalLatSum += $ch.sum; $causalLatCount += $ch.count

        # Path C: STAGE9_RECOVERY from docker logs
        $prev2 = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $logLines = & timeout 10 docker logs $cname 2>&1
        $ErrorActionPreference = $prev2
        $totalRecovery += (($logLines | Select-String -Pattern "STAGE9_RECOVERY" -SimpleMatch) | Measure-Object).Count
    }
    return @{
        equivoc_checks = $totalEquivoc
        equivoc_lat_count = $equivocLatCount
        equivoc_lat_sum_us = $equivocLatSum
        causal_decisions = $totalCausal
        causal_lat_count = $causalLatCount
        causal_lat_sum_us = $causalLatSum
        recovery_fetches = $totalRecovery
    }
}

function Inject-Loss([string]$runId, [int]$nv, [int]$lossPct) {
    if ($lossPct -eq 0) { return }
    for ($vi = 1; $vi -le $nv; $vi++) {
        $cname = "${runId}-validator-${vi}"
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $null = & docker exec $cname tc qdisc replace dev eth0 root netem loss "${lossPct}%" 2>&1
        $ErrorActionPreference = $prev
    }
}

# ---------- run grid ----------
$committees = @()
if ($Committee -in @("n7","both")) { $committees += @{ n=7; f=2; compose="compose.multivalidator.yaml"; suffix="n7" } }
if ($Committee -in @("n4","both")) { $committees += @{ n=4; f=1; compose="compose.multivalidator.n4.yaml"; suffix="n4" } }

foreach ($cmeta in $committees) {
  $compose = Join-Path $mv "compose\$($cmeta.compose)"
  $prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
  if ($cmeta.n -eq 4) { $prepare = Join-Path $mv "scripts\prepare_multivalidator_n4.ps1" }
  $stop = Join-Path $mv "scripts\stop_multivalidator.ps1"

  foreach ($loss in $LossRates) {
    foreach ($rep in 1..$Reps) {
        $RunId = "ch5_${($cmeta.suffix)}_loss${loss}_r${rep}"
        Write-Host "########## CHAPTER5 n=$($cmeta.n) loss=${loss}% rep=$rep RunId=$RunId ##########"
        $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
        $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = "0"
        $env:SUI_CONSENSUS_CERTIFICATE_GATE = "0"
        $cpStart = -1; $cpEnd = -1; $cadence = -1.0; $status = "started"
        $eqChk = 0; $eqLatCt = 0.0; $eqLatSum = 0.0
        $causDec = 0; $causLatCt = 0.0; $causLatSum = 0.0
        $recFetch = 0

        try {
            & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $prepare -RunId $RunId -Seed $Seed -Scenario "chapter5" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "prepare failed (exit=$LASTEXITCODE)" }
            $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
            $null = & docker-compose -f $compose up -d 2>&1
            $code = [int]$LASTEXITCODE; $ErrorActionPreference = $prev
            if ($code -ne 0) { throw "compose up failed ($code)" }

            # warmup
            $t0 = Get-Date; $stable = $false; $last = -1
            while (((Get-Date) - $t0).TotalSeconds -lt $WarmupCapSeconds) {
                Start-Sleep -Seconds 10
                $c = Get-Ckpt
                if ($c -ge 30 -and $last -ge 0 -and ($c - $last) -ge 10) { $stable = $true; break }
                $last = $c
            }
            if (-not $stable) { throw "warmup failed (last cp=$last)" }

            # inject loss
            Inject-Loss -runId $RunId -nv $cmeta.n -lossPct $loss
            Start-Sleep -Seconds 5

            # measurement window
            $cpStart = Get-Ckpt
            Start-Sleep -Seconds $WindowSeconds
            $cpEnd = Get-Ckpt
            if ($cpEnd -gt $cpStart) { $cadence = ($cpEnd - $cpStart) / $WindowSeconds }

            # collect metrics
            $metrics = Collect-Metrics -runId $RunId -nv $cmeta.n
            $eqChk = $metrics.equivoc_checks
            $eqLatCt = $metrics.equivoc_lat_count; $eqLatSum = $metrics.equivoc_lat_sum_us
            $causDec = $metrics.causal_decisions
            $causLatCt = $metrics.causal_lat_count; $causLatSum = $metrics.causal_lat_sum_us
            $recFetch = $metrics.recovery_fetches
            $status = "ok"
        } catch {
            Write-Host "ERROR: $_"
            $status = "failed: $_"
        } finally {
            # teardown
            $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
            & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $stop -RunId $RunId 2>&1 | Out-Null
            $ErrorActionPreference = $prev
            Start-Sleep -Seconds 5
        }

        # write CSV row
        "$loss,$($cmeta.n),$rep,$RunId,$cpStart,$cpEnd,$WindowSeconds,$([math]::Round($cadence,4))," +
        "$eqChk,$eqLatCt,$eqLatSum,$causDec,$causLatCt,$causLatSum,$recFetch,$status" |
        Add-Content -Path $csvPath -Encoding UTF8
        Write-Host "ROW: loss=$loss n=$($cmeta.n) rep=$rep cadence=$([math]::Round($cadence,4)) eqChk=$eqChk causDec=$causDec recFetch=$recFetch status=$status"
        # progress file for bg task monitoring (Write-Host doesn't reach bg stdout)
        $progFile = Join-Path $mv "data\runs\chapter5_progress.txt"
        $done = (Get-Content $csvPath -Encoding UTF8 | Where-Object { $_ -match ',ok$' } | Measure-Object).Count
        "$(Get-Date -Format 'HH:mm:ss') | $done/40 done | n=$($cmeta.n) loss=${loss}% rep=$rep cadence=$([math]::Round($cadence,4)) eqChk=$eqChk causDec=$causDec recFetch=$recFetch status=$status" | Set-Content -Path $progFile -Encoding UTF8
    }
  }
}
Write-Host "########## DONE. CSV: $csvPath ##########"
