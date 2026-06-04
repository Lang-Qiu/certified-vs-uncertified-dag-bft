# Partition pull test (stage9): force PULL-based recovery so the Δ_recover knob fires.
# Unlike `docker pause` (holds TCP open -> peers replay backlog = PUSH catch-up), a network
# disconnect SEVERS connections; on reconnect peers send current blocks whose ancestors v1 lacks,
# forcing v1 to FETCH the gap (synchronizer::process_fetched_blocks / commit_syncer::fetch_once).
# With instrumentation, every such fetch logs "STAGE9_RECOVERY ... delay_ms=<n>".
#
# Reuses stage7 prepare/stop + base compose. Self-contained; teardown in finally.
param(
    [string]$RunId = "partition_pull_test",
    [string]$SuiImage = "stage9-sui-certgate:local",
    [int]$RecoverMs = 1000,
    [int]$WarmupSeconds = 75,
    [int]$PartitionSeconds = 80,
    [int]$RecoverWatchSeconds = 60,
    [int]$Seed = 20260531
)
$ErrorActionPreference = "Stop"
$mv = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator"
$compose = Join-Path $mv "compose\compose.multivalidator.yaml"
$prepare = Join-Path $mv "scripts\prepare_multivalidator.ps1"
$stop = Join-Path $mv "scripts\stop_multivalidator.ps1"
$runRoot = Join-Path $mv "data\runs\$RunId"
$net = "${RunId}_net"
$v1 = "${RunId}-validator-1"
$v1ip = "172.28.7.11"

$env:RUN_ID = $RunId
$env:SUI_IMAGE = $SuiImage
$env:FULLNODE_RPC_PORT = "9000"
$env:SUI_CONSENSUS_RECOVERY_EXTRA_DELAY_MS = [string]$RecoverMs
$env:SUI_CONSENSUS_CERTIFICATE_GATE = "0"

function Get-Ckpt {
    try {
        $b = '{"jsonrpc":"2.0","id":1,"method":"sui_getLatestCheckpointSequenceNumber","params":[]}'
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:9000" -Method Post -ContentType "application/json" -Body $b -TimeoutSec 5
        return [int64]$r.result
    } catch { return -1 }
}

try {
    Write-Host "=== prepare genesis ($RunId) ==="
    & powershell -ExecutionPolicy Bypass -File $prepare -RunId $RunId -Seed $Seed -Scenario "partition_v1" -RepeatIndex 1 -SuiImage $SuiImage
    if ($LASTEXITCODE -ne 0) { throw "prepare failed" }

    Write-Host "=== compose up ==="
    $prevEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    $out = & docker-compose -f $compose up -d 2>&1
    $code = [int]$LASTEXITCODE
    $ErrorActionPreference = $prevEAP
    Write-Host ($out | Out-String)
    if ($code -ne 0) { throw "compose up failed ($code)" }

    Write-Host "=== warmup ${WarmupSeconds}s ==="
    Start-Sleep -Seconds $WarmupSeconds
    $before = Get-Ckpt
    Write-Host "  checkpoint before partition: $before"

    Write-Host "=== PARTITION v1 (network disconnect) for ${PartitionSeconds}s ==="
    & docker network disconnect $net $v1
    if ($LASTEXITCODE -ne 0) { throw "disconnect failed" }
    Start-Sleep -Seconds $PartitionSeconds
    $during = Get-Ckpt
    Write-Host "  checkpoint during partition (network advancing without v1): $during"

    Write-Host "=== HEAL v1 (network connect, re-assign $v1ip) ==="
    & docker network connect --ip $v1ip $net $v1
    if ($LASTEXITCODE -ne 0) { throw "connect failed" }
    Write-Host "=== watch recovery ${RecoverWatchSeconds}s ==="
    Start-Sleep -Seconds $RecoverWatchSeconds
    $after = Get-Ckpt
    Write-Host "  checkpoint after heal+watch: $after"

    Write-Host "=== capture v1 log + grep STAGE9_RECOVERY ==="
    $logDir = Join-Path $runRoot "partition_logs"
    New-Item -ItemType Directory -Force $logDir | Out-Null
    foreach ($n in 1..7) {
        $c = "${RunId}-validator-$n"
        $lp = Join-Path $logDir "$c.log"
        $prevEAP = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        $ll = & docker logs --timestamps $c 2>&1
        $ErrorActionPreference = $prevEAP
        ($ll | Out-String) | Set-Content -Path $lp -Encoding UTF8
        $hits = (Select-String -Path $lp -Pattern "STAGE9_RECOVERY" -ErrorAction SilentlyContinue | Measure-Object).Count
        Write-Host "  validator-$n : STAGE9_RECOVERY hits = $hits"
    }
    Write-Host "=== sample STAGE9_RECOVERY lines (v1) ==="
    $v1log = Join-Path $logDir "$v1.log"
    Select-String -Path $v1log -Pattern "STAGE9_RECOVERY" -ErrorAction SilentlyContinue | Select-Object -First 6 | ForEach-Object { Write-Host "  $($_.Line.Substring(0,[Math]::Min(150,$_.Line.Length)))" }
}
finally {
    Write-Host "=== teardown ==="
    & powershell -ExecutionPolicy Bypass -File $stop -RunId $RunId
}
