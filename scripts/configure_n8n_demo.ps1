param([string]$Token = 'demo-automation-local')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (Test-Path -LiteralPath '.env') {
    $tokenSetting = Get-Content -LiteralPath '.env' | Where-Object { $_ -match '^AUTOMATION_TOKEN=' } | Select-Object -First 1
    if ($tokenSetting) { $Token = $tokenSetting.Substring('AUTOMATION_TOKEN='.Length).Trim('"', "'") }
}
# Pipe credentials through stdin. They are encrypted in the project n8n volume, never exported into Git.
$credential = ConvertTo-Json -Depth 5 -InputObject @(@{ id='ortelanaApiHeader'; name='Ortelana API automation'; type='httpHeaderAuth';
    data=@{name='Authorization';value="Bearer $Token"} })
$credential | docker compose exec -T n8n sh -c 'umask 077; cat > /tmp/ortelana-credential.json; n8n import:credentials --input=/tmp/ortelana-credential.json; result=$?; rm -f /tmp/ortelana-credential.json; exit $result'
if ($LASTEXITCODE -ne 0) { throw 'n8n credential import failed' }
Write-Host 'Local automation credential configured. Workflows remain unpublished.'
