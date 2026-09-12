param([string]$Label='priority-30fps-120s',[int]$Seconds=120,[int]$Rate=30)
$ErrorActionPreference='Stop'
$tdTaskProcesses=@(Get-Process -Name TouchDesigner)
if ($tdTaskProcesses.Count -ne 1) { throw 'Expected exactly one TouchDesigner process' }
$tdTaskProcess=$tdTaskProcesses[0]
$tdTaskOriginalPriority=$tdTaskProcess.PriorityClass
$tdTaskRoot=Split-Path -Parent $PSScriptRoot
$tdTaskEvidence=Join-Path $tdTaskRoot ('docs/performance-program-20260912/td/'+$Label+'-priority.json')
if (Test-Path -LiteralPath $tdTaskEvidence) { throw 'Evidence already exists' }
try {
    $tdTaskProcess.PriorityClass='AboveNormal'
    & 'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe' (Join-Path $PSScriptRoot 'td_perform_benchmark_20260912.py') $Label --seconds $Seconds --rate $Rate --frame-pacing --worker-priority above_normal
    if ($LASTEXITCODE -ne 0) { throw 'Benchmark failed' }
} finally {
    if (-not $tdTaskProcess.HasExited) { $tdTaskProcess.PriorityClass=$tdTaskOriginalPriority }
    @{processId=$tdTaskProcess.Id;before=[string]$tdTaskOriginalPriority;during='AboveNormal';after=[string]$tdTaskProcess.PriorityClass} | ConvertTo-Json | Set-Content -LiteralPath $tdTaskEvidence -Encoding utf8
}
