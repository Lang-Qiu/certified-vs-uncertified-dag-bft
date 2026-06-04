param(
    [Parameter(Mandatory = $true)]
    [string]$RunId
)

$ErrorActionPreference = "Continue"
$warnings = [System.Collections.Generic.List[string]]::new()

function Invoke-Capture {
    param(
        [string]$Label,
        [string]$Path,
        [scriptblock]$Command
    )
    try {
        $output = & $Command 2>&1
        $text = ($output | Out-String)
        Set-Content -Path $Path -Value $text -Encoding UTF8
        if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
            [void]$warnings.Add("$Label failed with exit code $LASTEXITCODE")
        }
    }
    catch {
        Set-Content -Path $Path -Value $_.Exception.Message -Encoding UTF8
        [void]$warnings.Add("$Label failed: $($_.Exception.Message)")
    }
}

$mvRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$outDir = Join-Path $mvRoot "data\runs\$RunId\evidence\container_state"
New-Item -ItemType Directory -Force $outDir | Out-Null

Invoke-Capture "docker ps" (Join-Path $outDir "docker_ps.txt") { docker ps -a --filter "name=$RunId" }

$containers = @()
try {
    $containers = docker ps -a --filter "name=$RunId" --format "{{.Names}}" 2>$null
    if ($LASTEXITCODE -ne 0) {
        [void]$warnings.Add("docker ps names failed with exit code $LASTEXITCODE")
    }
}
catch {
    [void]$warnings.Add("docker ps names failed: $($_.Exception.Message)")
}

foreach ($container in $containers) {
    if (-not $container) {
        continue
    }
    $safeName = $container -replace "[^A-Za-z0-9_.-]", "_"
    Invoke-Capture "docker inspect $container" (Join-Path $outDir "$safeName.inspect.json") { docker inspect $container }
    Invoke-Capture "docker logs $container" (Join-Path $outDir "$safeName.logs.txt") { docker logs --timestamps $container }
}

$warningsPath = Join-Path $outDir "warnings.txt"
Set-Content -Path $warningsPath -Value ($warnings -join "`n") -Encoding UTF8
Write-Host "Wrote container state evidence: $outDir"
if ($warnings.Count -gt 0) {
    Write-Warning ($warnings -join "; ")
}
