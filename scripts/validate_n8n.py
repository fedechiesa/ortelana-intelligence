"""Execute real n8n engine scenarios with clearly labeled synthetic inputs. Originals stay inactive."""

import copy
import json
import subprocess
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def docker(*args):
    result = subprocess.run(
        ["docker", "compose", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:] + result.stdout[-2000:])
    return result.stdout


def main():
    source = json.loads((ROOT / "workflows/manual-analysis.json").read_text(encoding="utf-8"))
    folder = ROOT / ".local/validation"
    folder.mkdir(parents=True, exist_ok=True)
    results = []
    scenarios = [
        ("normal", "DEMO-001", "Normal recorded"),
        ("warning", "DEMO-002", "Warning recorded"),
        ("critical", "DEMO-003", "Human review required"),
        ("invalid-year", "DEMO-001", "Technical error recorded"),
        ("transient-retry", "DEMO-001", "Normal recorded"),
    ]
    for name, product, expected in scenarios:
        workflow = copy.deepcopy(source)
        workflow["id"] = "test" + uuid4().hex[:12]
        workflow["name"] = f"SYNTHETIC VALIDATION | {name}"
        prepare = next(n for n in workflow["nodes"] if n["name"] == "Prepare request")
        values = prepare["parameters"]["assignments"]["assignments"]
        next(v for v in values if v["name"] == "producto_id")["value"] = product
        if name == "invalid-year":
            next(v for v in values if v["name"] == "anio_actual")["value"] = 2028
        if name == "transient-retry":
            next(n for n in workflow["nodes"] if n["name"] == "Analyze via API")["parameters"]["url"] = (
                "http://backend:1/analizar"
            )
        path = folder / "n8n-synthetic-scenario.json"
        path.write_text(json.dumps(workflow), encoding="utf-8")
        docker("cp", str(path), "n8n:/tmp/ortelana-scenario.json")
        docker("exec", "-T", "n8n", "n8n", "import:workflow", "--input=/tmp/ortelana-scenario.json")
        output = docker(
            "exec",
            "-T",
            "-e",
            "N8N_RUNNERS_BROKER_PORT=5680",
            "n8n",
            "n8n",
            "execute",
            "--id",
            workflow["id"],
            "--rawOutput",
        )
        start = output.index('{\n  "data"')
        result = json.JSONDecoder().raw_decode(output[start:])[0]
        assert result["status"] == "success", result["status"]
        data = result["data"]["resultData"]
        assert data["lastNodeExecuted"] == expected, (name, data["lastNodeExecuted"])
        nodes = list(data["runData"])
        assert ("Retry once safely" in nodes) == (name == "transient-retry"), nodes
        final = data["runData"][expected][0]["data"]["main"][0][0]["json"]
        results.append(dict(scenario=name, status="passed", last_node=expected, nodes=nodes, **final))
        print("PASS real n8n engine:", name, "->", expected, flush=True)
    (folder / "n8n.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print("All five real n8n scenarios passed. Test workflows remain unpublished.")


if __name__ == "__main__":
    main()
