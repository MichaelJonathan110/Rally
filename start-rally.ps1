# RALLY - start both servers detached so they survive the launching session.
# Usage:  powershell -ExecutionPolicy Bypass -File C:\Users\kohja\rally\start-rally.ps1
$ErrorActionPreference = 'SilentlyContinue'
$Root = 'C:\Users\kohja\rally'
$Logs = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

function Stop-Port($port) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}

# --- kill stale listeners ---
Stop-Port 8001
Stop-Port 4173
Start-Sleep -Seconds 1

# --- backend: uvicorn on SQLite, port 8001 ---
Start-Process -FilePath (Join-Path $Root 'apps\api\.venv\Scripts\python.exe') `
  -ArgumentList 'scripts\serve_sqlite.py' `
  -WorkingDirectory (Join-Path $Root 'apps\api') `
  -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $Logs 'api.out.log') `
  -RedirectStandardError  (Join-Path $Logs 'api.err.log')

# --- frontend: vite preview on 4173 ---
$Npm = 'C:\Program Files\nodejs\npm.cmd'
Start-Process -FilePath $Npm `
  -ArgumentList 'run','preview','--','--port','4173','--host','127.0.0.1' `
  -WorkingDirectory (Join-Path $Root 'apps\web') `
  -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $Logs 'web.out.log') `
  -RedirectStandardError  (Join-Path $Logs 'web.err.log')

# --- wait for readiness ---
$ok = $false
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Seconds 1
  $b = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
  $f = Get-NetTCPConnection -LocalPort 4173 -State Listen -ErrorAction SilentlyContinue
  if ($b -and $f) { $ok = $true; break }
}
Write-Host ("backend 8001 LISTENING: " + [bool](Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue))
Write-Host ("frontend 4173 LISTENING: " + [bool](Get-NetTCPConnection -LocalPort 4173 -State Listen -ErrorAction SilentlyContinue))
Write-Host ("both ready: " + $ok)
