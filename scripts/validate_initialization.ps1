# Validate a clean PostgreSQL initialization without touching existing project volumes or host ports.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$suffix = [guid]::NewGuid().ToString('N').Substring(0,8)
$dbName = "ortelana-init-$suffix"
$apiName = "ortelana-init-api-$suffix"
$dbCreated = $false
$apiCreated = $false
$initPath = (Resolve-Path -LiteralPath 'infrastructure/postgres/init.sh').Path
try {
    docker run --rm -d --name $dbName --network ortelana-intelligence_internal `
        -e POSTGRES_USER=ortelana_admin -e POSTGRES_PASSWORD=demo-postgres-admin-local `
        -e POSTGRES_DB=ortelana -e APP_DATABASE_PASSWORD=demo-db-local `
        -e GRAFANA_DB_PASSWORD=demo-grafana-reader-local `
        --mount "type=bind,source=$initPath,target=/docker-entrypoint-initdb.d/init.sh,readonly" `
        postgres:16-alpine@sha256:721873c34ceb9f8d8fc265984940dc982404c105f19ad51be9fdc5970a6080ea | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Isolated PostgreSQL creation failed' }
    $dbCreated = $true
    $deadline = (Get-Date).AddSeconds(40)
    do {
        docker exec $dbName pg_isready -h 127.0.0.1 -U ortelana_admin -d ortelana 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    if ($LASTEXITCODE -ne 0) { throw 'Fresh PostgreSQL did not become ready' }
    Write-Host 'PASS: clean PostgreSQL initialization completed'
    docker compose run --rm -d --no-deps --name $apiName `
        -e "DATABASE_URL=postgresql+psycopg://ortelana:demo-db-local@${dbName}:5432/ortelana" `
        -e DATA_MODE=demo backend | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Isolated backend creation failed' }
    $apiCreated = $true
    $deadline = (Get-Date).AddSeconds(60)
    $probe = "fetch('http://${apiName}:8000/health/ready').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
    do {
        docker compose exec -T n8n node -e $probe 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    if ($LASTEXITCODE -ne 0) { throw 'Fresh migrations or checkpoint initialization failed' }
    $scenario = @"
(async()=>{
 const base='http://${apiName}:8000';
 const headers={'Content-Type':'application/json',Authorization:'Bearer demo-supervisor-local','Idempotency-Key':'clean-init-'+Date.now()};
 const result=await fetch(base+'/analizar',{method:'POST',headers,body:JSON.stringify({producto_id:'DEMO-003'}),signal:AbortSignal.timeout(10000)});
 if(!result.ok)throw new Error('Clean analysis failed: '+result.status);
 const e=await result.json();
 if(e.estado!=='CRITICO'||e.approval_status!=='PENDING')throw new Error('Incorrect clean review state');
 const response=await fetch(base+'/decision',{method:'POST',headers,body:JSON.stringify({ejecucion_id:e.ejecucion_id,decision:'APROBADO',comentario:'SYNTHETIC clean initialization validation'}),signal:AbortSignal.timeout(10000)});
 if(!response.ok)throw new Error('Clean decision failed: '+response.status);
 const decision=await response.json();
 if(decision.technical_status!=='COMPLETED'||!decision.simulated_authorization)throw new Error('Clean graph did not resume');
 console.log('PASS: fresh migrations, import, PostgreSQL checkpoints, critical interruption and authenticated approval');
})().catch(error=>{console.error(error.message);process.exit(1)});
"@
    docker compose exec -T n8n node -e $scenario
    if ($LASTEXITCODE -ne 0) { throw 'Clean API/graph validation failed' }
    docker exec -e PGPASSWORD=demo-db-local $dbName psql -h 127.0.0.1 -U ortelana -d ortelana `
        -c "SELECT current_user,rolsuper,rolcreatedb,rolcreaterole,rolreplication FROM pg_roles WHERE rolname=current_user;"
    if ($LASTEXITCODE -ne 0) { throw 'Application-role connection failed' }
} finally {
    if ($apiCreated) { docker stop $apiName | Out-Null }
    if ($dbCreated) { docker stop $dbName | Out-Null }
}
