param(
    [string]$ContainerName = "stage7-sui-local",
    [ValidateRange(0, 86400)]
    [int]$DownSeconds = 15
)

$ErrorActionPreference = "Stop"

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
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

    if ($outputText) {
        Write-Host $outputText
    }
    return $outputText
}

if ($ContainerName -notmatch '^[A-Za-z0-9_.-]+$') {
    throw "ContainerName contains unsupported characters: $ContainerName"
}

Write-Host "Stopping $ContainerName for $DownSeconds seconds"
Invoke-NativeCommand "docker stop $ContainerName" "docker" @("stop", $ContainerName) | Out-Null

try {
    if ($DownSeconds -gt 0) {
        Start-Sleep -Seconds $DownSeconds
    }

    Write-Host "Restarting $ContainerName"
    Invoke-NativeCommand "docker start $ContainerName" "docker" @("start", $ContainerName) | Out-Null
    Write-Host "Restart smoke completed for $ContainerName"
} catch {
    Write-Error "Failed while restarting $ContainerName after stop: $($_.Exception.Message)"
    throw
}
