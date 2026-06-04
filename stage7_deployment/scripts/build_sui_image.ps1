$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$composeDir = Join-Path $root "compose"
$envFile = Join-Path $composeDir ".env"
$envExample = Join-Path $composeDir ".env.example"
$composeFile = Join-Path $composeDir "compose.yaml"

function Invoke-NativeCommand {
    param(
        [string]$Description,
        [string]$FilePath,
        [string[]]$Arguments
    )

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & $FilePath @Arguments 2>&1
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
        throw "Missing Docker Compose v2. Tried 'docker compose version' and 'docker-compose version'."
    }
    $standalonePath = if ($standalone.Source) { $standalone.Source } else { $standalone.FullName }

    $version = Invoke-NativeCommand "docker-compose version" $standalonePath @("version")
    return @{
        FilePath = $standalonePath
        Prefix = @()
        Version = $version
    }
}

if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "Created $envFile from .env.example"
}

$dockerOs = Invoke-NativeCommand "docker info" "docker" @("info", "--format", "{{.OSType}}")
if ($dockerOs -ne "linux") {
    throw "Docker must be using Linux containers before building; observed OSType=$dockerOs"
}

$compose = Resolve-ComposeCommand
Write-Host "ok: $($compose.Version)"
Write-Host "ok: Docker Linux containers enabled"

$env:COMPOSE_BAKE = "false"
$composeArgs = @($compose.Prefix + @("--env-file", $envFile, "-f", $composeFile, "build", "sui-local"))
Invoke-NativeCommand "compose build sui-local" $compose.FilePath $composeArgs | Write-Host
