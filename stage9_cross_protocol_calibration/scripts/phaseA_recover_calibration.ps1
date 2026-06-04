# Phase A robust Δ_recover calibration harness.
# Fault model: network partition (docker disconnect/reconnect) forces PULL recovery on validator-1,
# which fires the STAGE9_RECOVERY knob (see PHASEA_SMOKE_FINDINGS.md). Sweeps RECOVER_MS x reps.
#
# Robustness over the ad-hoc partition_pull_test.ps1:
#  - dynamic warmup: poll RPC until checkpoint advances steadily (stable commit production)
#  - dynamic watch:  after heal, poll v1's STAGE9_RECOVERY count until it quiesces (catch-up done)
#                    or a hard cap, so slow high-delay catch-up is fully captured
#  - >=3 reps/level, incremental CSV (partial results survive a crash), continue-on-error
#
# Output: data/runs/phaseA_calibration_summary.csv with columns
#   recover_ms,rep,run_id,cp_before,cp_during,gap,fetches,catchup_s,status
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$RecoverMsList = @(0, 250, 500, 1000),
    [int]$Reps = 3,
    [int]$PartitionSeconds = 80,
    [int]$WarmupCapSeconds = 150,
    [int]$WatchCapSeconds = 200,
    [int]$QuiesceSeconds = 20,
    [int]$Seed = 20260531
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$csv = Join-Path $mv "data\runs\phaseA_calibration_summary.csv"
if (-not (Test-Path $csv)) {
    "recover_ms,rep,run_id,cp_before,cp_during,gap,fetches,catchup_s,status" | Set-Content -Path $csv -Encoding UTF8
}

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

foreach ($ms in $RecoverMsList) {
  foreach ($rep in 1..$Reps) {
    $RunId = "phaseAcal_ms${ms}_r${rep}"
    $net = "${RunId}_net"; $v1 = "${RunId}-validator-1"; $v1ip = "172.28.7.11"
    $cpBefore = -1; $cpDuring = -1; $fetches = -1; $catchup = -1; $status = "started"
    Write-Host "########## RECOVER_MS=$ms rep=$rep RunId=$RunId ##########"
    $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
    $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = [string]$ms; $env:SUI_CONSENSUS_CERTIFICATE_GATE = "0"
    try {
        & powershell -ExecutionPolicy Bypass -File $prepare -RunId $RunId -Seed $Seed -Scenario "partition_cal" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "prepare failed" }
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $null = & docker-compose -f $compose up -d 2>&1
        $code = [int]$LASTEXITCODE; $ErrorActionPreference = $prev
        if ($code -ne 0) { throw "compose up failed ($code)" }

        # dynamic warmup: wait until checkpoint advances by >= 20 across two reads 8s apart
        $t0 = Get-Date; $stable = $false; $last = -1
        while (((Get-Date) - $t0).TotalSeconds -lt $WarmupCapSeconds) {
            Start-Sleep -Seconds 8
            $c = Get-Ckpt
            if ($c -ge 30 -and $last -ge 0 -and ($c - $last) -ge 20) { $stable = $true; break }
            $last = $c
        }
        if (-not $stable) { throw "warmup did not stabilize (last cp=$last)" }
        $cpBefore = Get-Ckpt

        # partition v1
        & docker network disconnect $net $v1 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "disconnect failed" }
        Start-Sleep -Seconds $PartitionSeconds
        $cpDuring = Get-Ckpt
        # heal
        & docker network connect --ip $v1ip $net $v1 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "connect failed" }
        $tHeal = Get-Date

        # dynamic watch: poll v1 fetch count until quiesced (no change for QuiesceSeconds) or cap
        $lastCnt = -1; $lastChange = Get-Date; $cnt = 0
        while (((Get-Date) - $tHeal).TotalSeconds -lt $WatchCapSeconds) {
            Start-Sleep -Seconds 5
            $cnt = Get-FetchCount $v1
            if ($cnt -ne $lastCnt) { $lastCnt = $cnt; $lastChange = Get-Date }
            elseif (((Get-Date) - $lastChange).TotalSeconds -ge $QuiesceSeconds -and $cnt -gt 0) { break }
        }
        $fetches = $cnt
        $catchup = [Math]::Round((($lastChange) - $tHeal).TotalSeconds, 1)
        $status = "ok"
    }
    catch { $status = "fail:" + $_.Exception.Message.Replace(",",";") }
    finally {
        & powershell -ExecutionPolicy Bypass -File $stop -RunId $RunId | Out-Null
    }
    $gap = if ($cpDuring -ge 0 -and $cpBefore -ge 0) { $cpDuring - $cpBefore } else { -1 }
    $row = "$ms,$rep,$RunId,$cpBefore,$cpDuring,$gap,$fetches,$catchup,$status"
    Add-Content -Path $csv -Value $row -Encoding UTF8
    Write-Host "  -> $row"
    Start-Sleep -Seconds 6
  }
}
Write-Host "########## CALIBRATION DONE -> $csv ##########"
