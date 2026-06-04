# Phase 1b — Δ_save dose-response calibration (Route A1 certified arm).
#
# Sweeps the certification-channel latency (RoundProber interval) = the Δ_save magnitude knob.
# At each interval I, runs BOTH arms on the same prober so prober overhead cancels:
#   Δ_save(I) = latency_ON(I) - latency_OFF(I) = 1/cadence_ON(I) - 1/cadence_OFF(I).
# Larger I => the gate waits longer for the prober to confirm 2f+1 quorum-acceptance => larger Δ_save.
#
# Fault-free (Δ_recover=0). Observable: steady-state checkpoint cadence (ckpt/s) via fullnode RPC.
# Order: rep outer, interval, arm (OFF then ON) — spreads each cell across time to control daemon drift.
# Reuses stage7 prepare/stop + base compose + env-knob injection. Incremental CSV, continue-on-error.
# Output: data/runs/phase1b_dsave_calibration_summary.csv
#   cert_prober_ms,arm,cert_gate,rep,run_id,cp_start,cp_end,window_s,cadence_ckpt_s,status
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$CertProberMsList = @(75, 250, 500),
    [int]$WindowSeconds = 90,
    [int]$WarmupCapSeconds = 220,
    [int]$Reps = 2,
    [int]$Seed = 20260531
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$csv = Join-Path $mv "data\runs\phase1b_dsave_calibration_summary.csv"
if (-not (Test-Path $csv)) {
    "cert_prober_ms,arm,cert_gate,rep,run_id,cp_start,cp_end,window_s,cadence_ckpt_s,status" | Set-Content -Path $csv -Encoding UTF8
}

function Get-Ckpt {
    try {
        $b = '{"jsonrpc":"2.0","id":1,"method":"sui_getLatestCheckpointSequenceNumber","params":[]}'
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:9000" -Method Post -ContentType "application/json" -Body $b -TimeoutSec 5
        return [int64]$r.result
    } catch { return -1 }
}

$arms = @(@{ name = "OFF"; gate = "0" }, @{ name = "ON"; gate = "1" })

foreach ($rep in 1..$Reps) {
  foreach ($pms in $CertProberMsList) {
    foreach ($arm in $arms) {
      $g = $arm.gate; $aname = $arm.name
      $RunId = "p1b_${aname}_pm${pms}_r${rep}"
      $cpStart = -1; $cpEnd = -1; $cadence = -1.0; $status = "started"
      Write-Host "########## DSAVE pm=$pms arm=$aname rep=$rep RunId=$RunId ##########"
      $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
      $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = "0"
      $env:SUI_CONSENSUS_CERTIFICATE_GATE = $g
      $env:SUI_CONSENSUS_CERTIFICATE_PROBER_INTERVAL_MS = [string]$pms
      try {
          & powershell -ExecutionPolicy Bypass -File $prepare -RunId $RunId -Seed $Seed -Scenario "dsave_calib" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
          if ($LASTEXITCODE -ne 0) { throw "prepare failed" }
          $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
          $null = & docker-compose -f $compose up -d 2>&1
          $code = [int]$LASTEXITCODE; $ErrorActionPreference = $prev
          if ($code -ne 0) { throw "compose up failed ($code)" }

          # gentle dynamic warmup (cert ON + slow prober may be slow): cp>=20 AND +>=5 over a 10s read.
          # failing within the cap => possible gate degradation -> flagged, not silently measured.
          $t0 = Get-Date; $stable = $false; $last = -1
          while (((Get-Date) - $t0).TotalSeconds -lt $WarmupCapSeconds) {
              Start-Sleep -Seconds 10
              $c = Get-Ckpt
              if ($c -ge 20 -and $last -ge 0 -and ($c - $last) -ge 5) { $stable = $true; break }
              $last = $c
          }
          if (-not $stable) { throw "warmup did not stabilize (last cp=$last) - possible gate degradation" }

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
      $row = "$pms,$aname,$g,$rep,$RunId,$cpStart,$cpEnd,$WindowSeconds,$cadence,$status"
      Add-Content -Path $csv -Value $row -Encoding UTF8
      Write-Host "  -> $row"
      Start-Sleep -Seconds 6
    }
  }
}
Write-Host "########## DSAVE CALIBRATION DONE -> $csv ##########"
