from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sucursal_id: int | None = Field(default=None, ge=1, le=10000)
    producto_id: str | None = Field(default=None, min_length=1, max_length=40)
    linea_textil: str | None = Field(default=None, max_length=100)
    anio_base: int = Field(default=2024, ge=1900, le=2100)
    anio_actual: int = Field(default=2025, ge=1900, le=2100)

    @model_validator(mode="after")
    def different_years(self):
        if self.anio_actual <= self.anio_base:
            raise ValueError("Current reporting year must follow the baseline year")
        return self


class AnalysisFilters(AnalysisRequest):
    # Query strings arrive as text; POST JSON remains strictly typed.
    model_config = ConfigDict(extra="forbid", strict=False)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    ejecucion_id: str = Field(pattern=r"^[0-9a-f-]{36}$")
    decision: Literal["APROBADO", "RECHAZADO"]
    comentario: str = Field(min_length=3, max_length=2000)

    @field_validator("comentario")
    @classmethod
    def meaningful_comment(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("A meaningful review comment is required")
        return value.strip()


class PolicyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    warning: float = Field(default=-10, ge=-100, lt=0, allow_inf_nan=False)
    critical: float = Field(default=-20, ge=-100, lt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def ordered(self):
        if self.critical >= self.warning:
            raise ValueError("Critical threshold must be below warning threshold")
        return self


class LegacyResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    producto: str
    variacion: float | None = Field(allow_inf_nan=False)
    estado: Literal["NORMAL", "ADVERTENCIA", "CRITICO", "SIN_BASE"]
    recomendacion: str
    agentes: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def comparable(self):
        if (self.variacion is None) != (self.estado == "SIN_BASE"):
            raise ValueError("Missing comparison must be represented by SIN_BASE")
        return self


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    ejecucion_id: str
    thread_id: str
    trace_id: str
    fecha: str
    duracion_ms: int = Field(ge=0)
    estado: Literal["NORMAL", "ADVERTENCIA", "CRITICO", "SIN_BASE", "ERROR"] | None
    business_status: Literal["NORMAL", "ADVERTENCIA", "CRITICO", "SIN_BASE"] | None
    technical_status: Literal["RUNNING", "WAITING_REVIEW", "RESUMING", "COMPLETED", "ERROR"]
    approval_status: Literal["NOT_REQUIRED", "PENDING", "APPROVED", "REJECTED"]
    producto: str | None = None
    variacion: float | None = Field(default=None, allow_inf_nan=False)
    recomendacion: str | None = None
    agentes: list[str] = Field(default_factory=list)
    request: AnalysisRequest
    policy: dict
    steps: list[dict]
    dataset_id: str
    simulated_authorization: bool
    replayed: bool = False
    error: str | None = None


class ExecutionPage(BaseModel):
    items: list[ExecutionResponse]
    total: int
    page: int
    page_size: int
