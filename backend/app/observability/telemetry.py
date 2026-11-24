import json
import logging
from datetime import UTC, datetime

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter("ortelana_http_requests", "HTTP requests", ["method", "route", "status"])
HTTP_LATENCY = Histogram("ortelana_http_seconds", "HTTP latency", ["route"])
STARTED = Counter("ortelana_executions_started", "New persisted executions")
FINISHED = Counter("ortelana_executions_finished", "Execution attempts", ["outcome"])
DURATION = Histogram("ortelana_execution_seconds", "Execution attempt latency")
NODE_LATENCY = Histogram("ortelana_node_seconds", "Deterministic node latency", ["node"])
RETRIES = Counter("ortelana_retries", "Transient infrastructure retries", ["operation"])
DECISIONS = Counter("ortelana_human_decisions", "Committed human decisions", ["decision"])
PENDING = Gauge("ortelana_pending_reviews", "Persisted pending reviews")
CRITICAL = Gauge("ortelana_critical_executions", "Persisted critical analyses")
logger = logging.getLogger("ortelana")


def log(event: str, **values):
    level = "ERROR" if event.endswith("_error") else "WARNING" if event.endswith("_deferred") else "INFO"
    logger.log(
        getattr(logging, level),
        json.dumps(
            dict(
                timestamp=datetime.now(UTC).isoformat(),
                level=level,
                service="backend",
                event=event,
                **values,
            ),
            default=str,
        ),
    )
