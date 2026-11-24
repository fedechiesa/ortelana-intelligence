param([switch]$Services, [switch]$Browser)
$ErrorActionPreference='Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
function Assert-Command { if ($LASTEXITCODE -ne 0) { throw 'Validation command failed' } }
$python = Join-Path $PWD '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create the Python environment first; see README.md.' }
& $python -m ruff check --config backend/pyproject.toml backend scripts
Assert-Command
& $python -m ruff format --config backend/pyproject.toml --check backend scripts
Assert-Command
& $python -m mypy --config-file backend/pyproject.toml backend/app
Assert-Command
if ($Services) { $env:TEST_DATABASE_URL='postgresql+psycopg://ortelana:demo-db-local@127.0.0.1:5433/ortelana_test' }
& $python -m pytest backend/tests -q
Assert-Command
Push-Location frontend
try {
    npm run lint; Assert-Command
    npm run format:check; Assert-Command
    npm test; Assert-Command
    npm run build; Assert-Command
    if ($Browser) { npm run test:e2e; Assert-Command }
} finally { Pop-Location }
docker compose config --quiet
Assert-Command
if ($Services) {
    & $python scripts/validate_stack.py --restart-backend; Assert-Command
    & $python scripts/validate_n8n.py; Assert-Command
}
