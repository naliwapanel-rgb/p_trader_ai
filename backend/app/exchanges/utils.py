from typing import Any


def to_float(value: Any, default: float = 0.0) -> float:
    """
    Convert exchange numeric strings safely.

    Exchange APIs commonly return numbers as strings and may occasionally
    return null or empty strings.
    """
    if value is None or value == "":
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default