param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9-]+$')][string]$Label,
    [ValidateRange(10,180)][int]$Seconds=60,
    [ValidateRange(1,120)][int]$Rate=30,
    [switch]$Teensy
)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$reportPath=Join-Path $projectRoot "docs/performance-program-20260912/td/$Label-sync.json"
if (Test-Path -LiteralPath $reportPath) { throw 'Evidence already exists' }
$oneDriveRoot=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Microsoft/OneDrive'))
$processes=@(Get-CimInstance Win32_Process -Filter "Name='OneDrive.exe' OR Name='OneDrive.Sync.Service.exe'")
foreach ($process in $processes) {
    $resolved=[IO.Path]::GetFullPath($process.ExecutablePath)
    if (-not $resolved.StartsWith($oneDriveRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw 'Unexpected OneDrive process path; no process stopped'
    }
}
$report=[ordered]@{before=@($processes | Select-Object Name,ProcessId,ExecutablePath); stopped=@(); restored=@(); benchmark_exit=$null}
try {
    # Closing the sync client leaves local files intact. Its auxiliary sync
    # process can survive /shutdown, so stop only the verified same-user binary.
    $primary=@($processes | Where-Object Name -eq 'OneDrive.exe')
    if ($primary.Count) {
        $shutdown=Start-Process -FilePath $primary[0].ExecutablePath -ArgumentList '/shutdown' -WindowStyle Hidden -PassThru
        if (-not $shutdown.WaitForExit(5000)) {
            # Some OneDrive versions leave the command helper waiting on the
            # busy client. Bound that helper, then stop the verified originals.
            Stop-Process -Id $shutdown.Id
        }
        Start-Sleep -Seconds 1
    }
    foreach ($process in $processes) {
        $remaining=Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue
        if ($remaining) {
            if ([IO.Path]::GetFullPath($remaining.Path) -ne [IO.Path]::GetFullPath($process.ExecutablePath)) {throw 'Process identity changed'}
            Stop-Process -Id $process.ProcessId
        }
        $report.stopped += $process.Name
    }
    $script=if ($Teensy) {'td_teensy_integrated_20260912.py'} else {'td_perform_benchmark_20260912.py'}
    & 'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe' (Join-Path $PSScriptRoot $script) $Label --seconds $Seconds --rate $Rate --frame-pacing
    $report.benchmark_exit=$LASTEXITCODE
    if ($LASTEXITCODE -ne 0) {throw "Benchmark exited $LASTEXITCODE"}
}
finally {
    # Restore every originally running component, including on benchmark error.
    foreach ($process in ($processes | Sort-Object Name)) {
        $name=[IO.Path]::GetFileNameWithoutExtension($process.Name)
        if (-not (Get-Process -Name $name -ErrorAction SilentlyContinue)) {
            $arguments=if ($process.Name -eq 'OneDrive.exe') {'/background'} else {'/silentConfig'}
            Start-Process -FilePath $process.ExecutablePath -ArgumentList $arguments -WindowStyle Hidden
            Start-Sleep -Seconds 1
        }
        $report.restored += @{name=$process.Name;running=[bool](Get-Process -Name $name -ErrorAction SilentlyContinue)}
    }
    $report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportPath -Encoding utf8
}
