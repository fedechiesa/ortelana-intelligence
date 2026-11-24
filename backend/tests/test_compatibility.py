"""Independent synthetic cases for the public result adapter."""

import pytest
from src.adaptador import normalizar_resultado


@pytest.mark.parametrize("status,change", [("NORMAL", -5), ("SIN_BASE", None)])
def test_adapter_preserves_comparison_and_trace_fields(status, change):
    payload = {
        "producto": "DEMO-001",
        "variacion": change,
        "estado": status,
        "recomendacion": "Synthetic validation",
        "agentes": ["sales"],
        "trace_id": "synthetic-adapter-check",
    }
    assert normalizar_resultado(payload) == payload


@pytest.mark.parametrize("changes", [{"variacion": float("nan")}, {"agentes": []}, {"variacion": None}])
def test_adapter_rejects_nonfinite_empty_or_inconsistent_evidence(changes):
    payload = dict(
        producto="DEMO-002",
        variacion=-15,
        estado="ADVERTENCIA",
        recomendacion="Synthetic validation",
        agentes=["risk"],
    )
    with pytest.raises(ValueError):
        normalizar_resultado({**payload, **changes})
