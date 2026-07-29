# Start Scan Diagnosis Agent on a single public port (:8030).
# UI (Next.js) listens on 8030 and proxies /api + /docs to the local API on :18030.
#
# Run from repo root:  .\start-scan-diagnosis.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"

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

Clear-PortListener 8030
Clear-PortListener 18030
Clear-PortListener 3030

$env:PYTHONPATH = $RepoRoot
$env:ATE_API_PROXY = "http://127.0.0.1:18030"

Write-Host "Starting Scan Diagnosis API on :18030 (internal)..."
Start-Process -FilePath "python" -ArgumentList @(
    "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "18030"
) -WorkingDirectory $RepoRoot -WindowStyle Minimized

$deadline = (Get-Date).AddSeconds(30)
while (-not (Test-PortOpen 18030)) {
    if ((Get-Date) -gt $deadline) {
        Write-Error "API did not become ready on :18030"
    }
    Start-Sleep -Milliseconds 500
}

Set-Location $FrontendDir
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

Write-Host "Starting Scan Diagnosis UI on :8030 (public, proxies API)..."
Write-Host "Open http://127.0.0.1:8030"
npm run dev
