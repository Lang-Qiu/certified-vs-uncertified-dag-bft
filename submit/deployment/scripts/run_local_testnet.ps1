param(
    [int]$TimeoutSeconds = 180,
    [string]$RpcUrl = "http://127.0.0.1:9000"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$composeDir = Join-Path $root "compose"
$envFile = Join-Path $composeDir ".env"
$envExample = Join-Path $composeDir ".env.example"
$composeFile = Join-Path $composeDir "compose.yaml"
$rawDir = Join-Path $root "data/raw"
$derivedDir = Join-Path $root "data/derived"

New-Item -ItemType Directory -Force -Path $rawDir, $derivedDir | Out-Null

function Invoke-NativeCommand {
    param(
        [string]$Description,
        [string]$FilePath,
        [string[]]$Arguments
    )

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & $FilePath @Arguments 2>&1 | ForEach-Object { $_.ToString() }
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    $outputText = ($output | Out-String).Trim()
    if ($exitCode -ne 0) {
        $joined = $Arguments -join " "
        throw "$Description failed (exit $exitCode): $FilePath $joined`n$outputText"
    }
    return $outputText
}

function Resolve-ComposeCommand {
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $pluginOutput = & docker compose version 2>&1
        $pluginExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    if ($pluginExit -eq 0) {
        return @{
            FilePath = "docker"
            Prefix = @("compose")
            Version = ($pluginOutput | Out-String).Trim()
        }
    }

    $standalone = Get-Command "docker-compose" -ErrorAction SilentlyContinue
    if (-not $standalone) {
        $dockerDesktopCompose = "C:\Program Files\Docker\Docker\resources\bin\docker-compose.exe"
        if (Test-Path $dockerDesktopCompose) {
            $standalone = Get-Item $dockerDesktopCompose
        }
    }
    if (-not $standalone) {
        throw "Missing Docker Compose. Tried 'docker compose version', 'docker-compose', and Docker Desktop docker-compose.exe."
    }

    $standalonePath = if ($standalone.Source) { $standalone.Source } else { $standalone.FullName }
    $version = Invoke-NativeCommand "docker-compose version" $standalonePath @("version")
    return @{
        FilePath = $standalonePath
        Prefix = @()
        Version = $version
    }
}

function Get-EnvValue {
    param(
        [string]$Path,
        [string]$Name,
        [string]$Default
    )

    if (-not (Test-Path $Path)) {
        return $Default
    }

    $match = Get-Content -Path $Path | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -First 1
    if (-not $match) {
        return $Default
    }

    return (($match -split "=", 2)[1]).Trim().Trim('"').Trim("'")
}

function Write-Utf8NoBom {
    param(
        [string]$Path,
        [string]$Content
    )

    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Get-ContainerHealth {
    try {
        $status = Invoke-NativeCommand `
            "docker inspect stage7-sui-local health" `
            "docker" `
            @("inspect", "-f", "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}", "stage7-sui-local")
        return $status.Trim()
    } catch {
        return "unknown"
    }
}

function Invoke-RpcSmoke {
    param([string]$Method)

    $payload = @{
        jsonrpc = "2.0"
        id = 1
        method = $Method
        params = @()
    } | ConvertTo-Json -Compress

    $response = Invoke-WebRequest `
        -Uri $RpcUrl `
        -Method Post `
        -ContentType "application/json" `
        -Body $payload `
        -TimeoutSec 5 `
        -UseBasicParsing

    $responseText = $response.Content

    try {
        $json = $responseText | ConvertFrom-Json -ErrorAction Stop
        if ($null -ne $json.result) {
            return @{
                Ready = $true
                Method = $Method
                Response = $responseText
            }
        }
    } catch {
        return @{
            Ready = $false
            Method = $Method
            Response = $responseText
        }
    }

    return @{
        Ready = $false
        Method = $Method
        Response = $responseText
    }
}

function Wait-ForRpc {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $attempt = 0
    $methods = @("sui_getLatestCheckpointSequenceNumber", "sui_getTotalTransactionBlocks")

    while ((Get-Date) -lt $deadline) {
        $attempt += 1
        $health = Get-ContainerHealth
        foreach ($method in $methods) {
            try {
                $result = Invoke-RpcSmoke -Method $method
                if ($result.Ready) {
                    Write-Host "ok: RPC ready via $($result.Method); container health=$health; attempt=$attempt"
                    return $result
                }
            } catch {
                Write-Host "waiting: RPC not ready yet; container health=$health; attempt=$attempt"
            }
        }
        Start-Sleep -Seconds 3
    }

    throw "Timed out after $TimeoutSeconds seconds waiting for $RpcUrl to answer Sui JSON-RPC smoke checks."
}

if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "Created $envFile from .env.example"
}

$experimentLabel = Get-EnvValue -Path $envFile -Name "EXPERIMENT_LABEL" -Default "baseline_local_validator"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $rawDir "baseline_$stamp.log"
$rpcFile = Join-Path $rawDir "baseline_${stamp}_rpc.json"

$compose = Resolve-ComposeCommand
Write-Host "ok: $($compose.Version)"

$composeArgs = @($compose.Prefix + @("--env-file", $envFile, "-f", $composeFile))
Invoke-NativeCommand "compose up sui-local" $compose.FilePath ($composeArgs + @("up", "-d", "sui-local")) | Write-Host

try {
    $rpcResult = Wait-ForRpc
    $rpcRecord = [ordered]@{
        source = "real-deployment"
        experiment_label = $experimentLabel
        captured_at = (Get-Date).ToUniversalTime().ToString("o")
        rpc_url = $RpcUrl
        method = $rpcResult.Method
        response = ($rpcResult.Response | ConvertFrom-Json)
    }
    Write-Utf8NoBom -Path $rpcFile -Content ($rpcRecord | ConvertTo-Json -Depth 8)

    $logs = Invoke-NativeCommand "docker logs stage7-sui-local" "docker" @("logs", "stage7-sui-local", "--since", "1h")
    Write-Utf8NoBom -Path $logFile -Content $logs

    Write-Host "baseline log: $logFile"
    Write-Host "RPC smoke response: $rpcFile"
} catch {
    try {
        $logs = Invoke-NativeCommand "docker logs stage7-sui-local after failure" "docker" @("logs", "stage7-sui-local", "--since", "1h")
        Write-Utf8NoBom -Path $logFile -Content $logs
        Write-Host "baseline log: $logFile"
    } catch {
        Write-Host "warn: failed to collect docker logs after runner failure: $($_.Exception.Message)"
    }
    throw
}
