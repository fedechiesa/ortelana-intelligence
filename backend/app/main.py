import logging
import sqlite3
from contextlib import ExitStack, asynccontextmanager
from pathlib import Path
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import func, select, text

from app.api.routes import router
from app.core.config import DomainError, Settings
from app.observability.telemetry import CRITICAL, HTTP_LATENCY, HTTP_REQUESTS, PENDING, log
from app.repositories.database import make_database
from app.repositories.models import Execution
from app.services.executions import ExecutionService
from app.services.ingestion import load_dataset


def create_app(settings: Settings | None = None):
    cfg = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        engine, factory = make_database(cfg.database_url)
        saver: BaseCheckpointSaver
        with ExitStack() as stack:
            if engine.dialect.name == "postgresql":
                postgres_saver = stack.enter_context(
                    PostgresSaver.from_conn_string(
                        cfg.database_url.replace("postgresql+psycopg://", "postgresql://")
                    )
                )
                postgres_saver.setup()
                saver = postgres_saver
            else:
                Path(cfg.checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
                connection = sqlite3.connect(cfg.checkpoint_path, check_same_thread=False)
                stack.callback(connection.close)
                saver = SqliteSaver(connection)
            try:
                dataset_id = load_dataset(factory, cfg.data_dir, cfg.data_mode)
                app.state.service = ExecutionService(engine, factory, dataset_id, saver)
                app.state.settings = cfg
                app.state.service.recover_pending()
                yield
            finally:
                engine.dispose()

    app = FastAPI(
        title="Ortelana Intelligence",
        version="1.0.0",
        lifespan=lifespan,
        description="Deterministic reporting-year analysis and durable human supervision. "
        "Use a local bearer token. All commercial actions are simulated.",
    )

    @app.middleware("http")
    async def correlation(request, call_next):
        raw_trace = request.headers.get("X-Correlation-ID", "")
        try:
            trace_id = str(UUID(raw_trace))
        except ValueError:
            trace_id = str(uuid4())
        request.state.trace_id = trace_id
        start = perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            log("http_error", trace_id=trace_id, error=type(exc).__name__, result="ERROR")
            response = JSONResponse(
                status_code=500, content=dict(detail="Internal service error", trace_id=trace_id)
            )
        route = getattr(request.scope.get("route"), "path", "unmatched")
        HTTP_REQUESTS.labels(request.method, route, str(response.status_code)).inc()
        HTTP_LATENCY.labels(route).observe(perf_counter() - start)
        if route not in ("/health/ready", "/health/live", "/salud", "/metrics"):
            log(
                "http_completed",
                trace_id=trace_id,
                route=route,
                method=request.method,
                duration_ms=round((perf_counter() - start) * 1000, 2),
                result=response.status_code,
            )
        response.headers["X-Correlation-ID"] = trace_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse(
            status_code=exc.status, content=dict(detail=exc.message, trace_id=request.state.trace_id)
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        return JSONResponse(
            status_code=422,
            content=dict(
                detail="Invalid request",
                trace_id=request.state.trace_id,
                errors=[dict(location=list(e["loc"]), message=e["msg"]) for e in exc.errors()],
            ),
        )

    @app.get("/salud", tags=["Health"])
    @app.get("/health/live", tags=["Health"])
    def live():
        return dict(status="ok", sistema="ortelana")

    @app.get("/health/ready", tags=["Health"])
    def ready(request: Request):
        try:
            with request.app.state.service.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            request.app.state.service.graph.get_state({"configurable": {"thread_id": "readiness-check"}})
            return dict(status="ready", database="connected", checkpoint="initialized")
        except Exception:
            return JSONResponse(status_code=503, content=dict(status="not_ready"))

    @app.get("/metrics", tags=["Observability"])
    def metrics(request: Request):
        with request.app.state.service.factory() as session:
            PENDING.set(
                session.scalar(
                    select(func.count()).select_from(Execution).where(Execution.approval_status == "PENDING")
                )
            )
            CRITICAL.set(
                session.scalar(
                    select(func.count()).select_from(Execution).where(Execution.business_status == "CRITICO")
                )
            )
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(router)
    return app


app = create_app()
