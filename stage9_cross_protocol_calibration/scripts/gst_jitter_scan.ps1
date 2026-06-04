# P1-5 GST Jitter Scan — sec.7.4 partial-synchrony degradation.
#
# Simulates GST cycling: every JitterPeriodSeconds, a short (JitterDurationSeconds)
# partition is opened on {v1,v2} then healed. The cadence pays a recovery cost each
# cycle; as the jitter period shrinks (more frequent disruptions), recovery overhead
# should accumulate and cadence_eff should degrade monotonically.
#
# Why not a full rotation fault: a full rotation (heal v1,v2 + cut v3,v4) creates a
# sub-quorum stall. For GST jitter we want SUB-critical disruptions — the network
# should keep going but pay recovery tolls. Partition-and-heal on the SAME pair
# keeps quorum intact (v3..v7=5=quorum) so the network never halts; only v1,v2
# pay the PULL cost each cycle, and cadence absorbs the overhead.
#
# Grid: period ∈ {30, 60, 90}s × 3 reps = 9 runs.
#   period=30s: more frequent disruptions, more accumulated recovery cost
#   period=90s: less frequent, recovery cost amortized over more commits
#
# Fixed: JitterDuration=5s, Δ_recover=500ms, cert=OFF, observation window=200s.
# Output CSV: data/runs/gst_jitter_summary.csv
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$JitterPeriods = @(30, 60, 90),
    [int]$JitterDurationSeconds = 5,
    [int]$Reps = 3,
    [int]$RecoverMs = 500,
    [int]$ObservationWindowSeconds = 200,
    [int]$WarmupCapSeconds = 150,
    [int]$Seed = 20260603
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$csv = Join-Path $mv "data\runs\gst_jitter_summary.csv"
if (-not (Test-Path $csv)) {
    "jitter_period_s,rep,run_id,cp_start,cp_end,commits,wallclock_s,cadence_eff,cycles,sum_stall_s,recFetch,rho,eqChk,causDec,status" `
    | Set-Content -Path $csv -Encoding UTF8
}
$doneIds = @{}
Import-Csv $csv | ForEach-Object {
    if ($_.status -eq "ok") { $doneIds[$_.run_id] = $true }
}
Write-Host "Resume: $($doneIds.Count) completed cell(s) will be skipped."

# ---------- helpers ----------
function Get-Ckpt {
    try {
        $b = '{"jsonrpc":"2.0","id":1,"method":"sui_getLatestCheckpointSequenceNumber","params":[]}'
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:9000" -Method Post -ContentType "application/json" -Body $b -TimeoutSec 5
        return [int64]$r.result
    } catch { return -1 }
}
function Get-FetchCount([string]$container) {
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $lines = & docker logs $container 2>&1
    $ErrorActionPreference = $prev
    return (($lines | Select-String -Pattern "STAGE9_RECOVERY" -SimpleMatch) | Measure-Object).Count
}
function Get-MetricValue($lines, [string]$name) {
    ($lines | Where-Object { $_ -notmatch '^#' } | Select-String -Pattern "${name}[{ ]") `
    | ForEach-Object { $_.Line -replace "^.* (\S+)$",'$1' } | Select-Object -First 1
}
function Collect-Chapter5([string]$runId) {
    $totalEq = 0; $totalCaus = 0
    for ($vi = 1; $vi -le 7; $vi++) {
        $cname = "${runId}-validator-${vi}"; $mport = 2002 + ($vi - 1) * 10
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $mlines = & docker exec $cname timeout 10 curl -s "http://localhost:$mport/metrics" 2>&1
        $ErrorActionPreference = $prev
        if (-not $mlines) { continue }
        $ec = Get-MetricValue $mlines "chapter5_equivoc_checks"; if ($ec) { $totalEq += [int64]$ec }
        $cd = Get-MetricValue $mlines "chapter5_causal_decisions"; if ($cd) { $totalCaus += [int64]$cd }
    }
    return @{ eqChk = $totalEq; causDec = $totalCaus }
}
function Wait-Docker([int]$capSec = 180) {
    $t0 = Get-Date
    while (((Get-Date) - $t0).TotalSeconds -lt $capSec) {
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $null = & docker info --format '{{.ServerVersion}}' 2>&1
        $ok = ($LASTEXITCODE -eq 0); $ErrorActionPreference = $prev
        if ($ok) { return $true }
        Start-Sleep -Seconds 5
    }
    return $false
}

:sweep foreach ($period in $JitterPeriods) {
  foreach ($rep in 1..$Reps) {
    $RunId = "gst_p${period}_r${rep}"
    if ($doneIds.ContainsKey($RunId)) { Write-Host "SKIP (already done): $RunId"; continue }
    if (-not (Wait-Docker 180)) { Write-Host "ABORT: docker unhealthy at $RunId."; break sweep }
    $net = "${RunId}_net"
    $v1 = "${RunId}-validator-1"; $v2 = "${RunId}-validator-2"
    $v1ip = "172.28.7.11"; $v2ip = "172.28.7.12"
    $cpStart = -1; $cpEnd = -1; $commits = -1; $wall = -1; $cad = -1
    $cycles = 0; $sumStall = 0.0; $recFetch = -1; $rho = -1; $eqChk = 0; $causDec = 0; $status = "started"
    Write-Host "########## GST JITTER period=${period}s rep=$rep RunId=$RunId ##########"
    $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
    $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = [string]$RecoverMs; $env:SUI_CONSENSUS_CERTIFICATE_GATE = "0"
    try {
        & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $prepare `
            -RunId $RunId -Seed $Seed -Scenario "p1_gst" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "prepare failed" }
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $null = & docker-compose -f $compose up -d 2>&1
        $code = [int]$LASTEXITCODE; $ErrorActionPreference = $prev
        if ($code -ne 0) { throw "compose up failed ($code)" }

        # warmup
        $t0 = Get-Date; $stable = $false; $last = -1
        while (((Get-Date) - $t0).TotalSeconds -lt $WarmupCapSeconds) {
            Start-Sleep -Seconds 8
            $c = Get-Ckpt
            if ($c -ge 30 -and $last -ge 0 -and ($c - $last) -ge 20) { $stable = $true; break }
            $last = $c
        }
        if (-not $stable) { throw "warmup failed (last cp=$last)" }

        # Observation window: jitter cycles at the swept period.
        # Each cycle: pre_jitter checkpoint, disconnect v1,v2 for JitterDuration, reconnect, measure t_resume.
        $cpStart = Get-Ckpt; $tWinStart = Get-Date
        $nextJitterAt = $tWinStart + (New-TimeSpan -Seconds $period)
        while (((Get-Date) - $tWinStart).TotalSeconds -lt $ObservationWindowSeconds) {
            Start-Sleep -Seconds 1
            $now = Get-Date
            if ($now -lt $nextJitterAt) { continue }

            # Jitter cycle: partition v1,v2 for JitterDurationSeconds
            & docker network disconnect $net $v1 2>&1 | Out-Null
            & docker network disconnect $net $v2 2>&1 | Out-Null
            Start-Sleep -Seconds $JitterDurationSeconds
            & docker network connect --ip $v1ip $net $v1 2>&1 | Out-Null
            & docker network connect --ip $v2ip $net $v2 2>&1 | Out-Null
            $cycles++
            $sumStall += $JitterDurationSeconds
            $nextJitterAt = $nextJitterAt + (New-TimeSpan -Seconds $period)
            Write-Host "    cycle $cycles at +$([Math]::Round(($now - $tWinStart).TotalSeconds, 0))s"
        }
        $cpEnd = Get-Ckpt; $wall = [Math]::Round(((Get-Date) - $tWinStart).TotalSeconds, 1)
        $commits = $cpEnd - $cpStart
        $cad = if ($wall -gt 0) { [Math]::Round($commits / $wall, 4) } else { -1 }
        $rho = if ($wall -gt 0) { [Math]::Round($cycles / $wall, 8) } else { -1 }
        $f1 = Get-FetchCount $v1; $f2 = Get-FetchCount $v2; $recFetch = $f1 + $f2
        $ch5 = Collect-Chapter5 $RunId; $eqChk = $ch5.eqChk; $causDec = $ch5.causDec
        $status = if ($commits -gt 0) { "ok" } else { "partial" }
    }
    catch { $status = "fail:" + $_.Exception.Message.Replace(",",";") }
    finally {
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $stop -RunId $RunId 2>&1 | Out-Null
        & docker network rm $net 2>&1 | Out-Null
        $null = & docker network prune -f 2>&1
        $ErrorActionPreference = $prev
        Start-Sleep -Seconds 5
    }
    $row = "$period,$rep,$RunId,$cpStart,$cpEnd,$commits,$wall,$cad,$cycles,$sumStall,$recFetch,$rho,$eqChk,$causDec,$status"
    Add-Content -Path $csv -Value $row -Encoding UTF8
    Write-Host "ROW: $row"
    Start-Sleep -Seconds 15
  }
}
Write-Host "########## GST JITTER DONE -> $csv ##########"
