"""Exercise the running local stack. All scenarios below require the independent synthetic dataset."""

import json
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]


def validate(restart=False):
    evidence = {"dataset_mode": "demo", "checks": [], "executions": []}
    with httpx.Client(
        base_url="http://127.0.0.1:8001",
        timeout=60,
        trust_env=False,
        headers={"Authorization": "Bearer demo-supervisor-local"},
    ) as client:
        assert client.get("/dataset").json()["mode"] == "demo", "This validation requires synthetic demo mode"

        def analyze(product):
            key = f"validation-{uuid4()}"
            response = client.post(
                "/analizar", headers={"Idempotency-Key": key}, json={"producto_id": product}
            )
            response.raise_for_status()
            e = response.json()
            evidence["executions"].append(
                {k: e[k] for k in ("ejecucion_id", "estado", "technical_status", "trace_id", "dataset_id")}
            )
            assert (
                client.post(
                    "/analizar", headers={"Idempotency-Key": key}, json={"producto_id": product}
                ).json()["ejecucion_id"]
                == e["ejecucion_id"]
            )
            return e

        for product, status in [("DEMO-001", "NORMAL"), ("DEMO-002", "ADVERTENCIA"), ("DEMO-003", "CRITICO")]:
            e = analyze(product)
            assert e["estado"] == status
            evidence["checks"].append(f"Live API + PostgreSQL + LangGraph: {status}; idempotency preserved")
        pending = e
        if restart:
            subprocess.run(
                ["docker", "compose", "restart", "backend"], cwd=ROOT, check=True, capture_output=True
            )
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                try:
                    if client.get("/health/ready", timeout=3).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.5)
            else:
                raise RuntimeError("Backend did not become ready after restart")
            e = client.get(f"/executions/{pending['ejecucion_id']}").json()
            assert e["approval_status"] == "PENDING" and e["technical_status"] == "WAITING_REVIEW"
            evidence["checks"].append(
                "Real backend container restart preserved interrupted PostgreSQL checkpoint"
            )
        for decision in ["APROBADO", "RECHAZADO"]:
            e = pending if decision == "APROBADO" else analyze("DEMO-003")
            body = dict(
                ejecucion_id=e["ejecucion_id"],
                decision=decision,
                comentario="SYNTHETIC DEMO stack validation",
            )
            denied = client.post(
                "/decision", json=body, headers={"Authorization": "Bearer demo-operator-local"}
            )
            assert denied.status_code == 403
            result = client.post("/decision", json=body)
            result.raise_for_status()
            assert result.json()["technical_status"] == "COMPLETED"
            assert result.json()["simulated_authorization"] == (decision == "APROBADO")
            assert client.post("/decision", json=body).status_code == 409
            evidence["checks"].append(
                f"Human {decision}: persisted, resumed; unauthorized and duplicate requests rejected"
            )
        assert "ortelana_http_requests_total" in client.get("/metrics").text
    with httpx.Client(timeout=30, trust_env=False) as client:
        for _attempt in range(21):
            up = client.get(
                "http://127.0.0.1:9090/api/v1/query", params={"query": 'up{job="ortelana-api"}'}
            ).json()
            if up["data"]["result"] and up["data"]["result"][0]["value"][1] == "1":
                break
            time.sleep(1)  # Wait for the next real scrape after a container restart.
        else:
            raise AssertionError("Prometheus has not scraped a healthy backend")
        evidence["checks"].append("Prometheus scraping actual backend metrics: up=1")
    with httpx.Client(
        base_url="http://127.0.0.1:3000", auth=("admin", "demo-grafana-local"), timeout=30, trust_env=False
    ) as grafana:
        for uid in ["ortelana-pg", "ortelana-prom"]:
            response = grafana.get(f"/api/datasources/uid/{uid}/health")
            response.raise_for_status()
            assert response.json()["status"] == "OK", response.text
        for path in (ROOT / "infrastructure/grafana/provisioning/dashboards/json").glob("*.json"):
            dashboard = json.loads(path.read_text(encoding="utf-8"))
            published = grafana.get(f"/api/dashboards/uid/{dashboard['uid']}")
            published.raise_for_status()
            for panel in dashboard["panels"]:
                target = {
                    **panel["targets"][0],
                    "datasource": panel["datasource"],
                    "intervalMs": 10000,
                    "maxDataPoints": 1000,
                }
                response = grafana.post(
                    "/api/ds/query",
                    json={
                        "queries": [target],
                        "from": str(int((time.time() - 86400) * 1000)),
                        "to": str(int(time.time() * 1000)),
                    },
                )
                response.raise_for_status()
                result = response.json()["results"]["A"]
                assert not result.get("error"), f"{panel['title']}: {result}"
                evidence["checks"].append(f"Grafana executed real datasource query: {panel['title']}")
    folder = ROOT / ".local/validation"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "stack.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    for check in evidence["checks"]:
        print("PASS", check)
    print(f"Validated {len(evidence['checks'])} checks; local evidence: .local/validation/stack.json")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--restart-backend", action="store_true")
    validate(parser.parse_args().restart_backend)
