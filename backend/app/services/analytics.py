from decimal import Decimal

import pandas as pd
from sqlalchemy import select

from app.core.config import DomainError
from app.domain.calculations import classify, variation
from app.repositories.models import Branch, Dataset, Product, Sale


class Analytics:
    def __init__(self, factory):
        self.factory = factory

    def frame(self, dataset_id: str, request: dict):
        query = (
            select(Sale, Product)
            .join(Product, (Product.dataset_id == Sale.dataset_id) & (Product.id == Sale.product_id))
            .where(Sale.dataset_id == dataset_id)
        )
        for key, field in [
            ("sucursal_id", Sale.branch_id),
            ("producto_id", Sale.product_id),
            ("linea_textil", Product.line),
        ]:
            if request.get(key) is not None:
                query = query.where(field == request[key])
        with self.factory() as session:
            rows = session.execute(query).all()
        return pd.DataFrame(
            [
                dict(
                    branch_id=s.branch_id,
                    product_id=s.product_id,
                    year=s.year,
                    format=s.report_format,
                    total=s.total,
                    name=p.name,
                    line=p.line,
                )
                for s, p in rows
            ],
            columns=["branch_id", "product_id", "year", "format", "total", "name", "line"],
        )

    def validate(self, dataset_id, request):
        frame = self.frame(dataset_id, request)
        if frame.empty:
            raise DomainError(422, "No records match these filters")
        with self.factory() as session:
            years = set(session.get(Dataset, dataset_id).metadata_json["years"])
        if request["anio_base"] not in years or request["anio_actual"] not in years:
            raise DomainError(422, "Both reporting years must exist for the selected filters")

    @staticmethod
    def compare(frame, base_year: int, current_year: int, policy: dict):
        base = frame[frame.year == base_year]
        current = frame[frame.year == current_year]
        matched = base.merge(current, on=["branch_id", "product_id"], suffixes=("_base", "_current"))
        # Monthly/bimonthly/semester cover a calendar year; season totals form a different basis.
        if not matched.empty:
            compatible = (matched.format_base == "C") == (matched.format_current == "C")
            matched = matched[compatible]
        baseline = sum(matched.total_base, Decimal(0)) if len(matched) else None
        actual = sum(matched.total_current, Decimal(0)) if len(matched) else None
        change = variation(baseline, actual)
        union = set(zip(base.branch_id, base.product_id, strict=True)) | set(
            zip(current.branch_id, current.product_id, strict=True)
        )
        return dict(
            base_total=float(baseline) if baseline is not None else None,
            current_total=float(actual) if actual is not None else None,
            observed_base=float(sum(base.total, Decimal(0))) if len(base) else None,
            observed_current=float(sum(current.total, Decimal(0))) if len(current) else None,
            variation=float(change) if change is not None else None,
            status=classify(change, policy["warning"], policy["critical"]),
            matched_pairs=len(matched),
            base_records=len(base),
            current_records=len(current),
            excluded_pairs=len(union) - len(matched),
            coverage_pct=round(100 * len(matched) / len(union), 2) if union else 0,
            temporal_basis="reporting_year",
            comparison="matched_branch_product_pairs",
        )

    def summary(self, dataset_id, request, policy):
        return self.compare(
            self.frame(dataset_id, request), request["anio_base"], request["anio_actual"], policy
        )

    def rankings(self, dataset_id, request, policy, dimension):
        frame = self.frame(dataset_id, request)
        with self.factory() as session:
            branches = {
                b.id: b.name for b in session.scalars(select(Branch).where(Branch.dataset_id == dataset_id))
            }
        items = []
        for key, group in frame.groupby(dimension, sort=True):
            item = self.compare(group, request["anio_base"], request["anio_actual"], policy)
            item.update(
                id=int(key) if dimension == "branch_id" else str(key),
                name=branches[int(key)] if dimension == "branch_id" else str(group.iloc[0]["name"]),
                line=str(group.iloc[0]["line"]) if dimension == "product_id" else None,
            )
            items.append(item)
        return sorted(items, key=lambda i: -(i["observed_current"] or 0))

    def trends(self, dataset_id, request):
        frame = self.frame(dataset_id, request)
        return [
            dict(year=int(year), total=float(sum(group.total, Decimal(0))), records=len(group))
            for year, group in frame.groupby("year", sort=True)
        ]
