param(
    [Parameter(Mandatory = $true)]
    [string]$RunId
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

$mvRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$composeFile = Join-Path $mvRoot "compose\compose.multivalidator.n4.yaml"
$composeCommand = Get-ComposeCommand

$env:RUN_ID = $RunId
Invoke-Compose -ComposeCommand $composeCommand -Arguments @("-f", $composeFile, "down")
if ($LASTEXITCODE -ne 0) {
    throw "Compose down failed for run id: $RunId"
}
Write-Host "Stopped multivalidator containers for run id: $RunId"
Write-Host "Data retained under: $(Join-Path $mvRoot "data\runs\$RunId")"
