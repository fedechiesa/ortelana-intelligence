$ErrorActionPreference = 'Continue'
Set-Location (Split-Path -Parent $PSScriptRoot)
docker version
docker compose config --quiet
docker compose ps
$services = @{ 'API'='http://127.0.0.1:8001/health/ready'; 'UI'='http://127.0.0.1:5173/health';
    'Grafana'='http://127.0.0.1:3000/api/health'; 'n8n'='http://127.0.0.1:5678/healthz';
    'Prometheus'='http://127.0.0.1:9090/-/ready' }
foreach ($service in $services.GetEnumerator()) {
    try { $response=Invoke-WebRequest -Uri $service.Value -UseBasicParsing -TimeoutSec 5; Write-Host "$($service.Key): HTTP $($response.StatusCode)" }
    catch { Write-Warning "$($service.Key): unavailable" }
}
docker compose logs --tail 20 backend n8n
