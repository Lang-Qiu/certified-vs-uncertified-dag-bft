# Phase 2c — clean decomposed ρ*(Δr) mapping (the §7.2 crossover, done right).
#
# The amortized-window observable (phase2b) diluted the one-time recovery cost into noise. This measures
# the recovery cost DIRECTLY and cleanly, per arm, as the §7.6.2 t_resume (wall-clock stall until cadence
# resumes after the critical-path rotation). Sweeping Δ_recover gives:
#   t_resume_OFF(Δr), t_resume_ON(Δr)  -> excess(Δr) = t_resume_OFF - t_resume_ON  (certified's recovery saving)
# Combined with the clean fault-free Δ_save rate (PHASE1: 0.116 s/commit):
#   ρ*(Δr) = Δ_save_rate / excess(Δr)   = the fault rate where the §7.2 advantage flips uncertified->certified.
# ρ* should fall (certified wins more easily) as Δr grows and excess grows.
#
# Same critical-path rotation as §7.6.2 / phase2_recovery_asymmetry, fast prober both arms.
# Output: data/runs/phase2c_excess_sweep_summary.csv
#   cert_gate,recover_ms,cert_prober_ms,rep,run_id,cp_before,cp_gap,cp_rot,t_resume_s,v1_fetches,v2_fetches,status
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$RecoverMsList = @(0, 500, 1000, 2000, 4000),
    [int]$CertProberMs = 75,
    [int]$Reps = 2,
    [int]$GapSeconds = 90,
    [int]$WarmupCapSeconds = 200,
    [int]$ResumeCapSeconds = 240,
    [int]$ResumeThreshold = 8,
    [int]$Seed = 20260531
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$csv = Join-Path $mv "data\runs\phase2c_excess_sweep_summary.csv"
if (-not (Test-Path $csv)) {
    "cert_gate,recover_ms,cert_prober_ms,rep,run_id,cp_before,cp_gap,cp_rot,t_resume_s,v1_fetches,v2_fetches,status" | Set-Content -Path $csv -Encoding UTF8
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

foreach ($rep in 1..$Reps) {
  foreach ($ms in $RecoverMsList) {
    foreach ($g in @("0", "1")) {
      $RunId = "p2c_g${g}_ms${ms}_r${rep}"
      $net = "${RunId}_net"
      $v1 = "${RunId}-validator-1"; $v2 = "${RunId}-validator-2"
      $v3 = "${RunId}-validator-3"; $v4 = "${RunId}-validator-4"
      $v1ip = "172.28.7.11"; $v2ip = "172.28.7.12"; $v3ip = "172.28.7.13"; $v4ip = "172.28.7.14"
      $cpBefore = -1; $cpGap = -1; $cpRot = -1; $tResume = -1; $f1 = -1; $f2 = -1; $status = "started"
      Write-Host "########## EXCESS cert=$g recover=$ms rep=$rep RunId=$RunId ##########"
      $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
      $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = [string]$ms
      $env:SUI_CONSENSUS_CERTIFICATE_GATE = $g
      $env:SUI_CONSENSUS_CERTIFICATE_PROBER_INTERVAL_MS = [string]$CertProberMs
      try {
          & powershell -ExecutionPolicy Bypass -File $prepare -RunId $RunId -Seed $Seed -Scenario "excess_rot" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
          if ($LASTEXITCODE -ne 0) { throw "prepare failed" }
          $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
          $null = & docker-compose -f $compose up -d 2>&1
          $code = [int]$LASTEXITCODE; $ErrorActionPreference = $prev
          if ($code -ne 0) { throw "compose up failed ($code)" }

          $t0 = Get-Date; $stable = $false; $last = -1
          while (((Get-Date) - $t0).TotalSeconds -lt $WarmupCapSeconds) {
              Start-Sleep -Seconds 10
              $c = Get-Ckpt
              if ($c -ge 20 -and $last -ge 0 -and ($c - $last) -ge 5) { $stable = $true; break }
              $last = $c
          }
          if (-not $stable) { throw "warmup did not stabilize (last cp=$last)" }
          $cpBefore = Get-Ckpt

          & docker network disconnect $net $v1 2>&1 | Out-Null
          & docker network disconnect $net $v2 2>&1 | Out-Null
          Start-Sleep -Seconds $GapSeconds
          $cpGap = Get-Ckpt
          if ($cpGap -lt 0 -or ($cpGap - $cpBefore) -lt 10) { throw "gap did not open (cpBefore=$cpBefore cpGap=$cpGap)" }

          & docker network connect --ip $v1ip $net $v1 2>&1 | Out-Null
          & docker network connect --ip $v2ip $net $v2 2>&1 | Out-Null
          & docker network disconnect $net $v3 2>&1 | Out-Null
          & docker network disconnect $net $v4 2>&1 | Out-Null
          $tRot = Get-Date
          Start-Sleep -Seconds 3
          $cpRot = Get-Ckpt

          $resumed = $false
          while (((Get-Date) - $tRot).TotalSeconds -lt $ResumeCapSeconds) {
              Start-Sleep -Seconds 3
              $c = Get-Ckpt
              if ($c -ge 0 -and ($c - $cpRot) -ge $ResumeThreshold) {
                  $tResume = [Math]::Round(((Get-Date) - $tRot).TotalSeconds, 1); $resumed = $true; break
              }
          }
          $f1 = Get-FetchCount $v1; $f2 = Get-FetchCount $v2
          if ($resumed) { $status = "ok" } else { $tResume = $ResumeCapSeconds; $status = "stall_timeout" }

          & docker network connect --ip $v3ip $net $v3 2>&1 | Out-Null
          & docker network connect --ip $v4ip $net $v4 2>&1 | Out-Null
      }
      catch { $status = "fail:" + $_.Exception.Message.Replace(",",";") }
      finally {
          & powershell -ExecutionPolicy Bypass -File $stop -RunId $RunId | Out-Null
      }
      $row = "$g,$ms,$CertProberMs,$rep,$RunId,$cpBefore,$cpGap,$cpRot,$tResume,$f1,$f2,$status"
      Add-Content -Path $csv -Value $row -Encoding UTF8
      Write-Host "  -> $row"
      Start-Sleep -Seconds 6
    }
  }
}
Write-Host "########## EXCESS SWEEP DONE -> $csv ##########"
