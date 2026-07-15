from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Any


def to_decimal(
    value: Any,
    default: Decimal = Decimal("0"),
) -> Decimal:
    if value is None or value == "":
        return default

    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def is_step_aligned(
    value: Decimal,
    step: Decimal,
) -> bool:
    if step <= 0:
        return True

    return value % step == 0


def round_down_to_step(
    value: Decimal,
    step: Decimal,
) -> Decimal:
    if step <= 0:
        return value

    units = (value / step).to_integral_value(
        rounding=ROUND_DOWN
    )

    return units * step


def decimal_to_plain_string(value: Decimal) -> str:
    """
    Convert Decimal to a non-scientific string suitable for exchange APIs.
    """
    return format(value, "f")