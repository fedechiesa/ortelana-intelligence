param([switch]$Historical)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
if ($Historical) {
    if (-not (Test-Path -LiteralPath 'data/private/sales.csv') -or -not (Test-Path -LiteralPath 'data/private/master.json')) {
        throw 'Historical mode needs the authorized original files in data/private. See data/README.md.'
    }
    $env:DATA_MODE = 'historical'
}
docker compose up --build -d --wait --wait-timeout 180
if ($LASTEXITCODE -ne 0) { throw 'Startup failed. Run scripts/diagnose.ps1.' }
Write-Host 'Workspace: http://localhost:5173 | API docs: http://localhost:8001/docs'
Write-Host 'Grafana: http://localhost:3000 | n8n: http://localhost:5678 | Prometheus: http://localhost:9090'
Write-Host 'Schedules remain unpublished. The n8n editor requires its local owner setup on first visit.'
