# Ortelana Intelligence

**Commercial analytics, durable human review and observable automation.**

A portfolio application that turns textile sales reports into reproducible comparisons, traceable recommendations and accountable decisions. A React workspace, Python API and deterministic LangGraph workflow run together in a six-service local stack.

[![Continuous integration](https://github.com/fedechiesa/ortelana-intelligence/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/fedechiesa/ortelana-intelligence/actions/workflows/ci.yml)
[![Full stack](https://github.com/fedechiesa/ortelana-intelligence/actions/workflows/stack.yml/badge.svg?branch=main)](https://github.com/fedechiesa/ortelana-intelligence/actions/workflows/stack.yml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-19-149ECA?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)

![Actual application running on synthetic data](docs/screenshots/overview-demo.png)

## Business problem and value

A sales decline needs a trustworthy comparison before it needs an action. Reports can use different periods, omit observations or hide a declining product behind a healthy network average. Spreadsheet summaries also rarely preserve the policy, evidence and reviewer responsible for a decision.

Ortelana compares compatible reporting-year cohorts, identifies product and branch risk, and preserves the evidence behind each execution. Critical findings pause at a durable checkpoint until an authenticated supervisor approves or rejects a **simulated** commercial authorization. The result is a demonstrable path from source data to analysis, human authority and operational monitoring.

This is an independent personal continuation of an academic case from ORT's Artificial Intelligence and Data Science program. It is not an official ORT product or the original group submission. Only independently generated synthetic datasets are distributed. See [attribution and rights](THIRD_PARTY_NOTICES.md).

## Main capabilities

- Six connected views: Overview, Sales Analytics, Agent Executions, Human Review, System Monitoring and Settings. Responsive navigation, light/dark themes and explicit loading, empty and error states.
- Sales trends, product/branch rankings, observed versus matched totals, comparison coverage and versioned risk policies. Missing observations remain unknown; zero baselines do not produce invented percentages.
- Typed LangGraph state, three parallel specialists, a reducer, risk consolidation and persisted PostgreSQL checkpoints.
- Independent technical, commercial and approval states. Critical segment findings require review even when the network average is normal.
- Operator, supervisor and automation roles; database-enforced idempotency, immutable evidence, append-only decisions/audit and concurrent decision protection.
- Manual and weekly n8n workflow exports with authenticated HTTP integration, distinct outcome routes and one bounded retry for transient failures.
- Real Prometheus instrumentation and two provisioned Grafana dashboards backed by API metrics and a read-only PostgreSQL datasource.

**AI boundary:** the processing agents use deterministic Python calculations and policy rules. LangGraph coordinates execution; no LLM, trained predictive model, embeddings or generative reasoning is implemented. Recommendations use fixed templates. No model API key or paid service is required. Orders, prices and inventory are never modified.

## Real screenshots

These captures come from the running application and its labeled synthetic demo, rather than design mockups.

| Human review | Decision history |
| --- | --- |
| ![Critical evidence and supervisor review](docs/screenshots/critical-review-demo.png) | ![Persisted decision history](docs/screenshots/decision-history-demo.png) |

| Operational monitoring | Business intelligence |
| --- | --- |
| ![Grafana operations dashboard](docs/screenshots/grafana-operations-demo.png) | ![Grafana business dashboard](docs/screenshots/grafana-business-demo.png) |

[Mobile capture](docs/screenshots/mobile-demo.png). Browser tests exercise the actual API and refresh the captures.

## Architecture and processing

```mermaid
flowchart LR
    UI[React workspace] --> API[FastAPI: authentication and authority]
    N[n8n: manual and inactive schedule] --> API
    API --> G[LangGraph deterministic agents]
    API --> DB[(PostgreSQL: datasets, evidence, decisions, audit)]
    G --> DB
    G --> CP[(PostgreSQL checkpoints)]
    API -->|metrics| P[Prometheus]
    P --> GF[Grafana Operations]
    DB -->|read only| BI[Grafana Business Intelligence]
```

```mermaid
flowchart TD
    I[Validate source / pin immutable snapshot] --> C[Coordinator: validate filters]
    C --> S[Sales: matched totals and coverage]
    C --> P[Products: rankings and changes]
    C --> B[Branches: rankings and changes]
    S --> R[Join: highest supported risk]
    P --> R
    B --> R
    R --> E[Persist report, evidence and policy]
    E --> Q{Any critical finding?}
    Q -->|No| F[Complete]
    Q -->|Yes| H[Checkpoint / interrupt for human review]
    H --> D[Authenticated decision committed in PostgreSQL]
    D --> A[Resume and read authoritative decision]
    A --> F
```

Sales, products and branches read the same snapshot and write separate state fields. An additive reducer merges their recorded steps. Risk runs after all three branches complete. `human_review` uses a real LangGraph interrupt; the resume payload cannot grant authorization. Recovery reconciles committed decisions with durable checkpoints after supported crash windows.

Calculations use Decimal values before display conversion. M/B/S reports contain monthly, bimonthly or semester periods; C/E denotes commercial seasons. Comparisons join compatible branch/product keys. Seasons can cross calendar boundaries, so charts show **reporting years**, without inferring calendar months. Read the [data model](docs/data-model.md), [agents](docs/agents.md), [architecture](docs/architecture/README.md) and [review guarantees](docs/human-review.md).

## Technology

| Area | Implementation |
| --- | --- |
| API and analytics | Python 3.12, FastAPI, Pydantic, Pandas/NumPy, Decimal, Tenacity |
| Orchestration | LangGraph with PostgreSQL checkpoint persistence |
| Persistence | PostgreSQL 16, SQLAlchemy, Alembic, integrity triggers and locks |
| Frontend | React 19, TypeScript 5.9, Vite 6, Tailwind CSS, Recharts, TanStack Query |
| Automation | n8n Community, inactive JSON workflow exports |
| Observability | Prometheus, Grafana, structured correlated logs |
| Verification | Pytest, Ruff, Mypy, ESLint, Vitest, Playwright, GitHub Actions |
| Infrastructure | Docker Compose, digest-pinned images, persistent named volumes |

Python and npm locks are committed. Node 22 is used by containers and CI. Validated service versions include PostgreSQL 16.15, n8n 2.49.5 and Grafana 13.3.2; Compose image digests determine the exact builds.

## Run the complete demo

Install Git and Docker Engine with Compose v2 or newer (Docker Desktop with Linux containers on Windows). The first run downloads several large images; an 8 GB Docker memory allocation is a practical recommendation, not a measured minimum.

```bash
git clone https://github.com/fedechiesa/ortelana-intelligence.git
cd ortelana-intelligence
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 180
docker compose ps
```

Demo defaults work without an environment file. For explicit local configuration, copy `.env.example` to `.env` (`cp` on Linux/macOS, `Copy-Item` in PowerShell) before starting. Migrations, synthetic import, n8n workflow/credential import and Grafana provisioning run automatically.

| Service | Local access |
| --- | --- |
| Application | [localhost:5173](http://localhost:5173) |
| API / Swagger | [localhost:8001/docs](http://localhost:8001/docs) |
| Grafana | [localhost:3000](http://localhost:3000), `admin` / `demo-grafana-local` |
| n8n editor | [localhost:5678](http://localhost:5678), create a local owner on first visit |
| Prometheus | [localhost:9090](http://localhost:9090) |
| PostgreSQL | `127.0.0.1:5433`, database/user `ortelana`, `demo-db-local` |

All published ports bind to loopback. The app offers public demo identities: `demo-operator-local` and `demo-supervisor-local`. Automation uses `demo-automation-local` and cannot approve. Replace these values and implement individual identity/HTTPS before shared deployment. See [security](SECURITY.md).

The demo contains six `DEMO-*` products, four demonstration branches and 240 reporting records for 2016–2025, generated by [`scripts/generate_demo.py`](scripts/generate_demo.py). Compare 2024→2025: `DEMO-001` yields −5% / NORMAL, `DEMO-002` −15% / ADVERTENCIA and `DEMO-003` −28% / CRITICO under policy v1. These are synthetic scenarios, not measured company performance.

Stop with `docker compose down`; named volumes retain evidence and decisions. Do not remove volumes as routine troubleshooting. `pwsh -File scripts/validate_initialization.ps1` tests clean initialization without touching existing volumes.

## Environment variables

Defaults are intentionally public **localhost demo configuration**. Real replacements belong only in an ignored environment file or deployment secret store.

| Variable | Purpose / demo default |
| --- | --- |
| `DATA_MODE` | `demo`; `historical` accepts separately authorized local files |
| `POSTGRES_PASSWORD` | Restricted application identity: `demo-db-local` |
| `POSTGRES_ADMIN_PASSWORD` | Cluster bootstrap only: `demo-postgres-admin-local` |
| `GRAFANA_DB_PASSWORD` | Read-only datasource: `demo-grafana-reader-local` |
| `GRAFANA_ADMIN_PASSWORD` | Local Grafana login: `demo-grafana-local` |
| `N8N_ENCRYPTION_KEY` | Local volume encryption: `demo-n8n-encryption-key-local-only` |
| `OPERATOR_TOKEN` / `SUPERVISOR_TOKEN` / `AUTOMATION_TOKEN` | Three separate demo identities listed above |
| `DATABASE_URL` | Host Python connection; Compose supplies its internal PostgreSQL DSN |

For host Python, `DATA_DIR` overrides the data directory, `CHECKPOINT_PATH` selects SQLite diagnostic checkpoints, and `DEPLOYMENT=production` rejects demo API tokens. These settings alone do not provide production security. Admin credentials are not passed to the API or n8n. Editing `.env` does not rotate passwords already stored in persistent volumes.

## Development and tests

Use Python 3.12, [uv](https://docs.astral.sh/uv/) and Node 22. From the repository root:

```bash
uv sync --project backend --frozen
uv run --project backend --frozen ruff check --config backend/pyproject.toml backend scripts
uv run --project backend --frozen ruff format --config backend/pyproject.toml --check backend scripts
uv run --project backend --frozen mypy --config-file backend/pyproject.toml backend/app
uv run --project backend --frozen pytest backend/tests -q
uv run --project backend --frozen python scripts/check_public_tree.py --history
```

Set `TEST_DATABASE_URL=postgresql+psycopg://ortelana:demo-db-local@127.0.0.1:5433/ortelana_test` in your shell to include PostgreSQL tests. Tests refuse databases without the `_test` suffix. Without this variable PostgreSQL tests are explicitly skipped. Compose bootstrap creates the dedicated test database.

```bash
cd frontend
npm ci
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

E2E tests need the running demo stack. Linux hosts may need `npx playwright install --with-deps chromium`. For API development, stop this project's Compose backend, then run `uv run --project backend --frozen alembic -c backend/alembic.ini upgrade head` and `uv run --project backend --frozen uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001`. `npm run dev` uses the Vite proxy to that port.

```bash
# From the repository root, with the demo stack running:
uv run --project backend --frozen python scripts/validate_stack.py --restart-backend
uv run --project backend --frozen python scripts/validate_n8n.py
pwsh -File scripts/validate_initialization.ps1
```

Live checks exercise an actual backend restart, human decisions, Prometheus scrapes, twenty Grafana queries and five executions in the actual n8n engine. [Executed validation evidence](docs/VALIDATION.md) records results and limits. CI runs backend/PostgreSQL, frontend and repository checks on pushes/PRs; the manually dispatched [full-stack workflow](.github/workflows/stack.yml) runs containers and browsers.

## Automation and observability

n8n imports manual and weekly Monday 09:00 Buenos Aires workflow definitions. They remain **unpublished**. Editor first-owner setup is manual; CLI execution is independently bootstrapped. Requests retain one idempotency key through a bounded retry. Permanent 4xx responses are not retried; connection failures and 502/503/504 receive one backoff/retry. Critical results direct users to the review inbox; n8n never approves. Scheduled timer firing has not been tested. See [automation](docs/automation.md).

Prometheus measures actual request/node/execution activity and database-backed review gauges with bounded labels. Structured logs include correlation/execution IDs and sanitized errors. Grafana Operations queries Prometheus; Business Intelligence queries PostgreSQL through a SELECT-only identity. Panels show metres, not revenue. Empty rate windows are allowed. See [observability](docs/observability.md) and [operations](docs/troubleshooting.md).

## Repository guide

| Path | Contents |
| --- | --- |
| `backend/app/` | API, calculations, graph, services, repositories and telemetry |
| `backend/migrations/`, `backend/tests/` | Schema/integrity migrations and synthetic tests |
| `frontend/src/`, `frontend/tests/` | Connected UI, component and browser tests |
| `data/demo/` | Independently generated synthetic data only |
| `workflows/`, `infrastructure/` | n8n exports and six-service provisioning |
| `scripts/`, `docs/` | Validation, ADRs, technical/operational docs and real screenshots |

## Known limitations and roadmap

- Local portfolio configuration, shared demo identities, one API worker and synchronous bounded analyses. Individual OIDC identity, TLS, multi-tenant authorization and deployment hardening are future work.
- Reporting-year comparisons only; seasonal/monthly disaggregation is unsupported. Larger datasets would benefit from a durable background queue.
- Commercial actions are simulations. No forecasting, LLM reasoning, external ERP integration or real notification delivery is implemented.
- n8n owner onboarding is manual; scheduled timer firing has not been exercised. Workflows are intentionally inactive.
- Dependencies retain their own licenses, including n8n's source-available terms. A project-wide MIT grant is withheld because rights for all upstream academic contributions have not been established; copied teaching material is excluded. See [rights status](THIRD_PARTY_NOTICES.md).

Future priorities: individual identity, background execution, dataset selection and line-level drill-down, followed by optional local narrative explanations over computed evidence and OpenTelemetry. These are proposed extensions, not current functionality.

See [contributing](CONTRIBUTING.md), [security reporting](SECURITY.md), [changelog](CHANGELOG.md) and [release procedure](docs/publication.md).
