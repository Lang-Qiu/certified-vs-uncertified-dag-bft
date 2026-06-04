# Phase A critical-path Δ_recover harness — n=4 cross-scale replication of phaseA_criticalpath_partition.ps1.
#
# n=4 (f=1, quorum=3) rotation:
#   GAP={v1}  cut first -> carriers {v2,v3,v4}=3=quorum progress, gap opens on v1 (>= push window -> forces pull)
#   ROTATE: heal {v1} AND cut {v2} back-to-back -> current {v3,v4}=2 < quorum.
#           Network STALLS until v1 finishes PULLing its gap (Δ_recover-gated) and rejoins -> 3.
#   Observable t_resume = wall-clock from rotation until checkpoint advances again -> scales with Δ_recover.
#
# Same robustness as the n=7 harness (dynamic warmup/resume-watch, incremental CSV, continue-on-error).
# Output: data/runs/phaseA_criticalpath_n4_summary.csv columns
#   recover_ms,rep,run_id,cp_before,cp_gap,cp_rot,t_resume_s,v1_fetches,status
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$RecoverMsList = @(0, 250, 500, 1000),
    [int]$Reps = 3,
    [int]$GapSeconds = 90,
    [int]$WarmupCapSeconds = 150,
    [int]$ResumeCapSeconds = 200,
    [int]$ResumeThreshold = 8,
    [int]$Seed = 20260531
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.n4.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator_n4.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator_n4.ps1"
$csv = Join-Path $mv "data\runs\phaseA_criticalpath_n4_summary.csv"
if (-not (Test-Path $csv)) {
    "recover_ms,rep,run_id,cp_before,cp_gap,cp_rot,t_resume_s,v1_fetches,status" | Set-Content -Path $csv -Encoding UTF8
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
    $RunId = "phaseAcp_n4_ms${ms}_r${rep}"
    $net = "${RunId}_net"
    $v1 = "${RunId}-validator-1"; $v2 = "${RunId}-validator-2"
    $v1ip = "172.28.4.11"
    $cpBefore = -1; $cpGap = -1; $cpRot = -1; $tResume = -1; $f1 = -1; $status = "started"
    Write-Host "########## CRITPATH-n4 RECOVER_MS=$ms rep=$rep RunId=$RunId ##########"
    $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
    $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = [string]$ms; $env:SUI_CONSENSUS_CERTIFICATE_GATE = "0"
    try {
        & powershell -ExecutionPolicy Bypass -File $prepare -RunId $RunId -Seed $Seed -Scenario "critpath_rot_n4" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "prepare failed" }
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $null = & docker-compose -f $compose up -d 2>&1
        $code = [int]$LASTEXITCODE; $ErrorActionPreference = $prev
        if ($code -ne 0) { throw "compose up failed ($code)" }

        # dynamic warmup
        $t0 = Get-Date; $stable = $false; $last = -1
        while (((Get-Date) - $t0).TotalSeconds -lt $WarmupCapSeconds) {
            Start-Sleep -Seconds 8
            $c = Get-Ckpt
            if ($c -ge 30 -and $last -ge 0 -and ($c - $last) -ge 20) { $stable = $true; break }
            $last = $c
        }
        if (-not $stable) { throw "warmup did not stabilize (last cp=$last)" }
        $cpBefore = Get-Ckpt

        # phase GAP: cut v1 ; carriers v2,v3,v4 = 3 = quorum keep progressing
        & docker network disconnect $net $v1 2>&1 | Out-Null
        Start-Sleep -Seconds $GapSeconds
        $cpGap = Get-Ckpt
        if ($cpGap -lt 0 -or ($cpGap - $cpBefore) -lt 20) { throw "gap did not open (cpBefore=$cpBefore cpGap=$cpGap)" }

        # ROTATE: heal v1 AND cut v2 -> current {v3,v4}=2 < quorum
        & docker network connect --ip $v1ip $net $v1 2>&1 | Out-Null
        & docker network disconnect $net $v2 2>&1 | Out-Null
        $tRot = Get-Date
        Start-Sleep -Seconds 3
        $cpRot = Get-Ckpt

        # RESUME-WATCH
        $resumed = $false
        while (((Get-Date) - $tRot).TotalSeconds -lt $ResumeCapSeconds) {
            Start-Sleep -Seconds 3
            $c = Get-Ckpt
            if ($c -ge 0 -and ($c - $cpRot) -ge $ResumeThreshold) {
                $tResume = [Math]::Round(((Get-Date) - $tRot).TotalSeconds, 1); $resumed = $true; break
            }
        }
        $f1 = Get-FetchCount $v1
        if ($resumed) { $status = "ok" } else { $tResume = $ResumeCapSeconds; $status = "stall_timeout" }

        # heal the rotated node
        & docker network connect $net $v2 2>&1 | Out-Null
    }
    catch { $status = "fail:" + $_.Exception.Message.Replace(",",";") }
    finally {
        & powershell -ExecutionPolicy Bypass -File $stop -RunId $RunId | Out-Null
    }
    $row = "$ms,$rep,$RunId,$cpBefore,$cpGap,$cpRot,$tResume,$f1,$status"
    Add-Content -Path $csv -Value $row -Encoding UTF8
    Write-Host "  -> $row"
    Start-Sleep -Seconds 6
  }
}
Write-Host "########## CRITPATH-n4 DONE -> $csv ##########"
