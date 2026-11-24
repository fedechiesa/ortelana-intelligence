from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.config import DomainError
from app.core.security import Actor, authenticate, supervisor
from app.repositories.models import Audit, Branch, Dataset, Decision, Execution, Policy, Product
from app.schemas.contracts import (
    AnalysisFilters,
    AnalysisRequest,
    DecisionRequest,
    ExecutionPage,
    ExecutionResponse,
    PolicyRequest,
)
from app.services.executions import serialize_execution

router = APIRouter(dependencies=[Depends(authenticate)])
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


def service(request):
    return request.app.state.service


def paginate(session, query, page, page_size):
    total = session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    return session.scalars(query.offset((page - 1) * page_size).limit(page_size)).all(), total


@router.get("/auth/me", tags=["Identity"])
def identity(actor: Annotated[Actor, Depends(authenticate)]):
    return dict(name=actor.name, role=actor.role)


@router.post(
    "/analizar",
    response_model=ExecutionResponse,
    tags=["Analysis"],
    responses={409: {"description": "Idempotency conflict"}, 422: {"description": "Invalid comparison"}},
)
def analyze(
    body: AnalysisRequest,
    request: Request,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=120)],
    actor: Annotated[Actor, Depends(authenticate)],
):
    svc = service(request)
    e, created = svc.create(body.model_dump(), idempotency_key, actor, request.state.trace_id)
    if created:
        e = svc.run(e.id)
    return {**serialize_execution(e), "replayed": not created}


@router.post(
    "/decision",
    response_model=ExecutionResponse,
    tags=["Human review"],
    responses={
        403: {"description": "Supervisor required"},
        409: {"description": "Not a pending critical review"},
    },
)
def decide(body: DecisionRequest, request: Request, actor: Annotated[Actor, Depends(supervisor)]):
    return serialize_execution(service(request).decide(body, actor))


@router.get("/executions", tags=["Executions"], response_model=ExecutionPage)
def executions(
    request: Request,
    page: Page = 1,
    page_size: PageSize = 20,
    status: Annotated[
        str | None, Query(pattern="^(RUNNING|WAITING_REVIEW|RESUMING|COMPLETED|ERROR)$")
    ] = None,
    risk: Annotated[str | None, Query(pattern="^(NORMAL|ADVERTENCIA|CRITICO|SIN_BASE)$")] = None,
):
    query = select(Execution).order_by(Execution.created_at.desc())
    if status:
        query = query.where(Execution.technical_status == status)
    if risk:
        query = query.where(Execution.business_status == risk)
    with service(request).factory() as session:
        items, total = paginate(session, query, page, page_size)
        return dict(items=list(map(serialize_execution, items)), total=total, page=page, page_size=page_size)


@router.get("/executions/{execution_id}", tags=["Executions"], response_model=ExecutionResponse)
def execution(execution_id: str, request: Request):
    return serialize_execution(service(request).get(execution_id))


@router.post("/executions/{execution_id}/recover", tags=["Executions"], response_model=ExecutionResponse)
def recover(execution_id: str, request: Request, actor: Annotated[Actor, Depends(supervisor)]):
    svc = service(request)
    e = svc.get(execution_id)
    if e.technical_status == "COMPLETED":
        raise DomainError(409, "Execution already completed")
    with svc.factory.begin() as session:
        svc.audit(session, e, actor.name, "recovery_requested")
    return serialize_execution(svc.run(execution_id))


@router.get("/dataset", tags=["Data"])
def dataset(request: Request):
    svc = service(request)
    with svc.factory() as session:
        d = session.get(Dataset, svc.dataset_id)
        return dict(id=d.id, mode=d.mode, **d.metadata_json)


@router.get("/products", tags=["Data"])
def products(request: Request, page: Page = 1, page_size: PageSize = 100, line: str | None = None):
    svc = service(request)
    query = select(Product).where(Product.dataset_id == svc.dataset_id).order_by(Product.id)
    if line:
        query = query.where(Product.line == line)
    with svc.factory() as session:
        items, total = paginate(session, query, page, page_size)
        return dict(items=[dict(id=p.id, name=p.name, line=p.line) for p in items], total=total)


@router.get("/branches", tags=["Data"])
def branches(request: Request):
    svc = service(request)
    with svc.factory() as session:
        return [
            dict(id=b.id, name=b.name)
            for b in session.scalars(
                select(Branch).where(Branch.dataset_id == svc.dataset_id).order_by(Branch.id)
            )
        ]


@router.get("/analytics", tags=["Business intelligence"])
def analytics(request: Request, filters: Annotated[AnalysisFilters, Query()]):
    svc = service(request)
    data, policy = filters.model_dump(), svc.policy()
    svc.analytics.validate(svc.dataset_id, data)
    return dict(
        summary=svc.analytics.summary(svc.dataset_id, data, policy),
        products=svc.analytics.rankings(svc.dataset_id, data, policy, "product_id"),
        branches=svc.analytics.rankings(svc.dataset_id, data, policy, "branch_id"),
        trends=svc.analytics.trends(svc.dataset_id, data),
        policy=policy,
    )


@router.get("/trends", tags=["Business intelligence"])
def trends(request: Request, sucursal_id: int | None = None, producto_id: str | None = None):
    svc = service(request)
    return svc.analytics.trends(svc.dataset_id, dict(sucursal_id=sucursal_id, producto_id=producto_id))


@router.get("/indicators", tags=["Business intelligence"])
def indicators(request: Request):
    svc = service(request)
    with svc.factory() as session:
        states = dict(
            session.execute(
                select(Execution.technical_status, func.count()).group_by(Execution.technical_status)
            ).all()
        )
        risk = dict(
            session.execute(
                select(Execution.business_status, func.count())
                .where(Execution.business_status.is_not(None))
                .group_by(Execution.business_status)
            ).all()
        )
        pending = session.scalar(
            select(func.count()).select_from(Execution).where(Execution.approval_status == "PENDING")
        )
        average = session.scalar(
            select(func.avg(Execution.duration_ms)).where(
                Execution.technical_status.in_(["COMPLETED", "WAITING_REVIEW"])
            )
        )
    total = sum(states.values())
    successful = states.get("COMPLETED", 0) + states.get("WAITING_REVIEW", 0)
    return dict(
        executions=total,
        successful=successful,
        errors=states.get("ERROR", 0),
        success_rate=round(100 * successful / total, 1) if total else None,
        pending_reviews=pending,
        critical=risk.get("CRITICO", 0),
        average_duration_ms=round(average, 1) if average is not None else None,
        states=states,
        risks=risk,
    )


@router.get("/alerts", tags=["Human review"], response_model=ExecutionPage)
def alerts(request: Request, page: Page = 1, page_size: PageSize = 20):
    query = (
        select(Execution)
        .where(Execution.business_status.in_(["CRITICO", "ADVERTENCIA"]))
        .order_by(Execution.created_at.desc())
    )
    with service(request).factory() as session:
        items, total = paginate(session, query, page, page_size)
        return dict(items=list(map(serialize_execution, items)), total=total, page=page, page_size=page_size)


@router.get("/reviews", tags=["Human review"], response_model=ExecutionPage)
def reviews(
    request: Request,
    page: Page = 1,
    page_size: PageSize = 20,
    status: Annotated[str, Query(pattern="^(PENDING|APPROVED|REJECTED|ALL)$")] = "PENDING",
):
    query = (
        select(Execution).where(Execution.business_status == "CRITICO").order_by(Execution.created_at.desc())
    )
    if status != "ALL":
        query = query.where(Execution.approval_status == status)
    with service(request).factory() as session:
        items, total = paginate(session, query, page, page_size)
        return dict(items=list(map(serialize_execution, items)), total=total, page=page, page_size=page_size)


@router.get("/decisions", tags=["Human review"])
def decisions(request: Request, page: Page = 1, page_size: PageSize = 20):
    with service(request).factory() as session:
        items, total = paginate(
            session, select(Decision).order_by(Decision.created_at.desc()), page, page_size
        )
        return dict(
            items=[
                dict(
                    execution_id=d.execution_id,
                    decision=d.decision,
                    actor=d.actor,
                    comment=d.comment,
                    policy=d.policy,
                    created_at=d.created_at.isoformat(),
                )
                for d in items
            ],
            total=total,
        )


@router.get("/audit", tags=["Audit"])
def audit(request: Request, page: Page = 1, page_size: PageSize = 20, execution_id: str | None = None):
    query = select(Audit).order_by(Audit.id.desc())
    if execution_id:
        query = query.where(Audit.execution_id == execution_id)
    with service(request).factory() as session:
        items, total = paginate(session, query, page, page_size)
        return dict(
            items=[
                dict(
                    id=a.id,
                    execution_id=a.execution_id,
                    actor=a.actor,
                    event=a.event,
                    trace_id=a.trace_id,
                    detail=a.detail,
                    created_at=a.created_at.isoformat(),
                )
                for a in items
            ],
            total=total,
        )


@router.get("/policies", tags=["Settings"])
def policies(request: Request):
    svc = service(request)
    with svc.factory() as session:
        return [
            dict(
                version=p.version,
                warning=p.warning,
                critical=p.critical,
                actor=p.created_by,
                created_at=p.created_at.isoformat(),
            )
            for p in session.scalars(select(Policy).order_by(Policy.version.desc()))
        ]


@router.post("/policies", status_code=201, tags=["Settings"])
def policy(body: PolicyRequest, request: Request, actor: Annotated[Actor, Depends(supervisor)]):
    svc = service(request)
    try:
        with svc.factory.begin() as session:
            version = (session.scalar(select(func.max(Policy.version))) or 0) + 1
            session.add(Policy(version=version, **body.model_dump(), created_by=actor.name))
            svc.audit(
                session,
                None,
                actor.name,
                "policy_created",
                dict(version=version, **body.model_dump()),
                trace_id=request.state.trace_id,
            )
    except IntegrityError:
        raise DomainError(409, "Concurrent policy update; reload and retry") from None
    return dict(version=version, **body.model_dump())
