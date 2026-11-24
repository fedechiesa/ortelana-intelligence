"""Independent deterministic synthetic fixtures. Never modifies the historical dataset."""

import csv
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate():
    folder = ROOT / "data/demo"
    folder.mkdir(parents=True, exist_ok=True)
    products = [
        ("DEMO-001", "Demo Canvas Natural", "Utility", "M", "0.95"),
        ("DEMO-002", "Demo Twill Blue", "Apparel", "B", "0.85"),
        ("DEMO-003", "Demo Velvet Forest", "Upholstery", "S", "0.72"),
        ("DEMO-004", "Demo Linen Sand", "Home", "C", "1.12"),
        ("DEMO-005", "Demo Jersey Cloud", "Apparel", "M", "1.06"),
        ("DEMO-006", "Demo Jacquard Stone", "Home", "B", "0.98"),
    ]
    master = [
        dict(id=p, nombre=n, linea_textil=line, metadatos=dict(synthetic=True))
        for p, n, line, _, _ in products
    ]
    (folder / "master.json").write_text(json.dumps(master, indent=2) + "\n", encoding="utf-8", newline="\n")
    with (folder / "sales.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "Sucursal_ID",
                "Año",
                "Tela_ID",
                "Format_Reporte",
                *[f"Metros{i}" for i in range(1, 13)],
            ]
        )
        for year in range(2016, 2026):
            for branch in range(1, 5):
                for index, (product, _, _, fmt, factor) in enumerate(products):
                    count = {"M": 12, "B": 6, "S": 2, "C": 2}[fmt]
                    annual = Decimal(18000 + index * 3600 + branch * 2300 + (min(year, 2024) - 2016) * 1400)
                    if year == 2025:
                        annual *= Decimal(factor)
                    # Exact annual totals with explicitly simulated seasonal distribution.
                    value = (annual / count).quantize(Decimal("0.01"))
                    values = [value] * (count - 1) + [annual - value * (count - 1)]
                    writer.writerow(
                        [
                            branch,
                            year,
                            product,
                            fmt,
                            *map(str, values),
                            *[""] * (12 - count),
                        ]
                    )


if __name__ == "__main__":
    generate()
