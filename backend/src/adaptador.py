"""Import-safe compatibility with the two original TP2 contract tests."""

from app.schemas.contracts import LegacyResult


def normalizar_resultado(resultado: dict) -> dict:
    return LegacyResult.model_validate(resultado).model_dump()
