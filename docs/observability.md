# Real observability

Application events are JSON records with timestamp, severity, service, event, trace ID and, when applicable, execution/thread IDs, node, duration, outcome and sanitized error type. Request bodies, tokens and raw exception messages are not logged. Framework startup/access output can remain ordinary service logs; structured application events are distinct from the database's durable append-only audit.

Correlation IDs are UUIDs. A valid incoming `X-Correlation-ID` is preserved; invalid/missing values receive a new UUID. Each execution preserves its origin trace for recovery. The execution UUID is its LangGraph thread ID. The UI exposes trace and dataset identity in execution detail.

| Metric | Semantics |
| --- | --- |
| `ortelana_http_requests_total` | Actual HTTP requests by method, route template and status |
| `ortelana_http_seconds` | HTTP duration histogram |
| `ortelana_executions_started_total` | New persisted execution reservations |
| `ortelana_executions_finished_total{outcome}` | Graph **attempt** outcomes, including pauses and recovery; not a lifetime unique-execution total |
| `ortelana_execution_seconds` | Processing-attempt duration; excludes time waiting for humans |
| `ortelana_node_seconds{node}` | Actual completed/failed node latency, excluding human wait |
| `ortelana_retries_total{operation}` | Recognized transient infrastructure retries |
| `ortelana_human_decisions_total{decision}` | Newly committed authenticated decisions |
| `ortelana_pending_reviews` | Current database-backed pending count |
| `ortelana_critical_executions` | Persisted critical analyses, independent of technical errors |

Counters/histograms restart with the single API process. Persistent totals and review gauges come from PostgreSQL. Labels use route templates and fixed statuses/nodes, never execution ID, thread ID, arbitrary product or raw URL. Empty traffic windows may legitimately have no samples/undefined rates. No activity is fabricated to fill a dashboard.

Prometheus scrapes `backend:8000/metrics` every ten seconds. Grafana provisions a read-only PostgreSQL datasource and an internal Prometheus datasource. Operational Monitoring includes actual service scrape health, execution states, requests/errors, latency means/p95, node p95, critical/pending counts and human decisions. Business Intelligence queries reporting-year volumes, branches, textile lines, risk distribution, evidence-backed product declines, review history and final decisions. Sales panels use the latest imported snapshot; execution-history panels retain original mode/snapshot linkage.

`scripts/validate_stack.py` checks each datasource's health and executes all twenty dashboard queries through Grafana's real datasource API. It also verifies the real Prometheus `up` series and waits for a subsequent scrape after a backend restart. A successful JSON dashboard parse alone is not counted as validation.

Local trace IDs and recorded graph steps provide request reconstruction. OpenTelemetry/Jaeger and LangSmith are deliberately not mandatory and have not been represented as implemented integrations.
