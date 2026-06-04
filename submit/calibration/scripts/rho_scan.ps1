# P0-2 rho-axis scan -- fault FREQUENCY vs cadence (sec. 7.3 standalone calibration).
#
# WHY this design:
#   sec.7.3 claims cadence degrades as recovery frequency rho rises, and that beyond a
#   critical rho* the certified arm's up-front amortization flips to an advantage. rho*
#   was only ever DERIVED (from Delta_save / excess), never directly swept in deployment.
#   This harness sweeps fault count N and measures cadence_eff(rho) and recFetch(rho).
#
#   Each fault must be a critical-path ROTATION (not a static partition): only rotation
#   puts the Delta_recover-gated PULL recovery on the cadence critical path (see the
#   rationale at the top of phaseA_criticalpath_partition.ps1). Delta_recover is FIXED at
#   1000ms to amplify the per-fault recovery signal; cert is OFF (uncertified baseline arm).
#
#   DEVIATION from roadmap's "N faults evenly in a fixed 200s window": at Delta_recover=
#   1000ms one rotation+resume cycle is ~40-60s, so N=8 (~400s) cannot fit evenly in 200s
#   without overlap. We instead inject N faults SEQUENTIALLY over one run and report
#   rho = N / commits, cadence_eff = commits / wallclock over the whole post-warmup span.
#   Higher N => more wallclock lost to stalls => lower cadence_eff. This is the throughput
#   degradation sec.7.3 predicts; rho stays well-defined as fault density per commit.
#
# Grid: 5 (N) x 3 (reps) = 15 runs. N in {0,1,2,4,8}.
# Output CSV columns:
#   fault_count,rep,run_id,cp_start,cp_end,commits,wallclock_s,cadence_eff,
#   sum_t_resume_s,recFetch,rho,eqChk,causDec,status
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$FaultCounts = @(0, 1, 2, 4, 8),
    [int]$Reps = 3,
    [int]$RecoverMs = 1000,           # FIXED -- amplify per-fault recovery signal
    [int]$GapSeconds = 20,            # per-fault disconnect window (>= push window -> forces PULL)
    [int]$SettleSeconds = 6,          # quiet gap between sequential faults
    [int]$BaselineWindowSeconds = 120,# N=0 fault-free observation window for cadence intercept
    [int]$WarmupCapSeconds = 150,
    [int]$ResumeCapSeconds = 120,     # per-fault resume watch cap
    [int]$ResumeThreshold = 8,
    [int]$Seed = 20260602
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$csv = Join-Path $mv "data\runs\rho_scan_summary.csv"
if (-not (Test-Path $csv)) {
    "fault_count,rep,run_id,cp_start,cp_end,commits,wallclock_s,cadence_eff,sum_t_resume_s,recFetch,rho,eqChk,causDec,status" `
    | Set-Content -Path $csv -Encoding UTF8
}
# Resume: skip cells already completed (status ok/partial) on a re-launch.
$doneIds = @{}
Import-Csv $csv | ForEach-Object {
    if ($_.status -eq "ok" -or $_.status -eq "partial") { $doneIds[$_.run_id] = $true }
}
Write-Host "Resume: $($doneIds.Count) completed cell(s) will be skipped."

# ---------- helpers (mirror partition_grid_scan.ps1 -- proven-correct forms) ----------
function Get-Ckpt {
    try {
        $b = '{"jsonrpc":"2.0","id":1,"method":"sui_getLatestCheckpointSequenceNumber","params":[]}'
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:9000" -Method Post -ContentType "application/json" -Body $b -TimeoutSec 5
        return [int64]$r.result
    } catch { return -1 }
}
function Get-FetchCount([string]$container) {
    # bare docker logs -- NOT `timeout` (Windows timeout.exe breaks it; see partition_grid_scan.ps1).
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

# One critical-path rotation fault. Returns t_resume seconds (ResumeCapSeconds if it never
# resumed). Cuts {v1,v2} for GapSeconds (carriers {v3..v7}=5 progress), then heals {v1,v2}
# and cuts {v3,v4} -> connected-but-syncing set is sub-quorum -> stall until v1,v2 PULL their
# gap (Delta_recover-gated) and rejoin. Heals {v3,v4} before returning.
function Invoke-RotationFault($net, $v1, $v2, $v3, $v4, $v1ip, $v2ip, $v3ip, $v4ip, [int]$gapSec, [int]$resumeCap, [int]$resumeThr) {
    & docker network disconnect $net $v1 2>&1 | Out-Null
    & docker network disconnect $net $v2 2>&1 | Out-Null
    Start-Sleep -Seconds $gapSec
    & docker network connect --ip $v1ip $net $v1 2>&1 | Out-Null
    & docker network connect --ip $v2ip $net $v2 2>&1 | Out-Null
    & docker network disconnect $net $v3 2>&1 | Out-Null
    & docker network disconnect $net $v4 2>&1 | Out-Null
    $tRot = Get-Date
    Start-Sleep -Seconds 3
    $cpRot = Get-Ckpt
    $tResume = $resumeCap
    while (((Get-Date) - $tRot).TotalSeconds -lt $resumeCap) {
        Start-Sleep -Seconds 3
        $c = Get-Ckpt
        if ($c -ge 0 -and ($c - $cpRot) -ge $resumeThr) {
            $tResume = [Math]::Round(((Get-Date) - $tRot).TotalSeconds, 1); break
        }
    }
    & docker network connect --ip $v3ip $net $v3 2>&1 | Out-Null
    & docker network connect --ip $v4ip $net $v4 2>&1 | Out-Null
    return $tResume
}

# ---------- run sweep ----------
:sweep foreach ($N in $FaultCounts) {
  foreach ($rep in 1..$Reps) {
    $RunId = "rho_n${N}_r${rep}"
    if ($doneIds.ContainsKey($RunId)) { Write-Host "SKIP (already done): $RunId"; continue }
    if (-not (Wait-Docker 180)) { Write-Host "ABORT: docker unhealthy at $RunId."; break sweep }
    $net = "${RunId}_net"
    $v1 = "${RunId}-validator-1"; $v2 = "${RunId}-validator-2"
    $v3 = "${RunId}-validator-3"; $v4 = "${RunId}-validator-4"
    $v1ip = "172.28.7.11"; $v2ip = "172.28.7.12"; $v3ip = "172.28.7.13"; $v4ip = "172.28.7.14"
    $cpStart = -1; $cpEnd = -1; $commits = -1; $wall = -1; $cad = -1
    $sumRes = 0.0; $recFetch = -1; $rho = -1; $eqChk = 0; $causDec = 0; $status = "started"
    Write-Host "########## RHO N=$N rep=$rep RunId=$RunId (Delta_recover=${RecoverMs}ms cert=OFF) ##########"
    $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
    $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = [string]$RecoverMs; $env:SUI_CONSENSUS_CERTIFICATE_GATE = "0"
    try {
        & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $prepare `
            -RunId $RunId -Seed $Seed -Scenario "p0_rho" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
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

        $cpStart = Get-Ckpt; $tSpanStart = Get-Date
        if ($N -eq 0) {
            # fault-free baseline window -> cadence intercept; recFetch should stay ~0
            Start-Sleep -Seconds $BaselineWindowSeconds
        } else {
            for ($i = 1; $i -le $N; $i++) {
                $tr = Invoke-RotationFault $net $v1 $v2 $v3 $v4 $v1ip $v2ip $v3ip $v4ip $GapSeconds $ResumeCapSeconds $ResumeThreshold
                $sumRes += [double]$tr
                Write-Host "    fault $i/$N : t_resume=${tr}s"
                Start-Sleep -Seconds $SettleSeconds
            }
        }
        $cpEnd = Get-Ckpt; $wall = [Math]::Round(((Get-Date) - $tSpanStart).TotalSeconds, 1)
        $commits = $cpEnd - $cpStart
        $cad = if ($wall -gt 0) { [Math]::Round($commits / $wall, 4) } else { -1 }
        $rho = if ($commits -gt 0) { [Math]::Round($N / [double]$commits, 6) } else { -1 }
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
    $row = "$N,$rep,$RunId,$cpStart,$cpEnd,$commits,$wall,$cad,$sumRes,$recFetch,$rho,$eqChk,$causDec,$status"
    Add-Content -Path $csv -Value $row -Encoding UTF8
    Write-Host "ROW: $row"
    Start-Sleep -Seconds 15
  }
}
Write-Host "########## RHO SCAN DONE -> $csv ##########"
