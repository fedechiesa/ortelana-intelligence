"""Import-safe validation of the legacy Spanish result schema."""

from app.schemas.contracts import LegacyResult


def normalizar_resultado(resultado: dict) -> dict:
    return LegacyResult.model_validate(resultado).model_dump()
