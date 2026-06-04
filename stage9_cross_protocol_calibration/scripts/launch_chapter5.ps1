# Launcher: starts chapter5_enforcement_scan.ps1 as independent PowerShell process
# that writes to disk (not stdout), so we can monitor chapter5_progress.txt.
$scanScript = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage9_cross_protocol_calibration\scripts\chapter5_enforcement_scan.ps1"
$logFile = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage9_cross_protocol_calibration\data\chapter5_run.log"

# Use -Command instead of -File so array parameters bind correctly
$cmd = "& '$scanScript' -Committee both -LossRates @(0,2,5,10) -Reps 5 -WarmupCapSeconds 150"
$args = @(
    "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
    "-Command", $cmd
)

# Clean slate
$csvPath = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator\data\runs\chapter5_enforcement_summary.csv"
$progPath = "E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator\data\runs\chapter5_progress.txt"
if (Test-Path $csvPath) { Remove-Item $csvPath }
if (Test-Path $progPath) { Remove-Item $progPath }

Write-Host "Launching chapter5 scan as independent process..."
$proc = Start-Process -FilePath "powershell.exe" -ArgumentList $args -NoNewWindow -PassThru -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err"
Write-Host "PID: $($proc.Id)"
Write-Host "Monitor: E:\LQiu\lab_folder\Blockchain_final_pipeline\stage7_deployment\multivalidator\data\runs\chapter5_progress.txt"
Write-Host "Log: $logFile"
