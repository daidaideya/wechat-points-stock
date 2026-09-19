"""Money normalization shared by API schemas and persistence boundaries."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Optional


MONEY_DECIMAL_PLACES = 2
MONEY_QUANTUM = Decimal("0.01")


def normalize_cash_amount(
    value: Any,
    field_name: str = "cash",
    *,
    default: Optional[float] = None,
) -> Optional[float]:
    """Return a finite, non-negative yuan amount rounded to cents.

    API callers may still send numbers or numeric strings for compatibility.
    Decimal is constructed from the textual representation so values such as
    ``1.005`` follow the documented half-up rule instead of binary-float
    rounding.  Storage remains compatible with the current SQLite REAL columns;
    this function only closes the write/query boundary for new values.
    """
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number")

    text = str(value).strip()
    if not text:
        return default
    try:
        amount = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} is not a valid number: {value!r}") from exc

    if not amount.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if amount < 0:
        raise ValueError(f"{field_name} must be non-negative")

    try:
        normalized = amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} is outside the supported precision range") from exc
    return float(normalized)
