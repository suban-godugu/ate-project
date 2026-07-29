# Stop full VERILUMEN local stack (agents/UIs + API + ARQ + dashboard + Redis + MinIO).
# Does NOT stop PostgreSQL.
# Usage: powershell -ExecutionPolicy Bypass -File c:\office\stop-stack.ps1

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "Stopping agents + UIs..."
& "c:\office\stop-agents.ps1"

function Stop-PortListeners([int[]]$Ports) {
  $killed = @{}
  foreach ($port in $Ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
      $procId = $c.OwningProcess
      if (-not $procId -or $killed.ContainsKey($procId)) { continue }
      try {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$procId" -ErrorAction SilentlyContinue
        $name = if ($proc) { $proc.Name } else { "?" }
        Stop-Process -Id $procId -Force -ErrorAction Stop
        $killed[$procId] = $true
        Write-Host "  killed PID $procId ($name) on :$port"
      } catch {
        Write-Host "  could not kill PID $procId on :$port - $($_.Exception.Message)"
      }
    }
  }
}

Write-Host "Stopping backend / dashboard / Redis / MinIO listeners..."
Stop-PortListeners @(8000, 3000, 6379, 9000, 9001)

Write-Host "Stopping ARQ worker processes..."
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'arq\s+app\.workers\.WorkerSettings' } |
  ForEach-Object {
    try {
      Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
      Write-Host "  killed ARQ PID $($_.ProcessId)"
    } catch {
      Write-Host "  could not kill ARQ PID $($_.ProcessId)"
    }
  }

# Also stop uvicorn reload children / next that may linger on those ports after parent kill
Start-Sleep -Seconds 1
Stop-PortListeners @(8000, 3000, 6379, 9000, 9001)
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'uvicorn\s+app\.main:app.*port\s+8000' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Write-Host ""
$ports = 5432, 6379, 9000, 8000, 3000, 8011, 8021, 3020, 8031, 3030
foreach ($port in $ports) {
  $up = [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
  $label = if ($port -eq 5432) { " (Postgres kept)" } else { "" }
  Write-Host ("  :{0} {1}{2}" -f $port, $(if ($up) { "still UP" } else { "down" }), $label)
}

$arqLeft = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'arq\s+app\.workers\.WorkerSettings' }
Write-Host ("  ARQ {0}" -f $(if ($arqLeft) { "still UP" } else { "down" }))
Write-Host ""
