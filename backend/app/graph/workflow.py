import operator
from collections.abc import Callable
from time import perf_counter
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.observability.telemetry import NODE_LATENCY, log
from app.repositories.models import now


class AnalysisState(TypedDict, total=False):
    execution_id: str
    dataset_id: str
    trace_id: str
    request: dict
    policy: dict
    sales: dict
    products: list[dict]
    branches: list[dict]
    risk: dict
    report: dict
    authorized: bool
    # Parallel branches append independent records. Nodes have no repeated side effects.
    steps: Annotated[list[dict], operator.add]


def build_graph(analytics, persist_report: Callable, read_decision: Callable, checkpointer):
    def measured(name, function):
        def node(state):
            start, timestamp = perf_counter(), now().isoformat()
            try:
                result = function(state)
            except Exception as exc:
                # LangGraph interrupt inherits BaseException; never swallow it as an error.
                elapsed = perf_counter() - start
                NODE_LATENCY.labels(name).observe(elapsed)
                log(
                    "node_error",
                    execution_id=state["execution_id"],
                    thread_id=state["execution_id"],
                    trace_id=state["trace_id"],
                    node=name,
                    duration_ms=round(elapsed * 1000, 2),
                    result="ERROR",
                    error=type(exc).__name__,
                )
                raise
            elapsed = perf_counter() - start
            NODE_LATENCY.labels(name).observe(elapsed)
            step = dict(
                node=name, started_at=timestamp, duration_ms=round(elapsed * 1000, 2), outcome="completed"
            )
            log(
                "node_completed",
                execution_id=state["execution_id"],
                thread_id=state["execution_id"],
                trace_id=state["trace_id"],
                node=name,
                duration_ms=step["duration_ms"],
                result="completed",
            )
            return {**result, "steps": [step]}

        return node

    def coordinate(state):
        analytics.validate(state["dataset_id"], state["request"])
        return {}

    def sales(state):
        return {"sales": analytics.summary(state["dataset_id"], state["request"], state["policy"])}

    def products(state):
        return {
            "products": analytics.rankings(
                state["dataset_id"], state["request"], state["policy"], "product_id"
            )
        }

    def branches(state):
        return {
            "branches": analytics.rankings(
                state["dataset_id"], state["request"], state["policy"], "branch_id"
            )
        }

    def risk(state):
        alerts = [
            dict(scope="product", **item)
            for item in state["products"]
            if item["status"] in ("CRITICO", "ADVERTENCIA")
        ]
        alerts += [
            dict(scope="branch", **item)
            for item in state["branches"]
            if item["status"] in ("CRITICO", "ADVERTENCIA")
        ]
        statuses = {state["sales"]["status"], *(a["status"] for a in alerts)}
        # A network average must not conceal a critical segment.
        overall = next(s for s in ["CRITICO", "ADVERTENCIA", "NORMAL", "SIN_BASE"] if s in statuses)
        return {
            "risk": dict(
                status=overall,
                alerts=alerts,
                reason="Highest evidence-backed risk across network, products and branches",
            )
        }

    def report(state):
        status = state["risk"]["status"]
        recommendation = {
            "CRITICO": (
                "Review the declining segments and validate a recovery plan. Human authorization is required."
            ),
            "ADVERTENCIA": "Monitor declining segments and review the next comparable reporting period.",
            "NORMAL": "Maintain monitoring; no material decline under the selected policy.",
            "SIN_BASE": "Collect a non-zero, comparable baseline before drawing a commercial conclusion.",
        }[status]
        result = dict(
            producto=state["request"].get("producto_id") or "All selected products",
            variacion=state["sales"]["variation"],
            estado=status,
            recomendacion=recommendation,
            agentes=["coordinator", "sales", "products", "branches", "risk", "report"],
            sales=state["sales"],
            products=state["products"],
            branches=state["branches"],
            alerts=state["risk"]["alerts"],
            policy=state["policy"],
            risk_basis=state["risk"]["reason"],
            limitations=[
                "Reporting-year totals; seasonal periods can cross calendar years.",
                "Comparisons exclude absent and incompatible branch/product pairs.",
                "Recommendations and authorizations are simulations; no commercial action occurs.",
            ],
        )
        persist_report(state["execution_id"], result)
        return {"report": result}

    def human_review(state):
        # interrupt is outside exception handling and has no side effect before it.
        interrupt(
            dict(
                execution_id=state["execution_id"],
                status="PENDING",
                recommendation=state["report"]["recomendacion"],
            )
        )
        # The resume payload is never trusted as authority. Read the committed authenticated decision.
        decision = read_decision(state["execution_id"])
        if decision is None:
            raise ValueError("A persisted human decision is required")
        return {"authorized": decision == "APROBADO"}

    def finish(state):
        return {"authorized": state.get("authorized", False)}

    graph = StateGraph(AnalysisState)
    functions: dict[str, Any] = dict(
        coordinator=coordinate,
        sales=sales,
        products=products,
        branches=branches,
        risk=risk,
        report=report,
        human_review=human_review,
        finish=finish,
    )
    for name, function in functions.items():
        graph.add_node(name, measured(name, function))
    graph.add_edge(START, "coordinator")
    for name in ("sales", "products", "branches"):
        graph.add_edge("coordinator", name)
    graph.add_edge(["sales", "products", "branches"], "risk")
    graph.add_edge("risk", "report")
    graph.add_conditional_edges(
        "report",
        lambda s: "review" if s["risk"]["status"] == "CRITICO" else "done",
        {"review": "human_review", "done": "finish"},
    )
    graph.add_edge("human_review", "finish")
    graph.add_edge("finish", END)
    return graph.compile(checkpointer=checkpointer)
