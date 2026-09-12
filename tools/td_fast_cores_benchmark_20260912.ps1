param(
 [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9-]+$')][string]$Label,
 [ValidateRange(10,180)][int]$Seconds=60,
 [ValidateRange(1,120)][int]$Rate=32,
 [switch]$Teensy
)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$record=Join-Path $root "docs/performance-program-20260912/td/$Label-affinity.json"
if(Test-Path -LiteralPath $record){throw 'Evidence exists'}
$cpu=Get-Content -Raw -LiteralPath (Join-Path $root 'docs/performance-program-20260912/td/host-cpu-sets.json') | ConvertFrom-Json
$highest=($cpu.cpu_sets | Measure-Object efficiency -Maximum).Maximum
$selected=@($cpu.cpu_sets | Where-Object efficiency -eq $highest)
if($selected.Count -eq $cpu.cpu_sets.Count -or @($selected | Where-Object group -ne 0).Count){throw 'No audited heterogeneous single-group CPU topology'}
$processes=@(Get-Process TouchDesigner)
if($processes.Count -ne 1){throw 'Expected exactly one TouchDesigner process'}
$process=$processes[0]
$old=$process.ProcessorAffinity.ToInt64()
[long]$mask=0
foreach($cpuSet in $selected){$mask=$mask -bor ([long]1 -shl $cpuSet.logical)}
$report=[ordered]@{pid=$process.Id;before=$old;selected=$mask;logical_cpus=@($selected.logical)}
try {
 $process.ProcessorAffinity=[IntPtr]$mask
 & (Join-Path $PSScriptRoot 'td_sync_quiet_benchmark_20260912.ps1') -Label $Label -Seconds $Seconds -Rate $Rate -Teensy:$Teensy
}
finally {
 $process.ProcessorAffinity=[IntPtr]$old
 $report.restored=$process.ProcessorAffinity.ToInt64()
 $report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $record -Encoding utf8
}
