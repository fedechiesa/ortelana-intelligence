"""Reproducible n8n exports and provisioned dashboards. No business calculations live here."""

import copy
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def workflow(scheduled=False):
    nodes, connections = [], {}

    def node(name, kind, parameters, x, y, version=1, **extra):
        nodes.append(
            dict(
                id=str(uuid5(NAMESPACE_URL, name)),
                name=name,
                type=f"n8n-nodes-base.{kind}",
                typeVersion=version,
                position=[x, y],
                parameters=parameters,
                **extra,
            )
        )

    def edge(source, target, output=0):
        outputs = connections.setdefault(source, {"main": []})["main"]
        while len(outputs) <= output:
            outputs.append([])
        outputs[output].append(dict(node=target, type="main", index=0))

    node("Manual Trigger", "manualTrigger", {}, 0, 0)
    edge("Manual Trigger", "Prepare request")
    if scheduled:
        node(
            "Schedule Trigger",
            "scheduleTrigger",
            {"rule": {"interval": [{"field": "cronExpression", "expression": "0 9 * * 1"}]}},
            0,
            180,
            1.2,
        )
        edge("Schedule Trigger", "Prepare request")
    assignments = [
        dict(id=k, name=k, value=v, type=t)
        for k, v, t in [
            ("anio_base", 2024, "number"),
            ("anio_actual", 2025, "number"),
            ("producto_id", "", "string"),
            (
                "idempotency_key",
                "={{ 'n8n-' + $workflow.id + '-' + $execution.id }}",
                "string",
            ),
        ]
    ]
    node(
        "Prepare request",
        "set",
        {"assignments": {"assignments": assignments}, "options": {}},
        240,
        0,
        3.4,
    )
    params = dict(
        method="POST",
        url="http://backend:8000/analizar",
        authentication="genericCredentialType",
        genericAuthType="httpHeaderAuth",
        sendHeaders=True,
        headerParameters={
            "parameters": [
                dict(
                    name="Idempotency-Key",
                    value="={{ $('Prepare request').first().json.idempotency_key }}",
                )
            ]
        },
        sendBody=True,
        specifyBody="json",
        jsonBody="={{ JSON.stringify({anio_base: $('Prepare request').first().json.anio_base, "
        "anio_actual: $('Prepare request').first().json.anio_actual, "
        "producto_id: $('Prepare request').first().json.producto_id || null}) }}",
        options={
            "timeout": 45000,
            "response": {"response": {"fullResponse": True, "neverError": True}},
        },
    )
    cred = {"httpHeaderAuth": {"id": "ortelanaApiHeader", "name": "Ortelana API automation"}}
    node(
        "Analyze via API",
        "httpRequest",
        params,
        480,
        0,
        4.2,
        credentials=cred,
        onError="continueRegularOutput",
    )
    edge("Prepare request", "Analyze via API")
    node(
        "Transient failure?",
        "if",
        {
            "conditions": {
                "options": {"caseSensitive": True, "typeValidation": "strict"},
                "conditions": [
                    {
                        "id": "transient",
                        "leftValue": "={{ [0,502,503,504].includes($json.statusCode || 0) }}",
                        "rightValue": True,
                        "operator": {
                            "type": "boolean",
                            "operation": "true",
                            "singleValue": True,
                        },
                    }
                ],
                "combinator": "and",
            },
            "options": {},
        },
        720,
        0,
        2.2,
    )
    edge("Analyze via API", "Transient failure?")
    node(
        "Bounded backoff",
        "wait",
        {"amount": 2, "unit": "seconds"},
        960,
        -160,
        1.1,
        webhookId=str(uuid5(NAMESPACE_URL, "ortelana-safe-retry")),
    )
    node(
        "Retry once safely",
        "httpRequest",
        copy.deepcopy(params),
        1200,
        -160,
        4.2,
        credentials=cred,
        onError="continueRegularOutput",
    )
    edge("Transient failure?", "Bounded backoff", 0)
    edge("Bounded backoff", "Retry once safely")
    rules = []
    for status in ("NORMAL", "ADVERTENCIA", "CRITICO", "SIN_BASE"):
        rules.append(
            dict(
                conditions={
                    "options": {"caseSensitive": True, "typeValidation": "strict"},
                    "conditions": [
                        dict(
                            id=status,
                            leftValue="={{ $json.body?.estado || 'ERROR' }}",
                            rightValue=status,
                            operator={"type": "string", "operation": "equals"},
                        )
                    ],
                    "combinator": "and",
                },
                renameOutput=True,
                outputKey=status,
            )
        )
    node(
        "Route persisted risk",
        "switch",
        {"rules": {"values": rules}, "options": {"fallbackOutput": "extra"}},
        1440,
        0,
        3.2,
    )
    edge("Transient failure?", "Route persisted risk", 1)
    edge("Retry once safely", "Route persisted risk")
    for i, (name, outcome) in enumerate(
        [
            ("Normal recorded", "NORMAL: monitoring only"),
            ("Warning recorded", "ADVERTENCIA: review commercial trend"),
            (
                "Human review required",
                "CRITICO: backend checkpoint paused; decide in authenticated UI",
            ),
            ("No comparable baseline", "SIN_BASE: collect comparable evidence"),
            (
                "Technical error recorded",
                "ERROR: inspect API trace; no commercial authorization",
            ),
        ]
    ):
        node(
            name,
            "set",
            {
                "assignments": {
                    "assignments": [
                        dict(id="result", name="outcome", value=outcome, type="string"),
                        dict(
                            id="execution",
                            name="execution_id",
                            value="={{ $json.body?.ejecucion_id || '' }}",
                            type="string",
                        ),
                        dict(
                            id="trace",
                            name="trace_id",
                            value="={{ $json.headers?.['x-correlation-id'] || '' }}",
                            type="string",
                        ),
                        dict(
                            id="review",
                            name="review_url",
                            value="http://localhost:5173/#reviews",
                            type="string",
                        ),
                    ]
                },
                "options": {},
            },
            1700,
            i * 145 - 180,
            3.4,
        )
        edge("Route persisted risk", name, i)
    return dict(
        id="ortelanaSchedule" if scheduled else "ortelanaManual01",
        name="Ortelana | scheduled reporting-year analysis (inactive)"
        if scheduled
        else "Ortelana | manual reporting-year analysis",
        active=False,
        nodes=nodes,
        connections=connections,
        settings=dict(
            executionOrder="v1",
            saveDataSuccessExecution="all",
            saveDataErrorExecution="all",
            executionTimeout=120,
            timezone="America/Argentina/Buenos_Aires",
        ),
        versionId=str(uuid5(NAMESPACE_URL, f"ortelana-v1-{scheduled}")),
        tags=[],
    )


def dashboard(uid, title, specs):
    panels = []
    for i, (name, kind, source, query) in enumerate(specs):
        prometheus = source == "ortelana-prom"
        target = (
            dict(
                refId="A",
                expr=query,
                legendFormat="{{node}}" if "node" in query else "{{outcome}}",
            )
            if prometheus
            else dict(
                refId="A",
                rawSql=query,
                format="time_series" if kind == "timeseries" else "table",
                rawQuery=True,
                editorMode="code",
                sql={"columns": [], "groupBy": [], "limit": 1000},
            )
        )
        panels.append(
            dict(
                id=i + 1,
                title=name,
                type=kind,
                datasource=dict(
                    type="prometheus" if prometheus else "grafana-postgresql-datasource",
                    uid=source,
                ),
                targets=[target],
                gridPos=dict(h=8, w=12, x=(i % 2) * 12, y=(i // 2) * 8),
                fieldConfig=dict(defaults=dict(color=dict(mode="palette-classic")), overrides=[]),
                options=dict(
                    legend=dict(displayMode="list", placement="bottom"),
                    tooltip=dict(mode="multi"),
                    reduceOptions=dict(calcs=["lastNotNull"], values=False),
                ),
            )
        )
    return dict(
        uid=uid,
        title=title,
        tags=["ortelana", "live-sources"],
        timezone="browser",
        schemaVersion=40,
        version=1,
        refresh="10s",
        time=dict(**{"from": "now-24h", "to": "now"}),
        panels=panels,
    )


if __name__ == "__main__":
    write("workflows/manual-analysis.json", workflow())
    write("workflows/scheduled-analysis.json", workflow(True))
    ops = [
        ("API scrape availability", "stat", "ortelana-prom", 'up{job="ortelana-api"}'),
        (
            "Persisted execution states",
            "barchart",
            "ortelana-pg",
            "SELECT technical_status AS state, COUNT(*) AS executions FROM executions GROUP BY 1",
        ),
        (
            "HTTP request rate",
            "timeseries",
            "ortelana-prom",
            "sum(rate(ortelana_http_requests_total[5m]))",
        ),
        (
            "HTTP error rate",
            "timeseries",
            "ortelana-prom",
            'sum(rate(ortelana_http_requests_total{status=~"5.."}[5m]))',
        ),
        (
            "Mean execution latency (seconds)",
            "timeseries",
            "ortelana-prom",
            "rate(ortelana_execution_seconds_sum[5m]) / rate(ortelana_execution_seconds_count[5m])",
        ),
        (
            "Execution latency p95 (seconds)",
            "timeseries",
            "ortelana-prom",
            "histogram_quantile(0.95, sum by(le) (rate(ortelana_execution_seconds_bucket[5m])))",
        ),
        ("Pending human reviews", "stat", "ortelana-prom", "ortelana_pending_reviews"),
        (
            "Critical analyses (persisted)",
            "stat",
            "ortelana-prom",
            "ortelana_critical_executions",
        ),
        (
            "Node latency p95 (seconds)",
            "timeseries",
            "ortelana-prom",
            "histogram_quantile(0.95, sum by(le,node) (rate(ortelana_node_seconds_bucket[5m])))",
        ),
        (
            "Execution outcomes since process start",
            "timeseries",
            "ortelana-prom",
            "ortelana_executions_finished_total",
        ),
        (
            "Human decisions",
            "barchart",
            "ortelana-pg",
            "SELECT decision, COUNT(*) AS decisions FROM decisions GROUP BY 1",
        ),
        (
            "Successful processing / waiting review (%)",
            "stat",
            "ortelana-pg",
            "SELECT 100.0 * COUNT(*) FILTER(WHERE technical_status IN ('COMPLETED','WAITING_REVIEW')) "
            "/ NULLIF(COUNT(*),0) AS success_percent FROM executions",
        ),
    ]
    latest = "(SELECT id FROM datasets ORDER BY created_at DESC LIMIT 1)"
    bi = [
        (
            "Observed reporting-year metres (latest imported snapshot)",
            "barchart",
            "ortelana-pg",
            "SELECT year::text AS reporting_year, SUM(total) AS metres FROM sales "
            f"WHERE dataset_id={latest} GROUP BY year ORDER BY year",
        ),
        (
            "Observed branch volume, latest reporting year",
            "barchart",
            "ortelana-pg",
            "SELECT b.name, SUM(s.total) AS metres FROM sales s JOIN branches b "
            f"ON b.id=s.branch_id AND b.dataset_id=s.dataset_id WHERE s.dataset_id={latest} "
            f"AND s.year=(SELECT MAX(year) FROM sales WHERE dataset_id={latest}) "
            "GROUP BY b.name ORDER BY 2 DESC",
        ),
        (
            "Commercial risk distribution",
            "barchart",
            "ortelana-pg",
            "SELECT business_status AS risk, COUNT(*) AS analyses FROM executions "
            "WHERE business_status IS NOT NULL GROUP BY 1",
        ),
        (
            "Matched commercial changes and data mode",
            "table",
            "ortelana-pg",
            "SELECT e.created_at, d.mode, e.id, e.result->>'producto' AS product, "
            "(e.result->>'variacion')::numeric AS matched_change_percent, e.business_status, "
            "e.approval_status FROM executions e JOIN datasets d ON d.id=e.dataset_id "
            "ORDER BY e.created_at DESC LIMIT 100",
        ),
        (
            "Products with evidence-backed declines",
            "table",
            "ortelana-pg",
            "SELECT e.id AS execution, item->>'name' AS product, "
            "(item->>'variation')::numeric AS matched_change_percent, item->>'status' AS risk, "
            "item->>'coverage_pct' AS coverage_percent FROM executions e CROSS JOIN LATERAL "
            "json_array_elements(e.result->'products') item "
            "WHERE item->>'status' IN ('ADVERTENCIA','CRITICO') "
            "ORDER BY e.created_at DESC LIMIT 100",
        ),
        (
            "Immutable human decisions",
            "table",
            "ortelana-pg",
            "SELECT created_at, execution_id, decision, actor, comment, "
            "policy->>'version' AS policy_version FROM decisions ORDER BY created_at DESC LIMIT 100",
        ),
        (
            "Observed textile line volume, latest reporting year",
            "barchart",
            "ortelana-pg",
            "SELECT p.line, SUM(s.total) AS metres FROM sales s JOIN products p "
            f"ON p.id=s.product_id AND p.dataset_id=s.dataset_id WHERE s.dataset_id={latest} "
            f"AND s.year=(SELECT MAX(year) FROM sales WHERE dataset_id={latest}) "
            "GROUP BY p.line ORDER BY 2 DESC",
        ),
        (
            "Historical alert & review evidence",
            "table",
            "ortelana-pg",
            "SELECT created_at, id AS execution, business_status, approval_status, "
            "result->>'recomendacion' AS recommendation FROM executions "
            "WHERE business_status IN ('CRITICO','ADVERTENCIA') ORDER BY created_at DESC LIMIT 100",
        ),
    ]
    write(
        "infrastructure/grafana/provisioning/dashboards/json/operations.json",
        dashboard("ortelana-operations", "Ortelana | Operational Monitoring", ops),
    )
    write(
        "infrastructure/grafana/provisioning/dashboards/json/business.json",
        dashboard("ortelana-business", "Ortelana | Business Intelligence", bi),
    )
