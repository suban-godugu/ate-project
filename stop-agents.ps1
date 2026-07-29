# Stop Pattern + Failure + Scan Diagnosis agents and their UIs.
# Usage: powershell -ExecutionPolicy Bypass -File c:\office\stop-agents.ps1

$ErrorActionPreference = "Continue"
$ports = 8011, 8021, 3020, 8031, 3030, 8041, 3041, 8042, 3042, 8043, 3043

Write-Host ""
Write-Host "Stopping agent / UI listeners on: $($ports -join ', ')"
Write-Host ""

$killed = @{}
foreach ($port in $ports) {
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

Start-Sleep -Seconds 1
Write-Host ""
foreach ($port in $ports) {
  $up = [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
  Write-Host ("  :{0} {1}" -f $port, $(if ($up) { "still UP" } else { "down" }))
}
Write-Host ""
