# Troubleshooting and operations

Run `scripts/diagnose.ps1` first. It checks Compose configuration, actual container states and HTTP readiness without printing environment secrets. Startup logs: `docker compose logs --tail 100 backend n8n grafana`. Do not publish raw logs or n8n execution dumps without reviewing them.

## Docker Desktop unavailable

Start Docker Desktop and wait for its Linux engine. `docker info` must succeed. The initial environment had an installed CLI and a stopped engine; after startup all six services were validated. Do not delete volumes to fix readiness errors: they contain evidence, decisions, n8n credentials and Grafana state.

## Host networking or port conflicts

The development machine already had a service on 8000; this project publishes API port 8001. Do not terminate unrelated processes. Change only this project's Compose mapping and Vite proxy if another required port is occupied. On this Windows environment, direct Python `localhost` database connections stalled while `127.0.0.1` worked immediately; host DSNs therefore use 127.0.0.1. Docker services use `postgres:5432`.

## Authentication and decisions

401 means invalid/missing token; 403 means an insufficient role. Use supervisor access for reviews and policy writes. 409 on a second decision is expected and cannot be resolved by overwriting the record. Check `/executions/{id}`, `/decisions` and `/audit?execution_id={id}` to inspect the authoritative state. A changed policy does not rewrite old evidence.

## Database migrations and recovery

Migrations run before API startup. `docker compose exec backend alembic current` should show the latest revision. A failed migration makes startup fail, rather than serving an incompatible schema. Destructive downgrades are disabled. Back up the project volume before changing the schema.

The cluster uses `ortelana_admin`; the API uses restricted `ortelana`. Bootstrap scripts run only on a new volume, so editing password environment values does not rotate passwords in an existing database. Do not delete evidence volumes to change credentials. `scripts/validate_initialization.ps1` verifies a fresh setup in isolated temporary containers, without touching existing volumes.

An interrupted review remains pending after restart. Committed decisions in RESUMING are automatically reconciled. ERROR runs require an authenticated supervisor POST to `/executions/{id}/recover`; fix the underlying problem first. Technical failures do not become commercial critical risks. Duration measures processing, not time spent waiting for a human.

## n8n

The editor needs its first local owner account. Workflows/automation credential are bootstrapped independently and remain unpublished. Explicitly import changed workflow exports; the startup marker prevents overwriting user edits on every restart. `scripts/configure_n8n_demo.ps1` updates the credential after a token change. Restart n8n if its editor does not reflect a CLI import.

For CLI execution alongside a running server, use `N8N_RUNNERS_BROKER_PORT=5680` to avoid port 5679 collision. The optional Python runner warning is unrelated to these HTTP/Set/Switch/Wait workflows. Never enable the schedule simply to prove import success; the five deterministic CLI scenarios validate actual execution without unattended scheduled runs.

## Grafana / Prometheus

After restarting the API, allow one scrape interval before expecting `up=1`. Empty rate windows are normal. Check datasource health and execute queries with `scripts/validate_stack.py`. Sales charts show metres, not revenue. Seasonal and missing-cohort limitations apply equally in Grafana and the app. Grafana historical sales panels choose the most recently imported snapshot; they do not combine multiple copies of a source.

## Local tooling

Use Python 3.12 and Node 22. Locked Python dependencies can be installed through uv even if Windows `venv`'s initial `ensurepip` fails. For sandbox-restricted temporary paths, use a fresh project-local pytest `--basetemp=.local/<new-test-directory>` or the normal unsandboxed developer shell. Do not point `--basetemp` at existing user files: pytest owns and cleans that directory.

Screenshots are captured from the actual running demo. Chart animation is disabled to avoid capturing half-drawn data. Browser test failures retain a Playwright trace under ignored `frontend/test-results`; no captured evidence is represented as successful until the assertion passes.
