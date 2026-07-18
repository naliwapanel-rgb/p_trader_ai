import pytest
from pydantic import ValidationError
from app.schemas.risk_management import (
    PositionSizeRequest,
)
from app.services.risk_management_service import (
    PositionSizeCalculator,
)
def build_request(**overrides):
    data = {
        "account_equity": 1000,
        "risk_percent": 1,
        "entry_price": 100,
        "stop_loss_price": 95,
        "quantity_step": 0.01,
        "minimum_quantity": 0.01,
        "maximum_quantity": 100,
        "minimum_notional": 5,
        "leverage": 10,
    }
    data.update(overrides)
    return PositionSizeRequest(**data)
def test_calculates_position_size():
    result = PositionSizeCalculator.calculate(
        build_request()
    )
    assert result.valid is True
    assert result.requested_risk_amount == 10
    assert result.stop_distance == 5
    assert result.raw_quantity == 2
    assert result.rounded_quantity == 2
    assert result.position_notional == 200
    assert result.required_margin == 20
    assert result.actual_risk_amount == 10
    assert result.actual_risk_percent == 1
def test_supports_short_position():
    result = PositionSizeCalculator.calculate(
        build_request(
            entry_price=100,
            stop_loss_price=105,
        )
    )
    assert result.valid is True
    assert result.stop_distance == 5
    assert result.rounded_quantity == 2
def test_rounds_quantity_down_to_step():
    result = PositionSizeCalculator.calculate(
        build_request(
            entry_price=100,
            stop_loss_price=97,
            quantity_step=0.1,
        )
    )
    assert result.raw_quantity == pytest.approx(
        3.3333333333333335
    )
    assert result.rounded_quantity == 3.3
    assert result.actual_risk_amount == pytest.approx(
        9.9
    )
    assert result.actual_risk_percent == pytest.approx(
        0.99
    )
def test_caps_quantity_at_maximum():
    result = PositionSizeCalculator.calculate(
        build_request(
            account_equity=100000,
            risk_percent=10,
            entry_price=100,
            stop_loss_price=99,
            maximum_quantity=50,
        )
    )
    assert result.valid is True
    assert result.rounded_quantity == 50
    assert result.capped_by_maximum_quantity is True
    assert result.actual_risk_amount == 50
def test_rejects_quantity_below_minimum():
    result = PositionSizeCalculator.calculate(
        build_request(
            account_equity=100,
            risk_percent=0.1,
            entry_price=100,
            stop_loss_price=90,
            minimum_quantity=0.1,
            quantity_step=0.01,
        )
    )
    assert result.valid is False
    assert result.rounded_quantity == 0.01
    assert any(
        "below the instrument minimum quantity"
        in reason
        for reason in result.rejection_reasons
    )
def test_rejects_zero_after_rounding():
    result = PositionSizeCalculator.calculate(
        build_request(
            account_equity=10,
            risk_percent=0.1,
            entry_price=100,
            stop_loss_price=90,
            quantity_step=1,
            minimum_quantity=1,
        )
    )
    assert result.valid is False
    assert result.rounded_quantity == 0
    assert any(
        "zero after quantity-step rounding"
        in reason
        for reason in result.rejection_reasons
    )
def test_rejects_below_minimum_notional():
    result = PositionSizeCalculator.calculate(
        build_request(
            account_equity=100,
            risk_percent=1,
            entry_price=10,
            stop_loss_price=9,
            minimum_notional=20,
        )
    )
    assert result.valid is False
    assert result.position_notional == 10
    assert any(
        "below the instrument minimum notional"
        in reason
        for reason in result.rejection_reasons
    )
def test_applies_leverage_to_required_margin():
    result = PositionSizeCalculator.calculate(
        build_request(
            leverage=5,
        )
    )
    assert result.position_notional == 200
    assert result.required_margin == 40
def test_rejects_equal_entry_and_stop():
    with pytest.raises(
        ValidationError,
        match=(
            "entry_price and stop_loss_price "
            "cannot be equal"
        ),
    ):
        build_request(
            entry_price=100,
            stop_loss_price=100,
        )
def test_rejects_minimum_above_maximum():
    with pytest.raises(
        ValidationError,
        match=(
            "minimum_quantity cannot exceed "
            "maximum_quantity"
        ),
    ):
        build_request(
            minimum_quantity=10,
            maximum_quantity=1,
        )
@pytest.mark.parametrize(
    "field,value",
    [
        ("account_equity", 0),
        ("risk_percent", 0),
        ("entry_price", 0),
        ("stop_loss_price", 0),
        ("quantity_step", 0),
        ("minimum_quantity", 0),
        ("maximum_quantity", 0),
        ("leverage", 0),
    ],
)
def test_rejects_non_positive_values(
    field,
    value,
):
    with pytest.raises(ValidationError):
        build_request(**{field: value})
