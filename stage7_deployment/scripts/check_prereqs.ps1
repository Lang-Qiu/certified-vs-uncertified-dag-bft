$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        throw "Missing required command: $Name"
    }
    Write-Host "ok: $Name -> $($cmd.Source)"
}

function Invoke-NativeCommand {
    param(
        [string]$Description,
        [string]$Command,
        [string[]]$Arguments = @()
    )

    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & $Command @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    $text = ($output | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine

    if ($exitCode -ne 0) {
        if ([string]::IsNullOrWhiteSpace($text)) {
            $text = "<no output>"
        }
        throw "$Description failed (exit $exitCode): $text"
    }

    return $text.Trim()
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
            Version = (($pluginOutput | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine).Trim()
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

    $version = Invoke-NativeCommand `
        -Description "docker-compose version check" `
        -Command $standalonePath `
        -Arguments @("version")
    return @{
        FilePath = $standalonePath
        Prefix = @()
        Version = $version
    }
}

Require-Command "docker"
Require-Command "git"
Require-Command "python"

$dockerVersion = Invoke-NativeCommand `
    -Description "docker server version check" `
    -Command "docker" `
    -Arguments @("version", "--format", "{{.Server.Version}}")
Write-Host "ok: docker server $dockerVersion"

$compose = Resolve-ComposeCommand
Write-Host "ok: $($compose.Version)"

$dockerInfo = Invoke-NativeCommand `
    -Description "docker OSType check" `
    -Command "docker" `
    -Arguments @("info", "--format", "{{.OSType}}")
if ($dockerInfo -ne "linux") {
    throw "Docker must be using Linux containers; observed OSType=$dockerInfo"
}
Write-Host "ok: Docker Linux containers enabled"

$pythonVersion = Invoke-NativeCommand `
    -Description "python version check" `
    -Command "python" `
    -Arguments @("--version")
if ($pythonVersion -notmatch "Python\s+(\d+)\.(\d+)(?:\.(\d+))?") {
    throw "Unable to parse Python version from: $pythonVersion"
}
$pythonMajor = [int]$Matches[1]
$pythonMinor = [int]$Matches[2]
if (($pythonMajor -lt 3) -or (($pythonMajor -eq 3) -and ($pythonMinor -lt 9))) {
    throw "Python 3.9+ required; observed $pythonVersion"
}
Write-Host "ok: $pythonVersion"

$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if ($cargo) {
    Write-Host "ok: cargo -> $($cargo.Source)"
} else {
    Write-Host "warn: cargo not found; Docker build can still compile Sui, but local Rust inspection will be limited"
}
