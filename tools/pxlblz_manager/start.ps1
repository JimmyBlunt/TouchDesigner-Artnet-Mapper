$ErrorActionPreference = 'Stop'
$managerDirectory = $PSScriptRoot
try { $null = Invoke-RestMethod 'http://127.0.0.1:9990/api/state' -TimeoutSec 2 }
catch {
    $nodePath = (Get-Command node).Source
    Start-Process -FilePath $nodePath -ArgumentList ('"' + (Join-Path $managerDirectory 'service.mjs') + '"') -WorkingDirectory $managerDirectory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $managerDirectory 'service.log') -RedirectStandardError (Join-Path $managerDirectory 'service-error.log')
}
for ($managerAttempt = 0; $managerAttempt -lt 30; $managerAttempt++) {
    try { $null = Invoke-RestMethod 'http://127.0.0.1:9990/api/state' -TimeoutSec 1; break }
    catch { Start-Sleep -Milliseconds 200 }
}
Start-Process 'http://127.0.0.1:9990/'
