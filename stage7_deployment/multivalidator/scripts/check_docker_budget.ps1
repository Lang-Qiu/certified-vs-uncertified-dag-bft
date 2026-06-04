$ErrorActionPreference = "Continue"

function Add-WarningMessage {
    param([string]$Message)
    if ($Message -and -not $script:Warnings.Contains($Message)) {
        [void]$script:Warnings.Add($Message)
    }
}

function Invoke-Capture {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    try {
        $output = & $Command 2>&1
        if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
            $text = ($output | Out-String).Trim()
            $detail = "command returned nonzero exit"
            if ($text -match "Access is denied") {
                $detail = "access denied to Docker Desktop engine"
            }
            elseif ($text -match "unknown command") {
                $detail = "command not supported by this Docker CLI"
            }
            elseif ($text -match "Cannot connect|error during connect") {
                $detail = "Docker engine is not reachable"
            }
            if ($detail) {
                Add-WarningMessage "$Label failed with exit code $LASTEXITCODE`: $detail"
            }
            else {
                Add-WarningMessage "$Label failed with exit code $LASTEXITCODE"
            }
            return ""
        }
        return ($output | Out-String).Trim()
    }
    catch {
        Add-WarningMessage "$Label failed: $($_.Exception.Message)"
        return ""
    }
}

function ConvertTo-NullableInt64 {
    param([object]$Value)
    if ($null -eq $Value) {
        return $null
    }
    try {
        return [int64]$Value
    }
    catch {
        return $null
    }
}

$script:Warnings = [System.Collections.Generic.List[string]]::new()
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$manifestDir = Join-Path $root "data\manifests"
New-Item -ItemType Directory -Force $manifestDir | Out-Null
$snapshotPath = Join-Path $manifestDir "environment_snapshot.json"

$dockerServerVersion = ""
$dockerMemoryTotal = $null
$dockerInfo = ""
$dockerImages = ""
$composeVersion = ""
$suiCliVersion = ""

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if ($null -eq $dockerCommand) {
    Add-WarningMessage "docker command not found; Docker fields were left empty"
}
else {
    $dockerInfoJson = Invoke-Capture "docker info json" { docker info --format "{{json .}}" }
    if ($dockerInfoJson) {
        try {
            $dockerInfoObject = $dockerInfoJson | ConvertFrom-Json
            $dockerServerVersion = [string]$dockerInfoObject.ServerVersion
            $dockerMemoryTotal = ConvertTo-NullableInt64 $dockerInfoObject.MemTotal
        }
        catch {
            Add-WarningMessage "docker info json could not be parsed: $($_.Exception.Message)"
        }
    }

    $dockerInfo = Invoke-Capture "docker info" { docker info }
    $dockerImages = Invoke-Capture "docker images" { docker images --digests --format "{{.Repository}}:{{.Tag}} {{.ID}} {{.Digest}}" }
    $composeVersion = Invoke-Capture "docker compose version" { docker compose version }
    if (-not $composeVersion) {
        $composeCommand = Get-Command docker-compose -ErrorAction SilentlyContinue
        if ($null -ne $composeCommand) {
            $composeVersion = Invoke-Capture "docker-compose version" { docker-compose version }
        }
    }
}

$suiCommand = Get-Command sui -ErrorAction SilentlyContinue
if ($null -eq $suiCommand) {
    Add-WarningMessage "sui command not found; sui.cli_version was left empty"
}
else {
    $suiCliVersion = Invoke-Capture "sui --version" { sui --version }
}

$driveInfo = [System.IO.DriveInfo]::new((Split-Path -Qualifier $root.Path))
$diskFreeBytes = $null
if ($null -ne $driveInfo -and $driveInfo.IsReady) {
    $diskFreeBytes = [int64]$driveInfo.AvailableFreeSpace
}
else {
    Add-WarningMessage "disk free space could not be determined"
}

$snapshot = [ordered]@{
    captured_at = (Get-Date).ToString("o")
    host = [ordered]@{
        os = "Windows"
        timezone = "Asia/Shanghai"
    }
    docker = [ordered]@{
        server_version = $dockerServerVersion
        memory_total_bytes = $dockerMemoryTotal
        info = $dockerInfo
        images = $dockerImages
        compose_version = $composeVersion
    }
    sui = [ordered]@{
        commit = "62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a"
        cli_version = $suiCliVersion
    }
    disk = [ordered]@{
        path = $root.Path
        free_bytes = $diskFreeBytes
    }
    stage2 = [ordered]@{
        baseline_manifest = "stage7_deployment/data/manifest.json"
    }
    warnings = @($script:Warnings)
}

$snapshot | ConvertTo-Json -Depth 6 | Set-Content -Path $snapshotPath -Encoding UTF8
Write-Host "Wrote environment snapshot: $snapshotPath"
if ($script:Warnings.Count -gt 0) {
    Write-Warning ($script:Warnings -join "; ")
}
