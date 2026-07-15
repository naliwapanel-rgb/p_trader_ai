from decimal import Decimal

from app.exchanges.decimal_utils import (
    decimal_to_plain_string,
    is_step_aligned,
    round_down_to_step,
    to_decimal,
)


def test_to_decimal_preserves_precision():
    assert to_decimal("0.001") == Decimal("0.001")
    assert to_decimal(0.001) == Decimal("0.001")


def test_is_step_aligned():
    assert is_step_aligned(
        Decimal("0.003"),
        Decimal("0.001"),
    )

    assert not is_step_aligned(
        Decimal("0.0035"),
        Decimal("0.001"),
    )


def test_round_down_to_step():
    assert round_down_to_step(
        Decimal("0.0039"),
        Decimal("0.001"),
    ) == Decimal("0.003")


def test_decimal_to_plain_string():
    assert decimal_to_plain_string(
        Decimal("0.001")
    ) == "0.001"

    assert decimal_to_plain_string(
        Decimal("10000.0")
    ) == "10000.0"