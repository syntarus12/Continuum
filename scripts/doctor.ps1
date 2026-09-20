$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
docker compose config --quiet
docker compose ps

$apiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$apiUrl = "http://127.0.0.1:$apiPort"
for ($i = 0; $i -lt 30; $i++) {
    try {
        $health = Invoke-RestMethod "$apiUrl/health"
        Write-Host "API health: $($health | ConvertTo-Json -Compress)"
        $ready = Invoke-RestMethod "$apiUrl/ready"
        Write-Host "API ready: $($ready | ConvertTo-Json -Compress)"
        exit 0
    } catch {
        Start-Sleep -Seconds 2
    }
}
throw "Continuum did not become ready. Inspect logs with: docker compose logs --tail=200 backend"
