from decimal import Decimal

import pandas as pd
import pytest
from app.domain.calculations import classify, variation
from app.schemas.contracts import AnalysisRequest, PolicyRequest
from app.services.analytics import Analytics
from app.services.ingestion import parse_record


@pytest.mark.parametrize(
    "value,expected",
    [
        ("-9.99999", "NORMAL"),
        ("-10", "ADVERTENCIA"),
        ("-19.99999", "ADVERTENCIA"),
        ("-20", "CRITICO"),
        ("-100", "CRITICO"),
        ("0", "NORMAL"),
    ],
)
def test_exact_thresholds_without_rounding(value, expected):
    assert classify(Decimal(value)) == expected


@pytest.mark.parametrize("base,current", [(None, Decimal(1)), (Decimal(0), Decimal(5)), (Decimal(5), None)])
def test_absent_or_zero_baseline_is_not_a_percentage(base, current):
    assert variation(base, current) is None
    assert classify(variation(base, current)) == "SIN_BASE"


def test_real_percentage():
    assert variation(Decimal(120), Decimal(90)) == Decimal(-25)


def row(fmt="B"):
    return dict(
        Sucursal_ID="1",
        Año="2025",
        Tela_ID="P",
        Format_Reporte=fmt,
        **{
            f"Metros{i}": "10.25" if i <= {"M": 12, "B": 6, "S": 2, "C": 2, "E": 2}[fmt] else ""
            for i in range(1, 13)
        },
    )


@pytest.mark.parametrize("fmt,count", [("M", 12), ("B", 6), ("S", 2), ("C", 2), ("E", 2)])
def test_report_granularity_and_alias(fmt, count):
    result = parse_record(row(fmt))
    assert len(result["periods"]) == count
    assert result["total"] == Decimal("10.25") * count
    assert result["report_format"] == ("C" if fmt == "E" else fmt)


@pytest.mark.parametrize(
    "field,value",
    [
        ("Metros1", ""),
        ("Metros1", "NaN"),
        ("Metros1", "Infinity"),
        ("Metros1", "-1"),
        ("Metros1", "1.234"),
        ("Metros12", "10"),
        ("Format_Reporte", "X"),
    ],
)
def test_invalid_reporting_data_is_rejected(field, value):
    data = row()
    data[field] = value
    with pytest.raises(ValueError):
        parse_record(data)


def test_missing_pairs_are_excluded_not_treated_as_zero():
    rows = [
        dict(branch_id=1, product_id="A", year=2024, format="M", total=Decimal(100)),
        dict(branch_id=1, product_id="A", year=2025, format="M", total=Decimal(95)),
        dict(branch_id=2, product_id="A", year=2024, format="M", total=Decimal(900)),
    ]
    result = Analytics.compare(pd.DataFrame(rows), 2024, 2025, dict(warning=-10, critical=-20))
    assert result["variation"] == -5
    assert result["coverage_pct"] == 50
    assert result["observed_base"] == 1000
    assert result["base_total"] == 100


def test_seasonal_to_calendar_format_change_cannot_be_compared():
    data = pd.DataFrame(
        [
            dict(branch_id=1, product_id="A", year=y, format=f, total=Decimal(100))
            for y, f in [(2024, "C"), (2025, "S")]
        ]
    )
    result = Analytics.compare(data, 2024, 2025, dict(warning=-10, critical=-20))
    assert result["status"] == "SIN_BASE"
    assert result["matched_pairs"] == 0


def test_strict_requests_and_policy_order():
    for data in [dict(anio_base="2024"), dict(anio_base=2025, anio_actual=2024), dict(unknown=True)]:
        with pytest.raises(ValueError):
            AnalysisRequest(**data)
    with pytest.raises(ValueError):
        PolicyRequest(warning=-20, critical=-10)
