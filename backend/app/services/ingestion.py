import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select

from app.repositories.models import Branch, Dataset, Policy, Product, Sale

PERIODS = {"M": 12, "B": 6, "S": 2, "C": 2, "E": 2}
BRANCHES = [
    "Central Buenos Aires",
    "Córdoba",
    "Rosario",
    "Mendoza",
    "Mar del Plata",
    "Salta",
    "San Salvador de Jujuy",
    "Neuquén",
    "Ushuaia",
    "Posadas",
    "San Miguel de Tucumán",
    "Bahía Blanca",
]


def parse_record(row: dict) -> dict:
    fmt = row["Format_Reporte"].strip()
    if fmt not in PERIODS:
        raise ValueError(f"Unknown reporting format: {fmt}")
    count = PERIODS[fmt]
    values = []
    for i in range(1, 13):
        raw = row[f"Metros{i}"].strip()
        if i <= count and not raw:
            raise ValueError(f"Missing active period Metros{i}")
        try:
            value = Decimal(raw) if raw else Decimal(0)
        except InvalidOperation as exc:
            raise ValueError("Invalid metres value") from exc
        if not value.is_finite() or value < 0 or int(value.as_tuple().exponent) < -2:
            raise ValueError("Metres must be finite, non-negative and have at most two decimals")
        if i > count and value != 0:
            raise ValueError("Non-zero value in unused period")
        if i <= count:
            values.append(str(value))
    branch, year = int(row["Sucursal_ID"]), int(row["Año"])
    if not 1 <= branch <= 10000 or not 1900 <= year <= 2100:
        raise ValueError("Invalid branch or reporting year")
    return dict(
        branch_id=branch,
        year=year,
        product_id=row["Tela_ID"],
        report_format="C" if fmt == "E" else fmt,
        periods=values,
        total=sum(map(Decimal, values), Decimal(0)),
    )


def load_dataset(factory, directory: Path, mode: str) -> str:
    folder = directory / ("demo" if mode == "demo" else "private")
    sales_path, master_path = folder / "sales.csv", folder / "master.json"
    raw, master_raw = sales_path.read_bytes(), master_path.read_bytes()
    fingerprint = hashlib.sha256(mode.encode() + raw + master_raw).hexdigest()
    with factory() as session:
        if session.get(Dataset, fingerprint):
            return fingerprint
    master = json.loads(master_raw.decode("utf-8-sig"))
    ids = [p["id"] for p in master]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("Master catalog must have unique products")
    with sales_path.open(encoding="utf-8-sig", newline="") as source:
        rows = [parse_record(row) for row in csv.DictReader(source)]
    if not rows:
        raise ValueError("Dataset is empty")
    keys = [(r["branch_id"], r["year"], r["product_id"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate branch/year/product record")
    if set(r["product_id"] for r in rows) - set(ids):
        raise ValueError("Sales reference unknown products")
    years = sorted({r["year"] for r in rows})
    branches = sorted({r["branch_id"] for r in rows})
    expected = len(years) * len(branches) * len(ids)
    metadata = dict(
        rows=len(rows),
        years=years,
        branches=len(branches),
        products=len(ids),
        missing_combinations=expected - len(rows),
        expected_combinations=expected,
        formats=dict(Counter(r["report_format"] for r in rows)),
        source_sha256=hashlib.sha256(raw).hexdigest(),
        temporal_basis="reporting_year",
        synthetic=mode == "demo",
        limitations=[
            "Seasonal reports cross calendar boundaries; no monthly disaggregation.",
            "Absent records represent unknown sales, not zero.",
            "Year comparisons use matching branch/product pairs with compatible formats.",
        ],
    )
    with factory.begin() as session:
        session.add(Dataset(id=fingerprint, mode=mode, metadata_json=metadata))
        session.flush()
        session.add_all(
            [
                Product(
                    dataset_id=fingerprint, id=p["id"], name=p["nombre"], line=p["linea_textil"], details=p
                )
                for p in master
            ]
        )
        session.add_all(
            [
                Branch(dataset_id=fingerprint, id=b, name=BRANCHES[b - 1] if b <= 12 else f"Branch {b}")
                for b in branches
            ]
        )
        session.add_all([Sale(dataset_id=fingerprint, **r) for r in rows])
        if not session.scalar(select(Policy.version).limit(1)):
            session.add(Policy(version=1, warning=-10, critical=-20, created_by="bootstrap"))
    return fingerprint
