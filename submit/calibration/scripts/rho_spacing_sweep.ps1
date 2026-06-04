# P0-2 SPACING SWEEP — genuinely vary rho by sweeping inter-fault settle time.
#
# DIAGNOSIS of rho_scan.ps1: sequential faults with fixed 6s settle kept rho ~constant
# at 0.009 across all N>=1. We only had two rho clusters (0 and 0.009), not a curve.
#
# FIX: FIX N=2 rotation faults. SWEEP settleSeconds ∈ {20,40,80,160} (fault-free
# quiet between faults). Longer settle = more commits between faults = LOWER rho =
# recovery stall is a smaller fraction of the window = cadence_eff RISES.
#
# This gives a genuine 4-level rho gradient for the sec.7.3 degradation curve.
#
#   rho = N / commits  (N=2 fixed, commits vary with settle length)
#   cadence_eff = commits / wallclock  (measured; should rise as rho falls)
#
# Grid: 4 settle levels × 3 reps = 12 runs. Delta_recover=1000ms, cert=OFF.
# Output CSV: same columns as rho_scan_summary.csv.
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$SettleSeconds = @(20, 40, 80, 160),
    [int]$Reps = 3,
    [int]$RecoverMs = 1000,
    [int]$GapSeconds = 20,
    [int]$WarmupCapSeconds = 150,
    [int]$ResumeCapSeconds = 120,
    [int]$ResumeThreshold = 8,
    [int]$Seed = 20260603
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$csv = Join-Path $mv "data\runs\rho_spacing_summary.csv"
if (-not (Test-Path $csv)) {
    "fault_count,settle_s,rep,run_id,cp_start,cp_end,commits,wallclock_s,cadence_eff,sum_t_resume_s,recFetch,rho,eqChk,causDec,status" `
    | Set-Content -Path $csv -Encoding UTF8
}
$doneIds = @{}
Import-Csv $csv | ForEach-Object {
    if ($_.status -eq "ok" -or $_.status -eq "partial") { $doneIds[$_.run_id] = $true }
}
Write-Host "Resume: $($doneIds.Count) completed cell(s) will be skipped."

# ---------- helpers (proven-correct forms from partition_grid_scan.ps1) ----------
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

$N = 2  # FIXED fault count — settle seconds is the swept variable

:sweep foreach ($settleSec in $SettleSeconds) {
  foreach ($rep in 1..$Reps) {
    $RunId = "rhosettle_s${settleSec}_r${rep}"
    if ($doneIds.ContainsKey($RunId)) { Write-Host "SKIP (already done): $RunId"; continue }
    if (-not (Wait-Docker 180)) { Write-Host "ABORT: docker unhealthy at $RunId."; break sweep }
    $net = "${RunId}_net"
    $v1 = "${RunId}-validator-1"; $v2 = "${RunId}-validator-2"
    $v3 = "${RunId}-validator-3"; $v4 = "${RunId}-validator-4"
    $v1ip = "172.28.7.11"; $v2ip = "172.28.7.12"; $v3ip = "172.28.7.13"; $v4ip = "172.28.7.14"
    $cpStart = -1; $cpEnd = -1; $commits = -1; $wall = -1; $cad = -1
    $sumRes = 0.0; $recFetch = -1; $rho = -1; $eqChk = 0; $causDec = 0; $status = "started"
    Write-Host "########## RHO-SPACING settle=${settleSec}s rep=$rep RunId=$RunId ##########"
    $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
    $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = [string]$RecoverMs; $env:SUI_CONSENSUS_CERTIFICATE_GATE = "0"
    try {
        & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $prepare `
            -RunId $RunId -Seed $Seed -Scenario "p0_rho_spacing" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
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
        # --- Fault 1 ---
        $tr1 = Invoke-RotationFault $net $v1 $v2 $v3 $v4 $v1ip $v2ip $v3ip $v4ip $GapSeconds $ResumeCapSeconds $ResumeThreshold
        $sumRes += [double]$tr1
        Write-Host "    fault 1/2 : t_resume=$($tr1)s"
        # --- SETTLE (the swept variable) ---
        Start-Sleep -Seconds $settleSec
        # --- Fault 2 ---
        $tr2 = Invoke-RotationFault $net $v1 $v2 $v3 $v4 $v1ip $v2ip $v3ip $v4ip $GapSeconds $ResumeCapSeconds $ResumeThreshold
        $sumRes += [double]$tr2
        Write-Host "    fault 2/2 : t_resume=$($tr2)s"

        $cpEnd = Get-Ckpt; $wall = [Math]::Round(((Get-Date) - $tSpanStart).TotalSeconds, 1)
        $commits = $cpEnd - $cpStart
        $cad = if ($wall -gt 0) { [Math]::Round($commits / $wall, 4) } else { -1 }
        $rho = if ($commits -gt 0) { [Math]::Round($N / [double]$commits, 8) } else { -1 }
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
    $row = "$N,$settleSec,$rep,$RunId,$cpStart,$cpEnd,$commits,$wall,$cad,$sumRes,$recFetch,$rho,$eqChk,$causDec,$status"
    Add-Content -Path $csv -Value $row -Encoding UTF8
    Write-Host "ROW: $row"
    Start-Sleep -Seconds 15
  }
}
Write-Host "########## RHO SPACING DONE -> $csv ##########"
