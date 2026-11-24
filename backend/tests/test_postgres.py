from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from app.graph.workflow import build_graph
from app.repositories.models import Audit, Decision
from conftest import OPERATOR, SUPERVISOR
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def test_application_role_has_no_global_privileges(postgres_client):
    with postgres_client.app.state.service.engine.connect() as connection:
        flags = connection.execute(
            text(
                "SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls "
                "FROM pg_roles WHERE rolname=current_user"
            )
        ).one()
        assert not any(flags)


def create(client, key=None):
    return client.post(
        "/analizar",
        headers={**OPERATOR, "Idempotency-Key": key or str(uuid4())},
        json={"producto_id": "DEMO-003"},
    )


def test_postgres_checkpoints_and_concurrent_decisions(postgres_client):
    c = postgres_client
    response = create(c)
    assert response.status_code == 200, response.text
    e = response.json()
    config = {"configurable": {"thread_id": e["thread_id"]}}
    assert c.app.state.service.graph.get_state(config).next == ("human_review",)
    body = dict(
        ejecucion_id=e["ejecucion_id"], decision="APROBADO", comentario="Concurrent PostgreSQL review"
    )
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: c.post("/decision", headers=SUPERVISOR, json=body), range(2)))
    assert sorted(r.status_code for r in results) == [200, 409]
    with c.app.state.service.factory() as session:
        assert (
            len(list(session.scalars(select(Decision).where(Decision.execution_id == e["ejecucion_id"]))))
            == 1
        )
        assert (
            session.execute(
                text("SELECT COUNT(*) FROM checkpoints WHERE thread_id=:id"), {"id": e["thread_id"]}
            ).scalar()
            > 0
        )


def test_postgres_immutable_history(postgres_client):
    c = postgres_client
    create(c)
    with c.app.state.service.factory() as session:
        event = session.scalar(select(Audit).limit(1))
        event_id = event.id
    with pytest.raises(DBAPIError), c.app.state.service.engine.begin() as conn:
        conn.execute(text("UPDATE audit_events SET actor='tampered' WHERE id=:id"), {"id": event_id})


def test_postgres_idempotency_and_exclusive_processing(postgres_client):
    c = postgres_client
    key = str(uuid4())
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: create(c, key), range(2)))
    assert all(r.status_code == 200 for r in results)
    assert len({r.json()["ejecucion_id"] for r in results}) == 1
    svc = c.app.state.service
    execution_id = results[0].json()["ejecucion_id"]
    with svc.lock(execution_id), pytest.raises(Exception, match="already being processed"):
        with svc.lock(execution_id):
            pass


def test_postgres_rejects_unbacked_approval_and_evidence_tampering(postgres_client):
    c = postgres_client
    e = create(c).json()
    for statement in [
        "UPDATE executions SET approval_status='APPROVED' WHERE id=:id",
        "UPDATE executions SET result='{}'::json WHERE id=:id",
        "UPDATE executions SET policy='{}'::json WHERE id=:id",
    ]:
        with pytest.raises(DBAPIError), c.app.state.service.engine.begin() as connection:
            connection.execute(text(statement), {"id": e["ejecucion_id"]})
    stored = c.get(f"/executions/{e['ejecucion_id']}", headers=OPERATOR).json()
    assert stored["approval_status"] == "PENDING"
    assert stored["estado"] == "CRITICO"


def test_decision_during_report_checkpoint_is_not_lost(postgres_client):
    c = postgres_client
    svc = c.app.state.service
    original_graph = svc.graph
    ready, release = Event(), Event()
    execution_ids = []

    def pause_after_evidence(execution_id, report):
        svc.persist_report(execution_id, report)
        execution_ids.append(execution_id)
        ready.set()
        assert release.wait(5), "Timed out waiting for concurrent decision fixture"

    svc.graph = build_graph(
        svc.analytics, pause_after_evidence, svc.read_decision, original_graph.checkpointer
    )
    try:
        with ThreadPoolExecutor(2) as pool:
            analysis = pool.submit(create, c)
            assert ready.wait(5)
            execution_id = execution_ids[0]
            decision = pool.submit(
                c.post,
                "/decision",
                headers=SUPERVISOR,
                json={
                    "ejecucion_id": execution_id,
                    "decision": "APROBADO",
                    "comentario": "SYNTHETIC concurrent checkpoint review fixture",
                },
            )
            deadline = monotonic() + 3
            while not svc.read_decision(execution_id) and monotonic() < deadline:
                sleep(0.01)
            assert svc.read_decision(execution_id) == "APROBADO"
            release.set()
            assert analysis.result(timeout=5).status_code == 200
            response = decision.result(timeout=5)
            assert response.status_code == 200, response.text
            assert response.json()["technical_status"] == "COMPLETED"
            assert response.json()["simulated_authorization"] is True
        with svc.factory() as session:
            events = list(
                session.scalars(
                    select(Audit).where(
                        Audit.execution_id == execution_id, Audit.event == "execution_completed"
                    )
                )
            )
            assert len(events) == 1
    finally:
        release.set()
        svc.graph = original_graph
