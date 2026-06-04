param(
    [string]$SuiRef = "62ee6ada958cd61b3c8a4466dd33c9aba3cdff8a",
    [switch]$BypassGitProxy
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$external = Join-Path $root "external"
$suiDir = Join-Path $external "sui"
$narwhalDir = Join-Path $external "narwhal"
$suiUrl = "https://github.com/MystenLabs/sui.git"
$allowedSuiOrigins = @(
    "https://github.com/MystenLabs/sui.git",
    "git@github.com:MystenLabs/sui.git"
)

New-Item -ItemType Directory -Force -Path $external | Out-Null

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [string]$Action = "run git command"
    )

    $gitArgs = @()
    if ($BypassGitProxy) {
        $gitArgs += @("-c", "http.proxy=", "-c", "https.proxy=")
    }
    $gitArgs += $Arguments

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & git @gitArgs 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -ne 0) {
        $commandText = "git " + ($gitArgs -join " ")
        $outputText = ($output | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                $_.Exception.Message
            } else {
                $_.ToString()
            }
        } | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($outputText)) {
            $outputText = "<no output>"
        }
        throw "Failed to $Action. Command: $commandText. Exit code: $exitCode. Output: $outputText"
    }

    return $output
}

function Assert-SuiCheckout {
    param(
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    $insideWorktree = (Invoke-Git -Arguments @("-C", $Path, "rev-parse", "--is-inside-work-tree") -Action "verify existing Sui checkout is a Git worktree" | Select-Object -First 1).ToString().Trim()
    if ($insideWorktree -ne "true") {
        throw "Existing Sui path is not a Git worktree: $Path. Move it aside or choose a clean external directory; this script will not delete it."
    }

    $origin = (Invoke-Git -Arguments @("-C", $Path, "remote", "get-url", "origin") -Action "read existing Sui origin URL" | Select-Object -First 1).ToString().Trim()
    if ($allowedSuiOrigins -notcontains $origin) {
        $allowedText = $allowedSuiOrigins -join " or "
        throw "Existing Sui checkout at $Path has unexpected origin '$origin'. Expected $allowedText. This script will not modify or delete the checkout."
    }
}

function Sync-Repo {
    param(
        [string]$Url,
        [string]$Path,
        [string]$Name,
        [string]$Ref
    )

    Write-Host "$Name requested ref: $Ref"
    if (Test-Path $Path) {
        Write-Host "Updating $Name at $Path"
        Invoke-Git -Arguments @("-C", $Path, "fetch", "--depth", "1", "origin", $Ref) -Action "fetch $Name ref '$Ref'" | Out-Null
        Invoke-Git -Arguments @("-C", $Path, "checkout", "--detach", "FETCH_HEAD") -Action "checkout $Name ref '$Ref'" | Out-Null
    } else {
        Write-Host "Cloning $Name into $Path"
        Invoke-Git -Arguments @("clone", "--no-checkout", "--depth", "1", $Url, $Path) -Action "clone $Name from $Url" | Out-Null
        Invoke-Git -Arguments @("-C", $Path, "fetch", "--depth", "1", "origin", $Ref) -Action "fetch $Name ref '$Ref'" | Out-Null
        Invoke-Git -Arguments @("-C", $Path, "checkout", "--detach", "FETCH_HEAD") -Action "checkout $Name ref '$Ref'" | Out-Null
    }
    $sha = (Invoke-Git -Arguments @("-C", $Path, "rev-parse", "HEAD") -Action "read $Name HEAD SHA" | Select-Object -First 1).ToString().Trim()
    Write-Host "$Name actual commit: $sha"
}

Assert-SuiCheckout -Path $suiDir
Sync-Repo -Url $suiUrl -Path $suiDir -Name "sui" -Ref $SuiRef

Write-Host "Narwhal is archived; clone it only when explicitly requested:"
Write-Host "git clone --depth 1 https://github.com/MystenLabs/narwhal.git $narwhalDir"
