# Start Pattern + Failure + Scan Diagnosis + Recommendation agents and their UIs.
# Usage:  powershell -ExecutionPolicy Bypass -File .\start-agents.ps1
# Stop:   powershell -ExecutionPolicy Bypass -File .\stop-agents.ps1

$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
$ServiceKey = "dev-service-key-change-me"
$AgentOutput = Join-Path $Root "runtime\output"
$UploadInput = Join-Path $Root "runtime\input"
$LogDir = Join-Path $Root "runtime\logs"

$PatternRoot = Join-Path $Root "agents\pattern-analysis"
$PatternRecRoot = Join-Path $Root "agents\pattern-recommendation"
$FailureRoot = Join-Path $Root "agents\failure-analysis"
$FailureUi   = Join-Path $FailureRoot "ate-dashboard"
$ScanRoot    = Join-Path $Root "agents\scan-diagnosis"
$ScanUi      = Join-Path $ScanRoot "frontend"
$ScanDebugRecRoot = Join-Path $Root "agents\scan-debug-recommendation"
$TestOptRoot = Join-Path $Root "agents\test-optimization"
$PatternRecUi = Join-Path $PatternRecRoot "frontend"
$ScanDebugRecUi = Join-Path $ScanDebugRecRoot "frontend"
$TestOptBackend = Join-Path $TestOptRoot "backend"
$TestOptUi = Join-Path $TestOptRoot "frontend"

New-Item -ItemType Directory -Force -Path $LogDir, $AgentOutput, $UploadInput | Out-Null

function Test-Port([int]$Port) {
  return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
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
Write-Host "VERILUMEN agents + UIs"
Write-Host "======================"

if (Test-Port 8011) { Write-Host "  skip Pattern API/UI :8011 (already up)" }
else {
  Start-Window "Pattern Agent :8011" $PatternRoot @"
`$env:VERILUMEN_SERVICE_KEY = '$ServiceKey'
`$env:AGENT_OUTPUT_ROOT = '$AgentOutput'
`$env:UPLOAD_INPUT_ROOT = '$UploadInput'
python -m uvicorn server:app --host 127.0.0.1 --port 8011
"@
}

if (Test-Port 8021) { Write-Host "  skip Failure API :8021 (already up)" }
else {
  Start-Window "Failure Agent API :8021" $FailureRoot @"
Remove-Item Env:DATABASE_USER,Env:DATABASE_PASSWORD,Env:DATABASE_NAME,Env:DATABASE_URL -ErrorAction SilentlyContinue
`$env:VERILUMEN_SERVICE_KEY = '$ServiceKey'
`$env:AGENT_OUTPUT_ROOT = '$AgentOutput'
`$env:UPLOAD_INPUT_ROOT = '$UploadInput'
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8021
"@
}

if (Test-Port 3020) { Write-Host "  skip Failure UI :3020 (already up)" }
else {
  Start-Window "Failure Agent UI :3020" $FailureUi @"
`$env:ATE_API_PROXY = 'http://127.0.0.1:8021'
`$env:BACKEND_URL = 'http://127.0.0.1:8021'
`$env:NEXT_EMBED_BASE_PATH = '/embed/failure'
`$env:NEXT_PUBLIC_EMBED_BASE_PATH = '/embed/failure'
npm run dev -- -p 3020 -H 127.0.0.1
"@
}

if (Test-Port 8031) { Write-Host "  skip Scan API :8031 (already up)" }
else {
  Start-Window "Scan Diagnosis API :8031" $ScanRoot @"
`$env:VERILUMEN_SERVICE_KEY = '$ServiceKey'
`$env:AGENT_OUTPUT_ROOT = '$AgentOutput'
`$env:UPLOAD_INPUT_ROOT = '$UploadInput'
python -m uvicorn api.main:app --host 127.0.0.1 --port 8031
"@
}

if (Test-Port 3030) { Write-Host "  skip Scan UI :3030 (already up)" }
else {
  Start-Window "Scan Diagnosis UI :3030" $ScanUi @"
`$env:ATE_API_PROXY = 'http://127.0.0.1:8031'
`$env:BACKEND_URL = 'http://127.0.0.1:8031'
`$env:NEXT_EMBED_BASE_PATH = '/embed/scan'
`$env:NEXT_PUBLIC_API_BASE = '/embed/scan'
npx next dev -p 3030 -H 127.0.0.1
"@
}

if (Test-Port 8041) { Write-Host "  skip Pattern Recommendation API/UI :8041 (already up)" }
else {
  Start-Window "Pattern Recommendation API :8041" $PatternRecRoot @"
`$env:BACKEND_HOST = '127.0.0.1'
`$env:BACKEND_PORT = '8041'
`$env:PYTHONPATH = '.'
`$env:UPLOAD_INPUT_ROOT = '$UploadInput'
`$env:AGENT_OUTPUT_ROOT = '$AgentOutput'
`$env:BACKEND_DATA_DIR = '$UploadInput\pattern-recommendation'
`$env:BACKEND_OUTPUT_DIR = '$AgentOutput\pattern-recommendation'
python -m backend.app
"@
}

if (Test-Port 3041) { Write-Host "  skip Pattern Recommendation UI :3041 (already up)" }
else {
  Start-Window "Pattern Recommendation UI :3041" $PatternRecUi @"
`$env:VITE_API_PROXY_TARGET = 'http://127.0.0.1:8041'
`$env:VITE_API_BASE_URL = '/embed/pattern-rec/api-proxy'
`$env:VITE_EMBED_BASE = '/embed/pattern-rec/'
`$env:VITE_UI_PORT = '3041'
npm run dev -- --host 127.0.0.1 --port 3041
"@
}

if (Test-Port 8042) { Write-Host "  skip Scan Debug Recommendation API :8042 (already up)" }
else {
  Start-Window "Scan Debug Recommendation API :8042" $ScanDebugRecRoot @"
`$env:PYTHONPATH = '.'
`$env:UPLOAD_INPUT_ROOT = '$UploadInput'
`$env:AGENT_OUTPUT_ROOT = '$AgentOutput'
`$env:SCAN_DEBUG_DATA_DIR = '$UploadInput\scan-debug-recommendation'
`$env:SCAN_DEBUG_OUTPUT_DIR = '$AgentOutput\scan-debug-recommendation'
`$env:AUTO_TRAIN_ON_STARTUP = 'false'
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8042
"@
}

if (Test-Port 3042) { Write-Host "  skip Scan Debug Recommendation UI :3042 (already up)" }
else {
  Start-Window "Scan Debug Recommendation UI :3042" $ScanDebugRecUi @"
`$env:NEXT_PUBLIC_API_MODE = 'live'
`$env:NEXT_PUBLIC_API_BASE_URL = 'http://127.0.0.1:8042'
`$env:NEXT_EMBED_BASE_PATH = '/embed/scan-debug-rec'
`$env:NEXT_PUBLIC_EMBED_BASE_PATH = '/embed/scan-debug-rec'
`$env:API_PROXY_TARGET = 'http://127.0.0.1:8042'
`$env:PORT = '3042'
npm run dev -- --port 3042 -H 127.0.0.1
"@
}

if (Test-Port 8043) { Write-Host "  skip Test Optimization API :8043 (already up)" }
else {
  Start-Window "Test Optimization API :8043" $TestOptBackend @"
`$env:UPLOAD_INPUT_ROOT = '$UploadInput'
`$env:AGENT_OUTPUT_ROOT = '$AgentOutput'
`$env:INPUT_DIR = '$UploadInput\test-optimization'
`$env:DATA_DIR = '$AgentOutput\test-optimization'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8043
"@
}

if (Test-Port 3043) { Write-Host "  skip Test Optimization UI :3043 (already up)" }
else {
  Start-Window "Test Optimization UI :3043" $TestOptUi @"
`$env:VITE_API_PROXY_TARGET = 'http://127.0.0.1:8043'
`$env:VITE_API_BASE_URL = '/embed/test-opt/api-proxy/api/v1'
`$env:VITE_EMBED_BASE = '/embed/test-opt/'
`$env:VITE_UI_PORT = '3043'
npm run dev
"@
}

Write-Host ""
Write-Host "Waiting for ports..."
$deadline = (Get-Date).AddSeconds(45)
$ports = @(
  @{ Name = "Pattern API/UI"; Port = 8011 },
  @{ Name = "Failure API";    Port = 8021 },
  @{ Name = "Failure UI";     Port = 3020 },
  @{ Name = "Scan API";       Port = 8031 },
  @{ Name = "Scan UI";        Port = 3030 },
  @{ Name = "Pattern Rec API"; Port = 8041 },
  @{ Name = "Pattern Rec UI";  Port = 3041 },
  @{ Name = "Scan Debug Rec API"; Port = 8042 },
  @{ Name = "Scan Debug Rec UI";  Port = 3042 },
  @{ Name = "Test Optimization API"; Port = 8043 },
  @{ Name = "Test Optimization UI";  Port = 3043 }
)
do {
  $down = @($ports | Where-Object { -not (Test-Port $_.Port) })
  if ($down.Count -eq 0) { break }
  Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)

Write-Host ""
foreach ($p in $ports) {
  $ok = Test-Port $p.Port
  Write-Host ("  [{0}] {1,-24} :{2}" -f ($(if ($ok) { "UP" } else { "DOWN" }), $p.Name, $p.Port))
}
Write-Host ""
Write-Host "Open all agent UIs via Dashboard: http://localhost:3000/dashboard"
Write-Host "Stop: powershell -ExecutionPolicy Bypass -File .\stop-agents.ps1"
