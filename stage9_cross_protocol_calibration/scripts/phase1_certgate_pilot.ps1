# Phase 1 pilot — Route A1 certified-arm sanity (fault-free Δ_save + liveness).
#
# GOAL (no fault injection): confirm the certificate-gate works on a real n=7 deployment:
#   (a) Δ_save > 0      : cert ON cadence < cert OFF cadence (the certification round costs latency)
#   (b) liveness        : cert ON cadence does NOT collapse to the prober-fallback degradation
#                         (i.e. it stays a healthy fraction of OFF, proving no deadlock)
#   (c) OFF ≈ stock     : cert OFF cadence ≈ the stage7 baseline (image-equivalence self-check)
#
# Both arms run the SAME fast prober (CertProberMs) so prober overhead cancels and the measured
# cadence gap isolates the reference-gate effect (= Δ_save). Δ_recover knob held at 0.
#
# Observable: steady-state checkpoint cadence (ckpt/s) over a window, via fullnode JSON-RPC.
# Interleaves arms per rep (OFF,ON,OFF,ON...) to control for daemon/host drift.
# Reuses stage7 prepare/stop + base compose + env-knob injection. Incremental CSV, continue-on-error.
# Output: data/runs/phase1_certgate_pilot_summary.csv
#   arm,cert_gate,rep,run_id,cp_start,cp_end,window_s,cadence_ckpt_s,status
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int]$CertProberMs = 75,         # fast independent ack channel on BOTH arms
    [int]$WindowSeconds = 90,        # steady-state cadence measurement window
    [int]$WarmupCapSeconds = 180,
    [int]$Reps = 2,
    [int]$Seed = 20260531
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$csv = Join-Path $mv "data\runs\phase1_certgate_pilot_summary.csv"
if (-not (Test-Path $csv)) {
    "arm,cert_gate,rep,run_id,cp_start,cp_end,window_s,cadence_ckpt_s,status" | Set-Content -Path $csv -Encoding UTF8
}

function Get-Ckpt {
    try {
        $b = '{"jsonrpc":"2.0","id":1,"method":"sui_getLatestCheckpointSequenceNumber","params":[]}'
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:9000" -Method Post -ContentType "application/json" -Body $b -TimeoutSec 5
        return [int64]$r.result
    } catch { return -1 }
}

# arms: name -> cert_gate value. Both fast-prober.
$arms = @(
    @{ name = "OFF"; gate = "0" },
    @{ name = "ON";  gate = "1" }
)

foreach ($rep in 1..$Reps) {
  foreach ($arm in $arms) {
    $g = $arm.gate; $aname = $arm.name
    $RunId = "phase1_${aname}_r${rep}"
    $cpStart = -1; $cpEnd = -1; $cadence = -1.0; $status = "started"
    Write-Host "########## PILOT arm=$aname cert_gate=$g rep=$rep RunId=$RunId ##########"
    $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
    $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = "0"
    $env:SUI_CONSENSUS_CERTIFICATE_GATE = $g
    $env:SUI_CONSENSUS_CERTIFICATE_PROBER_INTERVAL_MS = [string]$CertProberMs
    try {
        & powershell -ExecutionPolicy Bypass -File $prepare -RunId $RunId -Seed $Seed -Scenario "phase1_pilot" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "prepare failed" }
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $null = & docker-compose -f $compose up -d 2>&1
        $code = [int]$LASTEXITCODE; $ErrorActionPreference = $prev
        if ($code -ne 0) { throw "compose up failed ($code)" }

        # dynamic warmup: gentle (cert ON may be slower) — cp >= 20 AND advanced >= 5 over a 10s read.
        # A collapse to the prober fallback would FAIL to clear this within the cap -> flagged as a
        # liveness failure rather than silently measuring a degraded cadence.
        $t0 = Get-Date; $stable = $false; $last = -1
        while (((Get-Date) - $t0).TotalSeconds -lt $WarmupCapSeconds) {
            Start-Sleep -Seconds 10
            $c = Get-Ckpt
            if ($c -ge 20 -and $last -ge 0 -and ($c - $last) -ge 5) { $stable = $true; break }
            $last = $c
        }
        if (-not $stable) { throw "warmup did not stabilize (last cp=$last) — possible gate degradation" }

        # steady-state cadence over WindowSeconds
        $cpStart = Get-Ckpt
        Start-Sleep -Seconds $WindowSeconds
        $cpEnd = Get-Ckpt
        if ($cpStart -lt 0 -or $cpEnd -lt 0) { throw "rpc read failed (cpStart=$cpStart cpEnd=$cpEnd)" }
        $cadence = [Math]::Round(($cpEnd - $cpStart) / $WindowSeconds, 4)
        $status = "ok"
    }
    catch { $status = "fail:" + $_.Exception.Message.Replace(",",";") }
    finally {
        & powershell -ExecutionPolicy Bypass -File $stop -RunId $RunId | Out-Null
    }
    $row = "$aname,$g,$rep,$RunId,$cpStart,$cpEnd,$WindowSeconds,$cadence,$status"
    Add-Content -Path $csv -Value $row -Encoding UTF8
    Write-Host "  -> $row"
    Start-Sleep -Seconds 6
  }
}
Write-Host "########## PILOT DONE -> $csv ##########"
Write-Host "Interpret: cadence_ON < cadence_OFF => Δ_save>0; cadence_ON not collapsed => liveness OK."
