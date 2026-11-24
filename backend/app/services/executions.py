import hashlib
import json
import threading
from contextlib import contextmanager
from time import perf_counter
from uuid import uuid4

from langgraph.types import Command
from sqlalchemy import select, text, update
from sqlalchemy.exc import IntegrityError, OperationalError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_random_exponential

from app.core.config import DomainError
from app.graph.workflow import build_graph
from app.observability.telemetry import DECISIONS, DURATION, FINISHED, RETRIES, STARTED, log
from app.repositories.models import Audit, Decision, Execution, Policy, Review
from app.services.analytics import Analytics


def transient_database_error(error):
    return isinstance(error, OperationalError) and getattr(error.orig, "sqlstate", None) in {
        "40001",
        "40P01",
        "08006",
        "08003",
    }


def record_retry(_):
    RETRIES.labels("database").inc()


class ExecutionService:
    def __init__(self, engine, factory, dataset_id, checkpointer):
        self.engine, self.factory, self.dataset_id = engine, factory, dataset_id
        self.analytics = Analytics(factory)
        self.graph = build_graph(self.analytics, self.persist_report, self.read_decision, checkpointer)
        self._sqlite_lock = threading.Lock()

    def policy(self):
        with self.factory() as session:
            p = session.scalar(select(Policy).order_by(Policy.version.desc()).limit(1))
            return dict(version=p.version, warning=p.warning, critical=p.critical)

    def audit(self, session, execution, actor, event, detail=None, trace_id=None):
        session.add(
            Audit(
                execution_id=execution.id if execution else None,
                actor=actor,
                event=event,
                trace_id=trace_id or (execution.trace_id if execution else str(uuid4())),
                detail=detail or {},
            )
        )

    def get(self, execution_id):
        with self.factory() as session:
            execution = session.get(Execution, execution_id)
            if not execution:
                raise DomainError(404, "Execution not found")
            return execution

    def create(self, request, key, actor, trace_id):
        self.analytics.validate(self.dataset_id, request)
        request_hash = hashlib.sha256(
            json.dumps(dict(request=request, dataset=self.dataset_id), sort_keys=True).encode()
        ).hexdigest()
        with self.factory() as session:
            existing = session.scalar(select(Execution).where(Execution.idempotency_key == key))
        if existing:
            if existing.request_hash != request_hash:
                raise DomainError(409, "Idempotency key already used for different input")
            return existing, False
        execution_id = str(uuid4())
        execution = Execution(
            id=execution_id,
            thread_id=execution_id,
            trace_id=trace_id,
            idempotency_key=key,
            request_hash=request_hash,
            dataset_id=self.dataset_id,
            requested_by=actor.name,
            request=request,
            policy=self.policy(),
        )
        try:
            with self.factory.begin() as session:
                session.add(execution)
                session.flush()
                self.audit(session, execution, actor.name, "execution_created")
        except IntegrityError:
            with self.factory() as session:
                existing = session.scalar(select(Execution).where(Execution.idempotency_key == key))
            if not existing or existing.request_hash != request_hash:
                raise DomainError(409, "Concurrent request conflicts with idempotency key") from None
            return existing, False
        STARTED.inc()
        return execution, True

    @contextmanager
    def lock(self, execution_id):
        if self.engine.dialect.name == "postgresql":
            with self.engine.connect() as connection:
                locked = connection.scalar(
                    text("SELECT pg_try_advisory_lock(hashtextextended(:id, 0))"), {"id": execution_id}
                )
                connection.commit()
                if not locked:
                    raise DomainError(409, "Execution is already being processed; retry safely")
                try:
                    yield
                finally:
                    connection.execute(
                        text("SELECT pg_advisory_unlock(hashtextextended(:id, 0))"), {"id": execution_id}
                    )
                    connection.commit()
        else:
            # Only isolated tests/single-process development. PostgreSQL enforces production concurrency.
            with self._sqlite_lock:
                yield

    @retry(
        retry=retry_if_exception(transient_database_error),
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(multiplier=0.1, max=1),
        before_sleep=record_retry,
        reraise=True,
    )
    def persist_report(self, execution_id, report):
        with self.factory.begin() as session:
            e = session.scalar(select(Execution).where(Execution.id == execution_id).with_for_update())
            if e.result:
                return  # Replay after crash: evidence/review/audit are already durable.
            e.result, e.business_status = report, report["estado"]
            if report["estado"] == "CRITICO":
                e.approval_status, e.technical_status = "PENDING", "WAITING_REVIEW"
                session.add(Review(execution_id=e.id, evidence=report))
                self.audit(session, e, "graph", "review_requested", {"policy": e.policy})
            self.audit(session, e, "graph", "report_persisted", {"status": report["estado"]})

    def read_decision(self, execution_id):
        with self.factory() as session:
            d = session.get(Decision, execution_id)
            return d.decision if d else None

    def run(self, execution_id):
        with self.lock(execution_id):
            e = self.get(execution_id)
            config = dict(configurable=dict(thread_id=e.thread_id), recursion_limit=16, max_concurrency=3)
            started = perf_counter()
            try:
                snapshot = self.graph.get_state(config)
                initial = dict(
                    execution_id=e.id,
                    dataset_id=e.dataset_id,
                    trace_id=e.trace_id,
                    request=e.request,
                    policy=e.policy,
                    steps=[],
                )
                if not snapshot.values:
                    self.graph.invoke(initial, config, durability="sync")
                elif snapshot.next and not self._interrupted(snapshot):
                    self.graph.invoke(None, config, durability="sync")
                snapshot = self.graph.get_state(config)
                if self._interrupted(snapshot) and self.read_decision(e.id):
                    self.graph.invoke(Command(resume=True), config, durability="sync")
                    snapshot = self.graph.get_state(config)
                waiting = bool(snapshot.next)
                with self.factory.begin() as session:
                    stored = session.get(Execution, e.id)
                    previous = stored.technical_status
                    stored.technical_status = "WAITING_REVIEW" if waiting else "COMPLETED"
                    stored.steps = {s["node"]: s for s in snapshot.values.get("steps", [])}
                    stored.duration_ms += max(1, round((perf_counter() - started) * 1000))
                    stored.error = None
                    if not waiting and previous != "COMPLETED":
                        self.audit(
                            session,
                            stored,
                            "graph",
                            "execution_completed",
                            {"simulated_authorization": snapshot.values.get("authorized", False)},
                        )
                FINISHED.labels("waiting_review" if waiting else "success").inc()
            except Exception as exc:
                with self.factory.begin() as session:
                    stored = session.get(Execution, e.id)
                    stored.technical_status = "ERROR"
                    stored.error = "Analysis failed; supervisor may recover this execution"
                    stored.duration_ms += max(1, round((perf_counter() - started) * 1000))
                    self.audit(
                        session, stored, "backend", "execution_error", {"error_type": type(exc).__name__}
                    )
                log(
                    "execution_error",
                    execution_id=e.id,
                    thread_id=e.thread_id,
                    trace_id=e.trace_id,
                    error=type(exc).__name__,
                    result="ERROR",
                    duration_ms=round((perf_counter() - started) * 1000),
                )
                FINISHED.labels("error").inc()
                raise DomainError(
                    500, f"Analysis failed. Correlation: {e.trace_id}; execution: {e.id}"
                ) from None
            finally:
                DURATION.observe(perf_counter() - started)
        return self.get(execution_id)

    @staticmethod
    def _interrupted(snapshot):
        return any(task.interrupts for task in snapshot.tasks)

    def decide(self, request, actor):
        if actor.role != "supervisor":
            raise DomainError(403, "Supervisor role required")
        try:
            with self.factory.begin() as session:
                e = session.scalar(
                    select(Execution).where(Execution.id == request.ejecucion_id).with_for_update()
                )
                if not e:
                    raise DomainError(404, "Execution not found")
                review = session.get(Review, e.id)
                if not review or e.business_status != "CRITICO" or e.approval_status != "PENDING":
                    raise DomainError(409, "Only an undecided critical review can receive a decision")
                approved = "APPROVED" if request.decision == "APROBADO" else "REJECTED"
                changed = session.execute(
                    update(Execution)
                    .where(Execution.id == e.id, Execution.approval_status == "PENDING")
                    .values(approval_status=approved, technical_status="RESUMING")
                )
                if changed.rowcount != 1:
                    raise DomainError(409, "Decision already recorded")
                session.add(
                    Decision(
                        execution_id=e.id,
                        decision=request.decision,
                        actor=actor.name,
                        comment=request.comentario,
                        evidence=review.evidence,
                        policy=e.policy,
                    )
                )
                self.audit(session, e, actor.name, "human_decision", {"decision": request.decision})
        except IntegrityError:
            raise DomainError(409, "Decision already recorded") from None
        DECISIONS.labels(request.decision).inc()
        # Commit must precede graph continuation. Startup recovery closes a crash between these two steps.
        return self.run(request.ejecucion_id)

    def recover_pending(self):
        with self.factory() as session:
            ids = list(
                session.scalars(
                    select(Execution.id).where(
                        Execution.technical_status.in_(["RUNNING", "RESUMING", "WAITING_REVIEW"])
                    )
                )
            )
        for execution_id in ids:
            try:
                self.run(execution_id)
            except DomainError as error:
                log("recovery_deferred", execution_id=execution_id, result="deferred", error=error.message)


def serialize_execution(e):
    return dict(
        ejecucion_id=e.id,
        thread_id=e.thread_id,
        trace_id=e.trace_id,
        fecha=e.created_at.isoformat(),
        duracion_ms=e.duration_ms,
        request=e.request,
        technical_status=e.technical_status,
        approval_status=e.approval_status,
        estado="ERROR" if e.technical_status == "ERROR" else e.business_status,
        business_status=e.business_status,
        policy=e.policy,
        dataset_id=e.dataset_id,
        steps=sorted(e.steps.values(), key=lambda s: s["started_at"]),
        error=e.error,
        simulated_authorization=e.approval_status == "APPROVED" and e.technical_status == "COMPLETED",
        **{k: v for k, v in e.result.items() if k not in {"estado", "policy"}},
    )
