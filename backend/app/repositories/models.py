from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now():
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    mode: Mapped[str] = mapped_column(String(20))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Product(Base):
    __tablename__ = "products"
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), primary_key=True)
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    line: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON)


class Branch(Base):
    __tablename__ = "branches"
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), primary_key=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("dataset_id", "branch_id", "product_id", "year"),
        CheckConstraint("total >= 0"),
        Index("ix_sales_dataset_year", "dataset_id", "year"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))
    branch_id: Mapped[int]
    product_id: Mapped[str] = mapped_column(String(40))
    year: Mapped[int]
    report_format: Mapped[str] = mapped_column(String(1))
    periods: Mapped[list] = mapped_column(JSON)
    total: Mapped[Any] = mapped_column(Numeric(18, 2))


class Policy(Base):
    __tablename__ = "policies"
    version: Mapped[int] = mapped_column(primary_key=True)
    warning: Mapped[float]
    critical: Mapped[float]
    created_by: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Execution(Base):
    __tablename__ = "executions"
    __table_args__ = (
        CheckConstraint("technical_status IN ('RUNNING','WAITING_REVIEW','RESUMING','COMPLETED','ERROR')"),
        CheckConstraint("approval_status IN ('NOT_REQUIRED','PENDING','APPROVED','REJECTED')"),
        CheckConstraint(
            "business_status IS NULL OR business_status IN ('NORMAL','ADVERTENCIA','CRITICO','SIN_BASE')"
        ),
        Index("ix_execution_created", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(36), unique=True)
    trace_id: Mapped[str] = mapped_column(String(36))
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"))
    requested_by: Mapped[str] = mapped_column(String(100))
    request: Mapped[dict] = mapped_column(JSON)
    policy: Mapped[dict] = mapped_column(JSON)
    technical_status: Mapped[str] = mapped_column(String(30), default="RUNNING")
    business_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(20), default="NOT_REQUIRED")
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    steps: Mapped[dict] = mapped_column(JSON, default=dict)
    duration_ms: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Review(Base):
    __tablename__ = "reviews"
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    evidence: Mapped[dict] = mapped_column(JSON)


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (CheckConstraint("decision IN ('APROBADO','RECHAZADO')"),)
    execution_id: Mapped[str] = mapped_column(ForeignKey("reviews.execution_id"), primary_key=True)
    decision: Mapped[str] = mapped_column(String(20))
    actor: Mapped[str] = mapped_column(String(100))
    comment: Mapped[str] = mapped_column(String(2000))
    evidence: Mapped[dict] = mapped_column(JSON)
    policy: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Audit(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    execution_id: Mapped[str | None] = mapped_column(ForeignKey("executions.id"), nullable=True)
    actor: Mapped[str] = mapped_column(String(100))
    event: Mapped[str] = mapped_column(String(80))
    trace_id: Mapped[str] = mapped_column(String(36))
    detail: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
