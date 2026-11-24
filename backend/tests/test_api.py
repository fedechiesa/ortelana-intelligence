from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from app.main import create_app
from app.repositories.models import Audit, Decision, Execution
from conftest import OPERATOR, SUPERVISOR
from fastapi.testclient import TestClient
from sqlalchemy import func, select


def analyze(client, product="DEMO-003", key=None):
    return client.post(
        "/analizar",
        headers={**OPERATOR, "Idempotency-Key": key or str(uuid4())},
        json={"producto_id": product},
    )


@pytest.mark.parametrize(
    "product,status", [("DEMO-001", "NORMAL"), ("DEMO-002", "ADVERTENCIA"), ("DEMO-003", "CRITICO")]
)
def test_real_demo_graph_routing_and_persistence(client, product, status):
    response = analyze(client, product)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["estado"] == status
    assert {"coordinator", "sales", "products", "branches", "risk", "report"} <= {
        s["node"] for s in result["steps"]
    }
    critical = status == "CRITICO"
    assert result["approval_status"] == ("PENDING" if critical else "NOT_REQUIRED")
    assert result["technical_status"] == ("WAITING_REVIEW" if critical else "COMPLETED")
    assert client.get(f"/executions/{result['ejecucion_id']}", headers=OPERATOR).json()["estado"] == status


@pytest.mark.parametrize("decision,approval", [("APROBADO", "APPROVED"), ("RECHAZADO", "REJECTED")])
def test_human_review_cannot_be_unauthorized_or_duplicated(client, decision, approval):
    execution = analyze(client).json()
    body = dict(
        ejecucion_id=execution["ejecucion_id"], decision=decision, comentario="Reviewed evidence carefully"
    )
    assert client.post("/decision", json=body).status_code == 401
    assert client.post("/decision", json=body, headers=OPERATOR).status_code == 403
    assert (
        client.post("/decision", json={**body, "responsable": "spoofed"}, headers=SUPERVISOR).status_code
        == 422
    )
    result = client.post("/decision", json=body, headers=SUPERVISOR)
    assert result.status_code == 200, result.text
    assert result.json()["approval_status"] == approval
    assert result.json()["technical_status"] == "COMPLETED"
    assert "human_review" in [s["node"] for s in result.json()["steps"]]
    assert client.post("/decision", json=body, headers=SUPERVISOR).status_code == 409
    with client.app.state.service.factory() as session:
        d = session.get(Decision, execution["ejecucion_id"])
        assert d.actor == "local-supervisor"
        assert d.evidence["estado"] == "CRITICO"
        assert (
            session.scalar(
                select(func.count())
                .select_from(Audit)
                .where(Audit.execution_id == execution["ejecucion_id"], Audit.event == "human_decision")
            )
            == 1
        )


def test_noncritical_or_missing_execution_cannot_receive_approval(client):
    execution = analyze(client, "DEMO-001").json()
    for execution_id, expected in [(execution["ejecucion_id"], 409), (str(uuid4()), 404)]:
        assert (
            client.post(
                "/decision",
                headers=SUPERVISOR,
                json=dict(
                    ejecucion_id=execution_id, decision="APROBADO", comentario="Do not approve this case"
                ),
            ).status_code
            == expected
        )


def test_idempotency_and_conflicting_input(client):
    key = str(uuid4())
    first = analyze(client, key=key).json()
    replay = analyze(client, key=key)
    assert replay.json()["ejecucion_id"] == first["ejecucion_id"]
    assert replay.json()["replayed"]
    assert analyze(client, "DEMO-001", key).status_code == 409


def test_error_is_sanitized_persisted_and_recoverable(client, monkeypatch):
    svc = client.app.state.service
    original = svc.analytics.summary

    def fail(*_):
        raise RuntimeError("secret-database-password-do-not-expose")

    monkeypatch.setattr(svc.analytics, "summary", fail)
    result = analyze(client)
    assert result.status_code == 500
    assert "secret-database-password" not in result.text
    errors = client.get("/executions?status=ERROR", headers=OPERATOR).json()["items"]
    assert len(errors) == 1
    e = errors[0]
    assert e["business_status"] is None
    assert e["trace_id"] == result.headers["X-Correlation-ID"]
    monkeypatch.setattr(svc.analytics, "summary", original)
    result = client.post(f"/executions/{e['ejecucion_id']}/recover", headers=SUPERVISOR)
    assert result.status_code == 200
    assert result.json()["estado"] == "CRITICO"


def test_checkpoint_and_committed_decision_survive_app_restart(settings):
    with TestClient(create_app(settings)) as c:
        execution = analyze(c).json()
        svc = c.app.state.service
        config = {"configurable": {"thread_id": execution["thread_id"]}}
        assert svc.graph.get_state(config).next == ("human_review",)
        # Simulated crash after decision commit, before graph continuation.
        with svc.factory.begin() as session:
            e = session.get(Execution, execution["ejecucion_id"])
            e.approval_status, e.technical_status = "APPROVED", "RESUMING"
            session.add(
                Decision(
                    execution_id=e.id,
                    decision="APROBADO",
                    actor="restart-test-supervisor",
                    comment="SIMULATED crash window fixture",
                    evidence=e.result,
                    policy=e.policy,
                )
            )
    with TestClient(create_app(settings)) as restarted:
        result = restarted.get(f"/executions/{execution['ejecucion_id']}", headers=OPERATOR).json()
        assert result["technical_status"] == "COMPLETED"
        assert result["approval_status"] == "APPROVED"
        assert len({s["node"] for s in result["steps"]}) == len(result["steps"])


def test_concurrent_idempotency_creates_one_execution(client):
    key = str(uuid4())
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: analyze(client, key=key), range(2)))
    assert all(r.status_code == 200 for r in results)
    assert len({r.json()["ejecucion_id"] for r in results}) == 1


def test_policies_are_versioned_and_execution_keeps_snapshot(client):
    e = analyze(client).json()
    assert client.post("/policies", headers=OPERATOR, json=dict(warning=-15, critical=-30)).status_code == 403
    result = client.post("/policies", headers=SUPERVISOR, json=dict(warning=-15, critical=-30))
    assert result.status_code == 201
    assert result.json()["version"] == 2
    assert analyze(client).json()["estado"] == "ADVERTENCIA"
    assert client.get(f"/executions/{e['ejecucion_id']}", headers=OPERATOR).json()["policy"]["version"] == 1


def test_pagination_metrics_health_and_correlation(client):
    assert client.get("/analytics?anio_base=2024&anio_actual=2025", headers=OPERATOR).status_code == 200
    assert client.get("/analytics?anio_base=2025&anio_actual=2024", headers=OPERATOR).status_code == 422
    analyze(client)
    analyze(client, "DEMO-001")
    result = client.get("/executions?page_size=1", headers=OPERATOR).json()
    assert len(result["items"]) == 1 and result["total"] == 2
    assert client.get("/executions?page_size=101", headers=OPERATOR).status_code == 422
    assert client.get("/dataset").status_code == 401
    assert client.get("/health/ready").status_code == 200
    metrics = client.get("/metrics").text
    assert "ortelana_pending_reviews 1.0" in metrics
    assert "ortelana_node_seconds_count" in metrics
    assert "execution_id=" not in metrics
    trace = str(uuid4())
    assert client.get("/salud", headers={"X-Correlation-ID": trace}).headers["X-Correlation-ID"] == trace


