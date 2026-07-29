# Start full VERILUMEN local stack (infra + API + ARQ + dashboard + agents/UIs).
# Usage:  powershell -ExecutionPolicy Bypass -File .\start-stack.ps1
# Stop:   powershell -ExecutionPolicy Bypass -File .\stop-stack.ps1
#
# Requires: PostgreSQL Windows service (or local Postgres) on :5432, Python 3.11+, Node 20+, Redis, MinIO.

$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
$BackendRoot = Join-Path $Root "backend"
$DashboardRoot = Join-Path $Root "dashboard"
$MinioData = Join-Path $Root "runtime\minio-data"

function Test-Port([int]$Port) {
  return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
}

function Test-ArqRunning {
  $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'arq\s+app\.workers\.WorkerSettings' }
  return [bool]$procs
}

function Start-Window([string]$Title, [string]$WorkDir, [string]$Command) {
  Write-Host "  starting: $Title"
  Start-Process -FilePath "powershell.exe" -WorkingDirectory $WorkDir -ArgumentList @(
    "-NoExit",
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "`$Host.UI.RawUI.WindowTitle = '$Title'; $Command"
  )
}

Write-Host ""
Write-Host "VERILUMEN full stack"
Write-Host "===================="

if (Test-Port 5432) { Write-Host "  OK Postgres :5432" }
else { Write-Host "  WARN Postgres :5432 is DOWN - start PostgreSQL first" }

if (Test-Port 6379) { Write-Host "  skip Redis :6379 (already up)" }
else { Start-Window "Redis :6379" $Root "redis-server --port 6379" }

if (Test-Port 9000) { Write-Host "  skip MinIO :9000 (already up)" }
else {
  New-Item -ItemType Directory -Force -Path $MinioData | Out-Null
  $minioCmd = ('$env:MINIO_ROOT_USER = ''minioadmin''; $env:MINIO_ROOT_PASSWORD = ''minioadmin''; minio server ''{0}'' --address '':9000'' --console-address '':9001''' -f $MinioData)
  Start-Window "MinIO :9000" $Root $minioCmd
}

$infraDeadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $infraDeadline) {
  if ((Test-Port 6379) -and (Test-Port 9000)) { break }
  Start-Sleep -Seconds 1
}

if (Test-Port 8000) { Write-Host "  skip Backend API :8000 (already up)" }
else {
  Start-Window "VERILUMEN API :8000" $BackendRoot `
    "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
}

if (Test-ArqRunning) { Write-Host "  skip ARQ worker (already running)" }
else {
  Start-Window "VERILUMEN ARQ worker" $BackendRoot `
    "python -m arq app.workers.WorkerSettings"
}

if (Test-Port 3000) { Write-Host "  skip Dashboard :3000 (already up)" }
else {
  Start-Window "VERILUMEN Dashboard :3000" $DashboardRoot "npm run dev"
}

Write-Host ""
Write-Host "Starting agents + UIs..."
& (Join-Path $Root "start-agents.ps1")

Write-Host ""
Write-Host "URLs"
Write-Host "  Dashboard:  http://localhost:3000/dashboard"
Write-Host "  Backend:    http://127.0.0.1:8000/docs"
Write-Host "  MinIO:      http://127.0.0.1:9001  (minioadmin / minioadmin)"
Write-Host ""
Write-Host "Stop: powershell -ExecutionPolicy Bypass -File .\stop-stack.ps1"
