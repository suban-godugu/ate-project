# Start Failure Analysis Agent API (:8000) + Next dashboard (:3000).
# Run from repo root:  .\start-dashboard.ps1
#
# Pins cwd for the dashboard so Turbopack cannot pick a parent lockfile
# (e.g. C:\Users\hsmak\package-lock.json) as the workspace root.

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$DashboardDir = Join-Path $RepoRoot "ate-dashboard"

if (-not (Test-Path (Join-Path $DashboardDir "package.json"))) {
    Write-Error "ate-dashboard not found at $DashboardDir"
}

function Test-PortOpen([int]$Port) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect("127.0.0.1", $Port)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}

function Clear-PortListener([int]$Port) {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        $procId = $c.OwningProcess
        if ($procId -and $procId -ne 0) {
            Write-Host "Stopping process $procId on port $Port..."
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

# Optional: free a stale Next listener left by a soft-killed process.
if ($env:FA_CLEAR_PORT_3000 -eq "1" -or $args -contains "-ClearPort") {
    Clear-PortListener 3000
}

$env:PYTHONPATH = $RepoRoot

if (-not (Test-PortOpen 8000)) {
    Write-Host "Starting API on :8000..."
    Start-Process -FilePath "python" -ArgumentList @(
        "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"
    ) -WorkingDirectory $RepoRoot -WindowStyle Normal
    Start-Sleep -Seconds 2
} else {
    Write-Host "API already listening on :8000"
}

Set-Location $DashboardDir
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dashboard dependencies..."
    npm install
}

Write-Host "Starting dashboard (cwd=$DashboardDir)..."
Write-Host "Open http://127.0.0.1:3000/overview"
npm run dev
