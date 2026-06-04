param(
    [string]$MatrixPath = "",
    [int]$Seed = 20260524,
    [int]$MaxRuns = 0,
    [string]$SuiImage = "stage7-sui:local",
    [switch]$StartCompose,
    [switch]$ContinueOnFailure,
    [int]$FullnodeRpcPort = 9000,
    [int]$WarmupTimeoutSeconds = 300,
    [int]$WarmupProbeSamples = 5,
    [int]$FaultProbeSamples = 5,
    [int]$RecoveryProbeSamples = 5,
    [int]$ProbeIntervalSeconds = 2,
    [double]$WorkloadTps = 1,
    [int]$WorkloadDurationSeconds = 60,
    [int]$WorkloadTimeoutSeconds = 90,
    [int]$InterRunCooldownSeconds = 5
)

$ErrorActionPreference = "Stop"

function Get-ComposeCommand {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($null -ne $docker) {
        $previousErrorActionPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = "Continue"
            & docker compose version > $null 2> $null
            if ($LASTEXITCODE -eq 0) {
                return @("docker", "compose")
            }
        }
        finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }
    }
    if ($null -ne (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        return @("docker-compose")
    }
    throw "Neither 'docker compose' nor 'docker-compose' is available."
}

function Invoke-Compose {
    param(
        [string[]]$ComposeCommand,
        [string[]]$Arguments
    )
    if ($ComposeCommand.Length -eq 1) {
        & $ComposeCommand[0] @Arguments
    }
    else {
        & $ComposeCommand[0] @($ComposeCommand[1..($ComposeCommand.Length - 1)] + $Arguments)
    }
}

function Convert-YamlScalar {
    param([string]$Value)
    $trimmed = $Value.Trim()
    if ($trimmed -eq "[]") {
        return @()
    }
    if ($trimmed -match '^"(.*)"$' -or $trimmed -match "^'(.*)'$") {
        return $Matches[1]
    }
    if ($trimmed -match "^-?[0-9]+$") {
        return [int]$trimmed
    }
    if ($trimmed -match "^-?[0-9]+\.[0-9]+$") {
        return [double]$trimmed
    }
    return $trimmed
}

function Read-Scenarios {
    param([string]$Path)
    $scenarios = @()
    $current = $null
    $currentFault = $null

    foreach ($line in Get-Content -Encoding UTF8 $Path) {
        if ($line -match "^\s*-\s+name:\s+([A-Za-z0-9_-]+)\s*$") {
            if ($null -ne $currentFault) {
                $current.faults += $currentFault
                $currentFault = $null
            }
            if ($null -ne $current) {
                $scenarios += $current
            }
            $current = [ordered]@{
                name = $Matches[1]
                repeats = 1
                faults = @()
            }
        }
        elseif ($null -ne $current -and $line -match "^\s+repeats:\s+([0-9]+)\s*$") {
            $current.repeats = [int]$Matches[1]
        }
        elseif ($null -ne $current -and $line -match "^\s+faults:\s*\[\]\s*$") {
            $current.faults = @()
        }
        elseif ($null -ne $current -and $line -match "^\s+-\s+action:\s+(.+?)\s*$") {
            if ($null -ne $currentFault) {
                $current.faults += $currentFault
            }
            $currentFault = [ordered]@{
                action = Convert-YamlScalar $Matches[1]
            }
        }
        elseif ($null -ne $currentFault -and $line -match "^\s+([A-Za-z0-9_]+):\s+(.+?)\s*$") {
            $currentFault[$Matches[1]] = Convert-YamlScalar $Matches[2]
        }
    }

    if ($null -ne $currentFault) {
        $current.faults += $currentFault
    }
    if ($null -ne $current) {
        $scenarios += $current
    }
    return $scenarios
}

function New-UtcIso {
    return [DateTime]::UtcNow.ToString("o").Replace("+00:00", "Z")
}

function Write-JsonFile {
    param(
        [object]$Value,
        [string]$Path
    )
    New-Item -ItemType Directory -Force (Split-Path $Path -Parent) | Out-Null
    $Value | ConvertTo-Json -Depth 30 | Set-Content -Path $Path -Encoding UTF8
}

function Invoke-ExternalCommand {
    param(
        [string]$Label,
        [string]$FilePath,
        [string[]]$Arguments
    )
    Write-Host "[$Label] $FilePath $($Arguments -join ' ')"
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Wait-RpcCheckpoint {
    param(
        [string]$Endpoint,
        [int]$MinimumCheckpoint,
        [int]$TimeoutSeconds
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $body = @{
        jsonrpc = "2.0"
        id = 1
        method = "sui_getLatestCheckpointSequenceNumber"
    } | ConvertTo-Json -Compress

    do {
        try {
            $response = Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType "application/json" -Body $body -TimeoutSec 5
            if ($null -ne $response.result) {
                $checkpoint = [int64]$response.result
                if ($checkpoint -ge $MinimumCheckpoint) {
                    Write-Host "RPC checkpoint ready at $checkpoint"
                    return $checkpoint
                }
            }
        }
        catch {
            Write-Host "Waiting for RPC checkpoint: $($_.Exception.Message)"
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    throw "RPC endpoint did not reach checkpoint $MinimumCheckpoint within $TimeoutSeconds seconds: $Endpoint"
}

function Invoke-RpcProbe {
    param(
        [string]$RunId,
        [string]$RunRoot,
        [string]$Endpoint,
        [string]$Phase,
        [int]$Samples,
        [int]$IntervalSeconds,
        [string]$ToolPath
    )
    $output = Join-Path $RunRoot "evidence\rpc_probe\$Phase.jsonl"
    Invoke-ExternalCommand -Label "rpc probe $Phase" -FilePath "python" -Arguments @(
        $ToolPath,
        "--run-id", $RunId,
        "--endpoint", $Endpoint,
        "--samples", [string]$Samples,
        "--interval-seconds", [string]$IntervalSeconds,
        "--output", $output
    )
}

function Invoke-Workload {
    param(
        [string]$RunId,
        [string]$RunRoot,
        [string]$DataRoot,
        [int]$Seed,
        [string]$SuiImage,
        [double]$Tps,
        [int]$DurationSeconds,
        [int]$TimeoutSeconds,
        [string]$ToolPath
    )
    $output = Join-Path $RunRoot "evidence\workload\actual_transfers.jsonl"
    Invoke-ExternalCommand -Label "actual-transfer workload" -FilePath "python" -Arguments @(
        $ToolPath,
        "--run-id", $RunId,
        "--seed", [string]$Seed,
        "--mode", "actual-transfer",
        "--data-root", $DataRoot,
        "--sui-image", $SuiImage,
        "--docker-network", "${RunId}_net",
        "--tps", [string]$Tps,
        "--duration-seconds", [string]$DurationSeconds,
        "--timeout-seconds", [string]$TimeoutSeconds,
        "--output", $output
    )
}

function Add-FaultEvent {
    param(
        [string]$TimelinePath,
        [string]$RunId,
        [string]$EventType,
        [string]$Action,
        [string]$Target,
        [string]$Status,
        [string]$Detail,
        [hashtable]$ExtraPayload = @{}
    )
    New-Item -ItemType Directory -Force (Split-Path $TimelinePath -Parent) | Out-Null
    $payload = [ordered]@{
        action = $Action
        target = $Target
        status = $Status
        detail = $Detail
    }
    foreach ($key in $ExtraPayload.Keys) {
        $payload[$key] = $ExtraPayload[$key]
    }
    $event = [ordered]@{
        ts = New-UtcIso
        run_id = $RunId
        source = "fault_timeline"
        event_type = $EventType
        payload = $payload
        evidence_ref = "$RunId/fault_timeline/$EventType/$Action/$Target"
    }
    ($event | ConvertTo-Json -Compress -Depth 12) | Add-Content -Path $TimelinePath -Encoding UTF8
}

function Resolve-FaultTarget {
    param(
        [string]$RunId,
        [string]$Target
    )
    if ($Target.StartsWith("$RunId-")) {
        return $Target
    }
    return "$RunId-$Target"
}

function Invoke-StartFaults {
    param(
        [object[]]$Faults,
        [string]$RunId,
        [string]$RunRoot
    )
    $timeline = Join-Path $RunRoot "evidence\fault_timeline.jsonl"
    $activePauseFaults = @()

    foreach ($fault in $Faults) {
        $action = [string]$fault.action
        if (-not $action) {
            continue
        }
        $target = Resolve-FaultTarget -RunId $RunId -Target ([string]$fault.target)

        switch ($action) {
            "netem_delay" {
                $delayMs = [int]$fault.delay_ms
                $jitterMs = [int]$fault.jitter_ms
                & docker exec $target sh -c "tc qdisc replace dev eth0 root netem delay ${delayMs}ms ${jitterMs}ms" > $null
                if ($LASTEXITCODE -ne 0) {
                    throw "netem_delay failed for $target"
                }
                Add-FaultEvent -TimelinePath $timeline -RunId $RunId -EventType "fault_applied" -Action $action -Target $target -Status "applied" -Detail "delay=${delayMs}ms jitter=${jitterMs}ms"
            }
            "netem_loss" {
                $lossPercent = [double]$fault.loss_percent
                & docker exec $target sh -c "tc qdisc replace dev eth0 root netem loss ${lossPercent}%" > $null
                if ($LASTEXITCODE -ne 0) {
                    throw "netem_loss failed for $target"
                }
                Add-FaultEvent -TimelinePath $timeline -RunId $RunId -EventType "fault_applied" -Action $action -Target $target -Status "applied" -Detail "loss=${lossPercent}%"
            }
            "pause_container" {
                $durationSeconds = [int]$fault.duration_seconds
                $startedAt = Get-Date
                & docker pause $target > $null
                if ($LASTEXITCODE -ne 0) {
                    throw "pause_container failed for $target"
                }
                Add-FaultEvent -TimelinePath $timeline -RunId $RunId -EventType "fault_applied" -Action $action -Target $target -Status "paused" -Detail "duration=${durationSeconds}s"
                $activePauseFaults += [ordered]@{
                    action = $action
                    target = $target
                    duration_seconds = $durationSeconds
                    started_at = $startedAt
                    timeline = $timeline
                }
            }
            default {
                throw "Unsupported fault action: $action"
            }
        }
    }

    return ,$activePauseFaults
}

function Complete-PauseFaults {
    param(
        [object[]]$ActiveFaults,
        [string]$RunId
    )
    foreach ($fault in $ActiveFaults) {
        $startedAt = [DateTime]$fault["started_at"]
        $durationSeconds = [double]$fault["duration_seconds"]
        $target = [string]$fault["target"]
        $timeline = [string]$fault["timeline"]
        $action = [string]$fault["action"]
        $elapsed = ((Get-Date) - $startedAt).TotalSeconds
        $remaining = [int][Math]::Ceiling($durationSeconds - $elapsed)
        if ($remaining -gt 0) {
            Start-Sleep -Seconds $remaining
        }
        & docker unpause $target > $null
        if ($LASTEXITCODE -ne 0) {
            throw "docker unpause failed for $target"
        }
        $recoveryMs = [int](((Get-Date) - $startedAt).TotalMilliseconds)
        Add-FaultEvent -TimelinePath $timeline -RunId $RunId -EventType "recovery_complete" -Action $action -Target $target -Status "unpaused" -Detail "docker unpause after pause fault" -ExtraPayload @{ recovery_time_ms = $recoveryMs }
    }
}

function Write-ControllerRecord {
    param(
        [object]$Record,
        [string]$RunRoot
    )
    Write-JsonFile -Value $Record -Path (Join-Path $RunRoot "controller_record.json")
}

$mvRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $MatrixPath) {
    $MatrixPath = Join-Path $mvRoot "config\experiment_matrix.yaml"
}
$composeFile = Join-Path $mvRoot "compose\compose.multivalidator.yaml"
$prepareScript = Join-Path $mvRoot "scripts\prepare_multivalidator.ps1"
$collectStateScript = Join-Path $mvRoot "scripts\collect_container_state.ps1"
$stopScript = Join-Path $mvRoot "scripts\stop_multivalidator.ps1"
$rpcProbeTool = Join-Path $mvRoot "tools\rpc_probe.py"
$workloadTool = Join-Path $mvRoot "tools\run_workload.py"
$metricsTool = Join-Path $mvRoot "tools\extract_consensus_metrics.py"
$collectEvidenceTool = Join-Path $mvRoot "tools\collect_evidence.py"
$validateManifestTool = Join-Path $mvRoot "tools\validate_manifest.py"
$dataRoot = Join-Path $mvRoot "data"
$rpcEndpoint = "http://127.0.0.1:$FullnodeRpcPort"

$matrix = Read-Scenarios -Path $MatrixPath
$plan = [System.Collections.Generic.List[object]]::new()

foreach ($scenario in $matrix) {
    for ($repeat = 1; $repeat -le $scenario.repeats; $repeat++) {
        $runId = "$($scenario.name)_seed$($Seed)_rep$($repeat.ToString("00"))"
        $plan.Add([ordered]@{
            run_id = $runId
            scenario = $scenario.name
            repeat_index = $repeat
            seed = $Seed
            faults = @($scenario.faults)
            status = "planned"
            run_root = "data/runs/$runId"
        })
    }
}

$planPath = Join-Path $mvRoot "data\runs\experiment_matrix_plan.json"
$statusPath = Join-Path $mvRoot "data\runs\experiment_matrix_status.json"
Write-JsonFile -Value $plan -Path $planPath
Write-Host "Wrote serial experiment plan: $planPath"

if ($MaxRuns -le 0) {
    Write-Host "MaxRuns is 0; no runs launched. Increase -MaxRuns to execute the serial controller."
    return
}

$composeCommand = Get-ComposeCommand
$launched = 0

foreach ($entry in $plan) {
    if ($launched -ge $MaxRuns) {
        break
    }

    $runId = [string]$entry.run_id
    $runRoot = Join-Path $mvRoot "data\runs\$runId"
    $record = [ordered]@{
        schema_version = 1
        run_id = $runId
        seed = $entry.seed
        scenario = $entry.scenario
        repeat_index = $entry.repeat_index
        faults = @($entry.faults)
        status = "running"
        started_at = New-UtcIso
        ended_at = $null
        error = $null
    }
    $entry["status"] = "running"
    $entry["started_at"] = $record.started_at
    Write-JsonFile -Value $plan -Path $statusPath
    Write-ControllerRecord -Record $record -RunRoot $runRoot

    $composeStarted = $false
    try {
        Invoke-ExternalCommand -Label "prepare $runId" -FilePath "powershell" -Arguments @(
            "-ExecutionPolicy", "Bypass",
            "-File", $prepareScript,
            "-RunId", $runId,
            "-Seed", [string]$Seed,
            "-Scenario", [string]$entry.scenario,
            "-RepeatIndex", [string]$entry.repeat_index,
            "-SuiImage", $SuiImage
        )

        if ($StartCompose) {
            $env:RUN_ID = $runId
            $env:SUI_IMAGE = $SuiImage
            $env:FULLNODE_RPC_PORT = [string]$FullnodeRpcPort
            Invoke-Compose -ComposeCommand $composeCommand -Arguments @("-f", $composeFile, "up", "-d")
            if ($LASTEXITCODE -ne 0) {
                throw "compose up failed for $runId"
            }
            $composeStarted = $true

            Wait-RpcCheckpoint -Endpoint $rpcEndpoint -MinimumCheckpoint 1 -TimeoutSeconds $WarmupTimeoutSeconds | Out-Null
            Invoke-RpcProbe -RunId $runId -RunRoot $runRoot -Endpoint $rpcEndpoint -Phase "warmup" -Samples $WarmupProbeSamples -IntervalSeconds $ProbeIntervalSeconds -ToolPath $rpcProbeTool

            $activePauseFaults = Invoke-StartFaults -Faults @($entry.faults) -RunId $runId -RunRoot $runRoot
            Invoke-RpcProbe -RunId $runId -RunRoot $runRoot -Endpoint $rpcEndpoint -Phase "fault_window" -Samples $FaultProbeSamples -IntervalSeconds $ProbeIntervalSeconds -ToolPath $rpcProbeTool
            Invoke-Workload -RunId $runId -RunRoot $runRoot -DataRoot $dataRoot -Seed $Seed -SuiImage $SuiImage -Tps $WorkloadTps -DurationSeconds $WorkloadDurationSeconds -TimeoutSeconds $WorkloadTimeoutSeconds -ToolPath $workloadTool
            Complete-PauseFaults -ActiveFaults @($activePauseFaults) -RunId $runId
            Invoke-RpcProbe -RunId $runId -RunRoot $runRoot -Endpoint $rpcEndpoint -Phase "recovery" -Samples $RecoveryProbeSamples -IntervalSeconds $ProbeIntervalSeconds -ToolPath $rpcProbeTool
        }

        $record.status = if ($StartCompose) { "completed" } else { "prepared" }
        $entry["status"] = $record.status
    }
    catch {
        $record.status = "failed"
        $record.error = $_.Exception.Message
        $entry["status"] = "failed"
        $entry["error"] = $_.Exception.Message
        Write-Warning $_.Exception.Message
        if (-not $ContinueOnFailure) {
            throw
        }
    }
    finally {
        if ($composeStarted) {
            try {
                Invoke-ExternalCommand -Label "collect container state $runId" -FilePath "powershell" -Arguments @(
                    "-ExecutionPolicy", "Bypass",
                    "-File", $collectStateScript,
                    "-RunId", $runId
                )
            }
            catch {
                $record.container_state_warning = $_.Exception.Message
            }

            try {
                Invoke-ExternalCommand -Label "stop $runId" -FilePath "powershell" -Arguments @(
                    "-ExecutionPolicy", "Bypass",
                    "-File", $stopScript,
                    "-RunId", $runId
                )
            }
            catch {
                $record.stop_warning = $_.Exception.Message
            }
        }

        $metricsJson = Join-Path $runRoot "metrics\consensus_metrics.json"
        $metricsCsv = Join-Path $runRoot "metrics\consensus_metrics.csv"
        try {
            Invoke-ExternalCommand -Label "extract metrics $runId" -FilePath "python" -Arguments @(
                $metricsTool,
                "--run-root", $runRoot,
                "--output-json", $metricsJson,
                "--output-csv", $metricsCsv
            )
        }
        catch {
            $record.metrics_warning = $_.Exception.Message
            if ($record.status -ne "failed") {
                $record.status = "failed"
                $entry["status"] = "failed"
                $entry["error"] = $_.Exception.Message
            }
            if (-not $ContinueOnFailure) {
                Write-ControllerRecord -Record $record -RunRoot $runRoot
                Write-JsonFile -Value $plan -Path $statusPath
                throw
            }
        }

        $record.ended_at = New-UtcIso
        $entry["ended_at"] = $record.ended_at
        Write-ControllerRecord -Record $record -RunRoot $runRoot
        Write-JsonFile -Value $plan -Path $statusPath

        $manifestPath = Join-Path $runRoot "manifest.json"
        try {
            Invoke-ExternalCommand -Label "collect evidence manifest $runId" -FilePath "python" -Arguments @(
                $collectEvidenceTool,
                "--run-root", $runRoot,
                "--output-manifest", $manifestPath
            )
            Invoke-ExternalCommand -Label "validate evidence manifest $runId" -FilePath "python" -Arguments @(
                $validateManifestTool,
                "--manifest", $manifestPath,
                "--root", $runRoot
            )
        }
        catch {
            $record.manifest_warning = $_.Exception.Message
            if ($record.status -ne "failed") {
                $record.status = "failed"
                $entry["status"] = "failed"
                $entry["error"] = $_.Exception.Message
            }
            if (-not $ContinueOnFailure) {
                Write-ControllerRecord -Record $record -RunRoot $runRoot
                Write-JsonFile -Value $plan -Path $statusPath
                throw
            }
        }
    }

    $launched++
    if ($InterRunCooldownSeconds -gt 0 -and $launched -lt $MaxRuns) {
        Start-Sleep -Seconds $InterRunCooldownSeconds
    }
}
