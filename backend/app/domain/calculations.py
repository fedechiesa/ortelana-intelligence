from decimal import Decimal


def variation(base: Decimal | None, current: Decimal | None) -> Decimal | None:
    if base is None or current is None or base == 0:
        return None
    return (current - base) / base * 100


def classify(value: Decimal | None, warning: float = -10, critical: float = -20) -> str:
    if value is None:
        return "SIN_BASE"
    if value <= Decimal(str(critical)):
        return "CRITICO"
    if value <= Decimal(str(warning)):
        return "ADVERTENCIA"
    return "NORMAL"
