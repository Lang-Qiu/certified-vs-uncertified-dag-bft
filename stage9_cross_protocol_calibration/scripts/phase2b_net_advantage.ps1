# Phase 2b — joint net-advantage / §7.2 crossover on real n=7 Sui.
#
# Validates net_advantage = Δ_save - ρ·Δ_recover by sweeping Δ_recover at a FIXED one-rotation fault
# (ρ = 1 critical-path recovery per fixed window), for both arms (cert ON/OFF, fast prober).
# Model is symmetric in ρ and Δ_recover (product term), so sweeping the clean Δ_recover knob also
# traces the crossover. Pre-confirmed asymmetry (phase2_recovery_asymmetry): cert ON recovers cheaper.
#
# Observable: amortized checkpoint cadence over a FIXED window that contains exactly one rotation fault
# (gap -> rotate -> recover -> tail). Same topology timeline for both arms => fair comparison.
#   net_advantage(Δr) = lat_ON - lat_OFF = (1/cadence_ON) - (1/cadence_OFF).
#   Δr=0:  OFF faster (fault-free Δ_save dominates, recovery cheap)        => net_adv > 0 (uncertified wins)
#   Δr big: OFF pays huge recovery (more fetches × delay)                  => net_adv < 0 (certified wins)
#   crossover Δr* where they balance = the §7.2 reversal, on real deployment.
#
# Output: data/runs/phase2b_net_advantage_summary.csv
#   cert_gate,recover_ms,cert_prober_ms,rep,run_id,cp_before,cp_end,window_s,ckpts,cadence_ckpt_s,v1_fetches,v2_fetches,status
param(
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int[]]$RecoverMsList = @(0, 1000, 2000, 4000),
    [int]$CertProberMs = 75,
    [int]$Reps = 1,
    [int]$GapSeconds = 90,
    [int]$TailSeconds = 105,          # post-rotation tail (recovery ~40s + steady tail) -> window = 5+Gap+Tail
    [int]$WarmupCapSeconds = 200,
    [int]$Seed = 20260531
)
$ErrorActionPreference = "Continue"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$csv = Join-Path $mv "data\runs\phase2b_net_advantage_summary.csv"
if (-not (Test-Path $csv)) {
    "cert_gate,recover_ms,cert_prober_ms,rep,run_id,cp_before,cp_end,window_s,ckpts,cadence_ckpt_s,v1_fetches,v2_fetches,status" | Set-Content -Path $csv -Encoding UTF8
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

$windowS = 5 + $GapSeconds + $TailSeconds
foreach ($rep in 1..$Reps) {
  foreach ($ms in $RecoverMsList) {
    foreach ($g in @("0", "1")) {
      $RunId = "p2b_g${g}_ms${ms}_r${rep}"
      $net = "${RunId}_net"
      $v1 = "${RunId}-validator-1"; $v2 = "${RunId}-validator-2"
      $v3 = "${RunId}-validator-3"; $v4 = "${RunId}-validator-4"
      $v1ip = "172.28.7.11"; $v2ip = "172.28.7.12"; $v3ip = "172.28.7.13"; $v4ip = "172.28.7.14"
      $cpBefore = -1; $cpEnd = -1; $ckpts = -1; $cadence = -1.0; $f1 = -1; $f2 = -1; $status = "started"
      Write-Host "########## NETADV cert=$g recover=$ms rep=$rep RunId=$RunId ##########"
      $env:RUN_ID = $RunId; $env:SUI_IMAGE = $SuiImage; $env:FULLNODE_RPC_PORT = "9000"
      $env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = [string]$ms
      $env:SUI_CONSENSUS_CERTIFICATE_GATE = $g
      $env:SUI_CONSENSUS_CERTIFICATE_PROBER_INTERVAL_MS = [string]$CertProberMs
      try {
          & powershell -ExecutionPolicy Bypass -File $prepare -RunId $RunId -Seed $Seed -Scenario "netadv_rot" -RepeatIndex $rep -SuiImage $SuiImage | Out-Null
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

          # FIXED WINDOW [tWin, tWin+windowS] containing one rotation fault.
          $cpBefore = Get-Ckpt; $tWin = Get-Date
          Start-Sleep -Seconds 5
          & docker network disconnect $net $v1 2>&1 | Out-Null     # GAP: cut v1,v2
          & docker network disconnect $net $v2 2>&1 | Out-Null
          Start-Sleep -Seconds $GapSeconds
          & docker network connect --ip $v1ip $net $v1 2>&1 | Out-Null   # ROTATE: heal v1,v2 / cut v3,v4
          & docker network connect --ip $v2ip $net $v2 2>&1 | Out-Null
          & docker network disconnect $net $v3 2>&1 | Out-Null
          & docker network disconnect $net $v4 2>&1 | Out-Null
          # hold the rest of the fixed window (recovery + tail), then snapshot
          $elapsed = ((Get-Date) - $tWin).TotalSeconds
          if ($windowS - $elapsed -gt 0) { Start-Sleep -Seconds ([int]($windowS - $elapsed)) }
          $cpEnd = Get-Ckpt
          $f1 = Get-FetchCount $v1; $f2 = Get-FetchCount $v2
          & docker network connect --ip $v3ip $net $v3 2>&1 | Out-Null
          & docker network connect --ip $v4ip $net $v4 2>&1 | Out-Null
          if ($cpBefore -lt 0 -or $cpEnd -lt 0) { throw "rpc read failed (cpBefore=$cpBefore cpEnd=$cpEnd)" }
          $ckpts = $cpEnd - $cpBefore
          $cadence = [Math]::Round($ckpts / $windowS, 4)
          $status = "ok"
      }
      catch { $status = "fail:" + $_.Exception.Message.Replace(",",";") }
      finally {
          & powershell -ExecutionPolicy Bypass -File $stop -RunId $RunId | Out-Null
      }
      $row = "$g,$ms,$CertProberMs,$rep,$RunId,$cpBefore,$cpEnd,$windowS,$ckpts,$cadence,$f1,$f2,$status"
      Add-Content -Path $csv -Value $row -Encoding UTF8
      Write-Host "  -> $row"
      Start-Sleep -Seconds 6
    }
  }
}
Write-Host "########## NETADV DONE -> $csv ##########"
Write-Host "net_advantage(Δr) = 1/cadence_ON - 1/cadence_OFF; sign flip across Δr = the §7.2 crossover."
