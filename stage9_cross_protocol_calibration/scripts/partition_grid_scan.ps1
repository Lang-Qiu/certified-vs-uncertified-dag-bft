# P0-1 Partition Grid — sweep disconnect duration × Δ_recover under critical-path rotation.
#
# Extends phaseA_criticalpath_partition.ps1: parameterizes GapSeconds to quantify the
# "cliff" where PUSH is exhausted → PULL activates. Combined with Δ_recover sweep,
# this closes §5.4's contingent-liability boundary.
#
# Grid: 3×3×2 = 18 runs
#   disconnect_duration: 30s, 60s, 90s
#   Δ_recover: 0ms, 500ms, 1000ms
#   reps: 2 per cell
#
# Observables per run:
#   cp_before, cp_gap, cp_rot, t_resume_s — cadence stall timing
#   v1_fetches, v2_fetches — STAGE9_RECOVERY count (= recFetch, the PULL activation counter)
#   chapter5 equivoc/causal counters — Path A/B cost (control: should be flat regardless)
#   status — ok | stall_timeout | fail:...
#
# Output CSV: data/runs/partition_grid_summary.csv
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$DisconnectDurations = @(30, 60, 90),
    [int[]]$RecoverMsList = @(0, 500, 1000),
    [int]$Reps = 2,
    [int]$WarmupCapSeconds = 150,
    [int]$ResumeCapSeconds = 250,
    [int]$ResumeThreshold = 8,
    [int]$Seed = 20260601
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$csv = Join-Path $mv "data\runs\partition_grid_summary.csv"
if (-not (Test-Path $csv)) {
    "disconnect_s,recover_ms,rep,run_id,cp_before,cp_gap,cp_rot,t_resume_s,v1_fetches,v2_fetches,eqChk,causDec,status" `
    | Set-Content -Path $csv -Encoding UTF8
}
# Resume: collect run_ids already present (status ok or stall_timeout) so a re-launch skips them.
$doneIds = @{}
Import-Csv $csv | ForEach-Object {
    if ($_.status -eq "ok" -or $_.status -eq "stall_timeout") { $doneIds[$_.run_id] = $true }
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
    # NOTE: do NOT prepend `timeout` here. Under PowerShell `timeout` is Windows
    # timeout.exe (not GNU coreutils): it errors in a non-interactive shell, docker
    # logs never runs, and the count silently returns 0. Phase A used bare `docker
    # logs` and that is the proven-correct form. Container log volume here is bounded
    # (~5-7 min lifetime) so there is no real hang risk.
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $lines = & docker logs $container 2>&1
    $ErrorActionPreference = $prev
    return (($lines | Select-String -Pattern "STAGE9_RECOVERY" -SimpleMatch) | Measure-Object).Count
}
function Get-MetricValue($lines, [string]$name) {
    ($lines | Where-Object { $_ -notmatch '^#' } | Select-String -Pattern "${name}[{ ]") `
    | ForEach-Object { $_.Line -replace "^.* (\S+)$",'$1' } | Select-Object -First 1
}
# Block until the docker daemon answers `docker info`, polling up to $capSec.
# Returns $true if healthy, $false if it never came back (the WSL2 backend is the
# fragile link under rapid churn — gate every run on it rather than charging ahead).
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
function Collect-Chapter5([string]$runId) {
    $totalEq = 0; $totalCaus = 0
    for ($vi = 1; $vi -le 7; $vi++) {
        $cname = "${runId}-validator-${vi}"
        $mport = 2002 + ($vi - 1) * 10
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $mlines = & docker exec $cname timeout 10 curl -s "http://localhost:$mport/metrics" 2>&1
        $ErrorActionPreference = $prev
        if (-not $mlines) { continue }
        $ec = Get-MetricValue $mlines "chapter5_equivoc_checks"
        if ($ec) { $totalEq += [int64]$ec }
        $cd = Get-MetricValue $mlines "chapter5_causal_decisions"
        if ($cd) { $totalCaus += [int64]$cd }
    }
    return @{ eqChk = $totalEq; causDec = $totalCaus }
}

# ---------- run grid ----------
:grid foreach ($gapSec in $DisconnectDurations) {
  foreach ($ms in $RecoverMsList) {
    foreach ($rep in 1..$Reps) {
        $RunId = "pgrid_d${gapSec}_ms${ms}_r${rep}"
        if ($doneIds.ContainsKey($RunId)) {
            Write-Host "SKIP (already done): $RunId"
            continue
        }
        # Gate on daemon health before touching anything — if WSL2 is wedged, wait it out.
        if (-not (Wait-Docker 180)) {
            Write-Host "ABORT: docker daemon not healthy after 180s at $RunId. Stopping grid."
            break grid
        }
        $net = "${RunId}_net"
        $v1 = "${RunId}-validator-1"; $v2 = "${RunId}-validator-2"
        $v3 = "${RunId}-validator-3"; $v4 = "${RunId}-validator-4"
        $v1ip = "172.28.7.11"; $v2ip = "172.28.7.12"; $v3ip = "172.28.7.13"; $v4ip = "172.28.7.14"
        $cpB = -1; $cpG = -1; $cpR = -1; $tRes = -1; $f1 = -1; $f2 = -1
        $eqChk = 0; $causDec = 0; $status = "started"
        Write-Host "########## PGRID gap=${gapSec}s recover_ms=${ms} rep=${rep} RunId=${RunId} ##########"
        $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
        $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = [string]$ms; $env:SUI_CONSENSUS_CERTIFICATE_GATE = "0"
        try {
            & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $prepare `
                -RunId $RunId -Seed $Seed -Scenario "p0_grid" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "prepare failed" }
            $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
            $null = & docker-compose -f $compose up -d 2>&1
            $code = [int]$LASTEXITCODE; $ErrorActionPreference = $prev
            if ($code -ne 0) { throw "compose up failed ($code)" }

            # warmup: cp >= 30 && advances >= 20 in 8s
            $t0 = Get-Date; $stable = $false; $last = -1
            while (((Get-Date) - $t0).TotalSeconds -lt $WarmupCapSeconds) {
                Start-Sleep -Seconds 8
                $c = Get-Ckpt
                if ($c -ge 30 -and $last -ge 0 -and ($c - $last) -ge 20) { $stable = $true; break }
                $last = $c
            }
            if (-not $stable) { throw "warmup failed (last cp=$last)" }
            $cpB = Get-Ckpt

            # GAP: cut v1,v2 for $gapSec seconds (carriers v3..v7=5=quorum progress)
            & docker network disconnect $net $v1 2>&1 | Out-Null
            & docker network disconnect $net $v2 2>&1 | Out-Null
            Start-Sleep -Seconds $gapSec
            $cpG = Get-Ckpt
            if ($cpG -lt 0 -or ($cpG - $cpB) -lt 10) { throw "gap not opened (cpB=$cpB cpG=$cpG)" }

            # ROTATE: heal v1,v2 + cut v3,v4 -> {v5,v6,v7}=3 < quorum -> STALL
            & docker network connect --ip $v1ip $net $v1 2>&1 | Out-Null
            & docker network connect --ip $v2ip $net $v2 2>&1 | Out-Null
            & docker network disconnect $net $v3 2>&1 | Out-Null
            & docker network disconnect $net $v4 2>&1 | Out-Null
            $tRot = Get-Date
            Start-Sleep -Seconds 3
            $cpR = Get-Ckpt

            # RESUME-WATCH
            $resumed = $false
            while (((Get-Date) - $tRot).TotalSeconds -lt $ResumeCapSeconds) {
                Start-Sleep -Seconds 3
                $c = Get-Ckpt
                if ($c -ge 0 -and ($c - $cpR) -ge $ResumeThreshold) {
                    $tRes = [Math]::Round(((Get-Date) - $tRot).TotalSeconds, 1); $resumed = $true; break
                }
            }
            $f1 = Get-FetchCount $v1; $f2 = Get-FetchCount $v2
            $ch5 = Collect-Chapter5 $RunId; $eqChk = $ch5.eqChk; $causDec = $ch5.causDec
            if ($resumed) { $status = "ok" } else { $tRes = $ResumeCapSeconds; $status = "stall_timeout" }

            # heal rotated set
            & docker network connect --ip $v3ip $net $v3 2>&1 | Out-Null
            & docker network connect --ip $v4ip $net $v4 2>&1 | Out-Null
        }
        catch { $status = "fail:" + $_.Exception.Message.Replace(",",";") }
        finally {
            $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
            & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $stop -RunId $RunId 2>&1 | Out-Null
            # Reclaim the per-run network + any dangling ones; leftover networks are what
            # accumulate under churn and eventually wedge the WSL2 bridge.
            & docker network rm $net 2>&1 | Out-Null
            $null = & docker network prune -f 2>&1
            $ErrorActionPreference = $prev
            Start-Sleep -Seconds 5
        }
        $row = "$gapSec,$ms,$rep,$RunId,$cpB,$cpG,$cpR,$tRes,$f1,$f2,$eqChk,$causDec,$status"
        Add-Content -Path $csv -Value $row -Encoding UTF8
        Write-Host "ROW: $row"
        # Longer inter-run cooldown: give the daemon time to fully release containers/veths
        # before the next teardown/re-up cycle (the rapid cycling is what crashed it at run 5).
        Start-Sleep -Seconds 15
    }
  }
}
Write-Host "########## PGRID DONE -> $csv ##########"
