param(
    [string]$RunId = "",
    [int]$Seed = 20260524,
    [string]$Scenario = "baseline",
    [int]$RepeatIndex = 1,
    [int]$EpochDurationMs = 60000,
    [string]$SuiImage = "stage7-sui:local"
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if ($null -eq (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

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

function Join-ProcessArguments {
    param([string[]]$Arguments)

    $escapedArgs = foreach ($arg in $Arguments) {
        if ($arg -match '^[^\s"]+$') {
            $arg
        }
        else {
            '"' + ($arg -replace '"', '\"') + '"'
        }
    }
    return ($escapedArgs -join " ")
}

function Invoke-ProcessCapture {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$StdoutPath,
        [string]$StderrPath
    )

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo.FileName = $FilePath
    $process.StartInfo.Arguments = Join-ProcessArguments -Arguments $Arguments
    $process.StartInfo.UseShellExecute = $false
    $process.StartInfo.RedirectStandardOutput = $true
    $process.StartInfo.RedirectStandardError = $true
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    Set-Content -Path $StdoutPath -Value $stdout -Encoding UTF8
    Set-Content -Path $StderrPath -Value $stderr -Encoding UTF8
    return $process.ExitCode
}

function Patch-FullnodeNetworkConfig {
    param([string]$FullnodePath)

    $fullnodeNetworkAddress = "network-address: /ip4/172.28.7.20/tcp/2070/https"
    $fullnodeListenAddress = 'listen-address: "0.0.0.0:2071"'
    $fullnodeExternalAddress = "external-address: /ip4/172.28.7.20/udp/2071"
    $fullnodeMetricsAddress = 'metrics-address: "0.0.0.0:2072"'

    $text = Get-Content -Path $FullnodePath -Raw -Encoding UTF8
    $text = $text -replace 'network-address: /ip4/127\.0\.0\.1/tcp/[0-9]+/https', $fullnodeNetworkAddress
    $text = $text -replace 'listen-address: "127\.0\.0\.1:[0-9]+"', $fullnodeListenAddress
    $text = $text -replace 'external-address: /ip4/127\.0\.0\.1/udp/[0-9]+', $fullnodeExternalAddress
    $text = $text -replace 'metrics-address: "127\.0\.0\.1:[0-9]+"', $fullnodeMetricsAddress
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($FullnodePath, $text, $utf8NoBom)

    $patched = [System.IO.File]::ReadAllText($FullnodePath, $utf8NoBom)
    foreach ($expected in @(
        $fullnodeNetworkAddress,
        $fullnodeListenAddress,
        $fullnodeExternalAddress,
        $fullnodeMetricsAddress
    )) {
        if (-not $patched.Contains($expected)) {
            throw "Fullnode config patch missing expected value: $expected"
        }
    }
}

Require-Command "python"
Require-Command "docker"
$composeCommand = Get-ComposeCommand

$mvRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$dataDir = Join-Path $mvRoot "data"
$generator = Join-Path $mvRoot "tools\generate_validator_configs.py"
New-Item -ItemType Directory -Force $dataDir | Out-Null

$generatorArgs = @(
    $generator,
    "--seed", [string]$Seed,
    "--scenario", $Scenario,
    "--repeat-index", [string]$RepeatIndex,
    "--output-root", $mvRoot.Path,
    "--validators", "7",
    "--fault-tolerance", "2",
    "--write"
)
if ($RunId) {
    $generatorArgs += @("--run-id", $RunId)
}

$planOutput = (& python @generatorArgs 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "generate_validator_configs.py --write failed: $planOutput"
}
if (-not $RunId) {
    $planPath = $planOutput -split "`r?`n" | Select-Object -Last 1
    $RunId = Split-Path (Split-Path $planPath -Parent) -Leaf
}
if (-not $RunId) {
    throw "RunId could not be resolved from generator output."
}

$runRoot = Join-Path $dataDir "runs\$RunId"
$prepareDir = Join-Path $runRoot "prepare"
$officialGenesisDir = Join-Path $runRoot "official-genesis"
New-Item -ItemType Directory -Force $prepareDir | Out-Null
New-Item -ItemType Directory -Force $officialGenesisDir | Out-Null

Write-Host "Checking image contains sui-node: $SuiImage"
& docker run --rm $SuiImage sh -c "command -v sui-node" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Image '$SuiImage' does not contain sui-node. Rebuild stage7-sui:local after the Dockerfile update, then rerun this script."
}

$benchmarkIps = @(
    "172.28.7.11",
    "172.28.7.12",
    "172.28.7.13",
    "172.28.7.14",
    "172.28.7.15",
    "172.28.7.16",
    "172.28.7.17"
)

$genesisStdout = Join-Path $prepareDir "genesis.stdout.log"
$genesisStderr = Join-Path $prepareDir "genesis.stderr.log"
$dockerArgs = @(
    "run", "--rm",
    "-v", "${dataDir}:/mvdata",
    $SuiImage,
    "sui", "genesis",
    "--committee-size", "7",
    "--benchmark-ips"
) + $benchmarkIps + @(
    "--working-dir", "/mvdata/runs/$RunId/official-genesis",
    "--force",
    "--with-faucet",
    "--epoch-duration-ms", [string]$EpochDurationMs
)

Write-Host "Running official sui genesis for run id: $RunId"
$exitCode = Invoke-ProcessCapture -FilePath "docker" -Arguments $dockerArgs -StdoutPath $genesisStdout -StderrPath $genesisStderr
if ($exitCode -ne 0) {
    throw "sui genesis failed with exit code $exitCode. See $genesisStdout and $genesisStderr"
}

Patch-FullnodeNetworkConfig -FullnodePath (Join-Path $officialGenesisDir "fullnode.yaml")

$expectedFiles = @(
    "172.28.7.11-2000.yaml",
    "172.28.7.12-2010.yaml",
    "172.28.7.13-2020.yaml",
    "172.28.7.14-2030.yaml",
    "172.28.7.15-2040.yaml",
    "172.28.7.16-2050.yaml",
    "172.28.7.17-2060.yaml",
    "network.yaml",
    "fullnode.yaml",
    "genesis.blob"
)
foreach ($file in $expectedFiles) {
    $path = Join-Path $officialGenesisDir $file
    if (-not (Test-Path $path)) {
        throw "Expected genesis artifact missing: $path"
    }
}

$composeFile = Join-Path $mvRoot "compose\compose.multivalidator.yaml"
$composeText = (@($composeCommand) + @("-f", $composeFile, "up", "-d")) -join " "
Write-Host "RunId: $RunId"
Write-Host "Genesis logs: $prepareDir"
Write-Host "Next:"
Write-Host "  `$env:RUN_ID='$RunId'; `$env:SUI_IMAGE='$SuiImage'; $composeText"
