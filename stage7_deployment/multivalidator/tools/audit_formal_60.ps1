param(
    [string]$RunsRoot = "$PSScriptRoot/../data/runs",
    [string]$OutFile  = "$PSScriptRoot/../reports/audit_recheck_$((Get-Date).ToString('yyyyMMddHHmmss')).md"
)

$ErrorActionPreference = 'Stop'
$RunsRoot = (Resolve-Path $RunsRoot).Path

$plan = @{
    'baseline'               = @{ seed = 2026052402; reps = 1..10 }
    'delay_low'              = @{ seed = 2026052402; reps = 1..10 }
    'delay_high'             = @{ seed = 2026052402; reps = 1..10 }
    'loss_low'               = @{ seed = 2026052402; reps = 1..10 }
    'crash_one_validator'    = @{ seed = 2026052406; reps = 1..10 }
    'two_validator_pressure' = @{ seed = 2026052406; reps = 1..10 }
}

$rows = New-Object System.Collections.Generic.List[object]
$globalIssues = New-Object System.Collections.Generic.List[string]

foreach ($scenario in $plan.Keys | Sort-Object) {
    $cfg = $plan[$scenario]
    foreach ($rep in $cfg.reps) {
        $runId = "{0}_seed{1}_rep{2:D2}" -f $scenario, $cfg.seed, $rep
        $runDir = Join-Path $RunsRoot $runId

        $row = [ordered]@{
            run_id            = $runId
            scenario          = $scenario
            dir_exists        = $false
            controller_ok     = $false
            controller_status = $null
            manifest_exists   = $false
            manifest_entries  = 0
            hash_mismatches   = 0
            metrics_exists    = $false
            validator_count   = $null
            fault_tolerance   = $null
            tx_ok             = $null
            tx_failed         = $null
            availability      = $null
            recovery_time_ms  = $null
            ckpt_count        = $null
        }

        if (-not (Test-Path $runDir)) {
            $globalIssues.Add("${runId}: directory missing")
            $rows.Add([pscustomobject]$row); continue
        }
        $row.dir_exists = $true

        $ctlPath = Join-Path $runDir 'controller_record.json'
        if (Test-Path $ctlPath) {
            try {
                $ctl = Get-Content $ctlPath -Raw -Encoding utf8 | ConvertFrom-Json
                $row.controller_status = $ctl.status
                $row.controller_ok = ($ctl.status -eq 'completed')
                if (-not $row.controller_ok) { $globalIssues.Add("${runId}: controller status=$($ctl.status)") }
            } catch {
                $globalIssues.Add("${runId}: controller_record.json parse failed: $_")
            }
        } else {
            $globalIssues.Add("${runId}: controller_record.json missing")
        }

        $mfPath = Join-Path $runDir 'manifest.json'
        if (Test-Path $mfPath) {
            $row.manifest_exists = $true
            try {
                $mf = Get-Content $mfPath -Raw -Encoding utf8 | ConvertFrom-Json
                $row.manifest_entries = $mf.entries.Count
                $mismatch = 0
                foreach ($entry in $mf.entries) {
                    $entryPath = Join-Path $runDir $entry.path
                    if (-not (Test-Path $entryPath -PathType Leaf)) {
                        $mismatch++
                        $globalIssues.Add("${runId}: missing artifact $($entry.path)")
                        continue
                    }
                    $actual = (Get-FileHash -Path $entryPath -Algorithm SHA256).Hash.ToLowerInvariant()
                    if ($actual -ne $entry.sha256.ToLowerInvariant()) {
                        $mismatch++
                        $globalIssues.Add("${runId}: hash mismatch on $($entry.path) (expected $($entry.sha256), got $actual)")
                    }
                }
                $row.hash_mismatches = $mismatch
            } catch {
                $globalIssues.Add("${runId}: manifest parse failed: $_")
            }
        } else {
            $globalIssues.Add("${runId}: manifest.json missing")
        }

        $mxPath = Join-Path $runDir 'metrics/consensus_metrics.json'
        if (Test-Path $mxPath) {
            $row.metrics_exists = $true
            try {
                $mx = Get-Content $mxPath -Raw -Encoding utf8 | ConvertFrom-Json
                $row.validator_count  = $mx.validator_count
                $row.fault_tolerance  = $mx.fault_tolerance
                $row.tx_ok            = $mx.successful_transactions
                $row.tx_failed        = $mx.failed_transactions
                $row.availability     = $mx.availability_ratio
                $row.recovery_time_ms = $mx.recovery_time_ms
                $row.ckpt_count       = $mx.checkpoint_count

                if ($mx.validator_count -ne 7)        { $globalIssues.Add("${runId}: validator_count=$($mx.validator_count) expected 7") }
                if ($mx.fault_tolerance -ne 2)        { $globalIssues.Add("${runId}: fault_tolerance=$($mx.fault_tolerance) expected 2") }
                if ($mx.failed_transactions -ne 0)    { $globalIssues.Add("${runId}: failed_transactions=$($mx.failed_transactions) expected 0") }
                if ($mx.availability_ratio -lt 1.0)   { $globalIssues.Add("${runId}: availability=$($mx.availability_ratio) <1.0") }
            } catch {
                $globalIssues.Add("${runId}: consensus_metrics parse failed: $_")
            }
        } else {
            $globalIssues.Add("${runId}: consensus_metrics.json missing")
        }

        $rows.Add([pscustomobject]$row)
    }
}

$scenarioRows = $rows | Group-Object scenario | ForEach-Object {
    $g = $_.Group
    $okList = $g | Where-Object { $_.metrics_exists }
    $ckpt = $okList | ForEach-Object { [int]$_.ckpt_count }
    $tx_ok_sum   = ($okList | Measure-Object tx_ok -Sum).Sum
    $tx_fail_sum = ($okList | Measure-Object tx_failed -Sum).Sum
    $availMin    = ($okList | Measure-Object availability -Minimum).Minimum
    $recoveries  = $okList | Where-Object { $_.recovery_time_ms -ne $null } | ForEach-Object { [int]$_.recovery_time_ms }
    [pscustomobject]@{
        scenario        = $_.Name
        n               = $g.Count
        n_completed     = ($g | Where-Object controller_ok).Count
        n_metrics       = $okList.Count
        tx_ok_total     = $tx_ok_sum
        tx_failed_total = $tx_fail_sum
        availability_min= $availMin
        ckpt_min        = ($ckpt | Measure-Object -Minimum).Minimum
        ckpt_max        = ($ckpt | Measure-Object -Maximum).Maximum
        ckpt_median     = if ($ckpt.Count) { ($ckpt | Sort-Object)[[int][math]::Floor($ckpt.Count/2)] } else { $null }
        recovery_median = if ($recoveries.Count) { ($recoveries | Sort-Object)[[int][math]::Floor($recoveries.Count/2)] } else { $null }
        recovery_min    = if ($recoveries.Count) { ($recoveries | Measure-Object -Minimum).Minimum } else { $null }
        recovery_max    = if ($recoveries.Count) { ($recoveries | Measure-Object -Maximum).Maximum } else { $null }
    }
}

$summaryPath = Join-Path $RunsRoot 'formal_matrix_summary_seed2026052402_2026052406.json'
$published = Get-Content $summaryPath -Raw -Encoding utf8 | ConvertFrom-Json
$comparison = foreach ($pub in $published) {
    $rec = $scenarioRows | Where-Object scenario -eq $pub.scenario
    [pscustomobject]@{
        scenario      = $pub.scenario
        tx_ok_pub     = $pub.tx_ok_total;            tx_ok_rec     = $rec.tx_ok_total
        tx_fail_pub   = $pub.tx_failed_total;        tx_fail_rec   = $rec.tx_failed_total
        avail_pub     = $pub.availability_min;       avail_rec     = $rec.availability_min
        ckpt_med_pub  = $pub.checkpoint_count_median; ckpt_med_rec = $rec.ckpt_median
        ckpt_min_pub  = $pub.checkpoint_count_min;   ckpt_min_rec  = $rec.ckpt_min
        ckpt_max_pub  = $pub.checkpoint_count_max;   ckpt_max_rec  = $rec.ckpt_max
        recov_med_pub = $pub.recovery_time_median_ms; recov_med_rec = $rec.recovery_median
    }
}

$L = New-Object System.Collections.Generic.List[string]
$L.Add("# Stage 2 Formal 60-run Re-check Report")
$L.Add("")
$L.Add("- Generated (UTC): $([DateTime]::UtcNow.ToString('o'))")
$L.Add("- Script: stage7_deployment/multivalidator/tools/audit_formal_60.ps1")
$L.Add("- Scope: 6 scenarios x 10 reps = 60 formal runs (per report spec)")
$L.Add("")
$L.Add("## 1. Overview")
$L.Add("")
$L.Add("| Check | Pass / Total |")
$L.Add("| --- | ---: |")
$L.Add("| Directory present | $(($rows | Where-Object dir_exists).Count) / 60 |")
$L.Add("| controller_record.status=completed | $(($rows | Where-Object controller_ok).Count) / 60 |")
$L.Add("| manifest.json present | $(($rows | Where-Object manifest_exists).Count) / 60 |")
$L.Add("| manifest hashes all match | $(($rows | Where-Object { $_.manifest_exists -and $_.hash_mismatches -eq 0 }).Count) / 60 |")
$L.Add("| consensus_metrics.json present | $(($rows | Where-Object metrics_exists).Count) / 60 |")
$L.Add("| validator_count=7 | $(($rows | Where-Object { $_.validator_count -eq 7 }).Count) / 60 |")
$L.Add("| fault_tolerance=2 | $(($rows | Where-Object { $_.fault_tolerance -eq 2 }).Count) / 60 |")
$L.Add("| failed_transactions=0 | $(($rows | Where-Object { $_.tx_failed -eq 0 }).Count) / 60 |")
$L.Add("| availability=1.0 | $(($rows | Where-Object { $_.availability -eq 1.0 }).Count) / 60 |")
$L.Add("")
$L.Add("## 2. Scenario aggregate: recomputed vs published")
$L.Add("")
$L.Add("Format: recomputed / published")
$L.Add("")
$L.Add("| scenario | n | n_completed | tx_ok | tx_fail | avail_min | ckpt_med | ckpt_min | ckpt_max | recov_med |")
$L.Add("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
foreach ($c in $comparison | Sort-Object scenario) {
    $rec = $scenarioRows | Where-Object scenario -eq $c.scenario
    $L.Add("| $($c.scenario) | $($rec.n) | $($rec.n_completed) | $($c.tx_ok_rec)/$($c.tx_ok_pub) | $($c.tx_fail_rec)/$($c.tx_fail_pub) | $($c.avail_rec)/$($c.avail_pub) | $($c.ckpt_med_rec)/$($c.ckpt_med_pub) | $($c.ckpt_min_rec)/$($c.ckpt_min_pub) | $($c.ckpt_max_rec)/$($c.ckpt_max_pub) | $($c.recov_med_rec)/$($c.recov_med_pub) |")
}
$L.Add("")
$L.Add("## 3. All anomalies (hash mismatch / missing artifact / abnormal status)")
$L.Add("")
if ($globalIssues.Count -eq 0) {
    $L.Add("None.")
} else {
    foreach ($issue in $globalIssues) { $L.Add("- $issue") }
}
$L.Add("")
$L.Add("## 4. Per-run detail")
$L.Add("")
$L.Add("| run_id | dir | ctl | mf | hash# | metrics | val | f | tx_ok | tx_fail | avail | recovery_ms | ckpt |")
$L.Add("| --- | :---: | :---: | :---: | ---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
foreach ($r in $rows | Sort-Object scenario, run_id) {
    $ctlMark = if ($r.controller_ok) { 'OK' } else { "$($r.controller_status)" }
    $dirMark = if ($r.dir_exists) { 'Y' } else { 'N' }
    $mfMark  = if ($r.manifest_exists) { 'Y' } else { 'N' }
    $mxMark  = if ($r.metrics_exists) { 'Y' } else { 'N' }
    $L.Add("| $($r.run_id) | $dirMark | $ctlMark | $mfMark | $($r.hash_mismatches) | $mxMark | $($r.validator_count) | $($r.fault_tolerance) | $($r.tx_ok) | $($r.tx_failed) | $($r.availability) | $($r.recovery_time_ms) | $($r.ckpt_count) |")
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($OutFile, ($L -join "`n"), $utf8NoBom)
Write-Host "Audit report written to: $OutFile"
Write-Host "Total issues: $($globalIssues.Count)"
