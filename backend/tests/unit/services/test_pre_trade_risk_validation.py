import pytest
from pydantic import ValidationError
from app.schemas.risk_management import (
    PositionSizeResult,
    PreTradeRiskRequest,
    RiskConfiguration,
)
from app.services.risk_management_service import (
    RiskManagementService,
)
def build_position_size(**overrides):
    values = {
        "valid": True,
        "account_equity": 1000,
        "requested_risk_percent": 1,
        "requested_risk_amount": 10,
        "entry_price": 100,
        "stop_loss_price": 95,
        "stop_distance": 5,
        "raw_quantity": 2,
        "rounded_quantity": 2,
        "position_notional": 200,
        "required_margin": 20,
        "actual_risk_amount": 10,
        "actual_risk_percent": 1,
        "quantity_step": 0.01,
        "minimum_quantity": 0.01,
        "maximum_quantity": 100,
        "minimum_notional": 5,
        "leverage": 10,
        "capped_by_maximum_quantity": False,
        "rejection_reasons": [],
    }
    values.update(overrides)
    return PositionSizeResult(**values)
def build_request(**overrides):
    values = {
        "side": "BUY",
        "account_equity": 1000,
        "requested_leverage": 5,
        "current_open_positions": 2,
        "current_total_exposure_percent": 20,
        "entry_price": 100,
        "stop_loss_price": 95,
        "take_profit_price": 110,
        "position_size": build_position_size(),
    }
    values.update(overrides)
    return PreTradeRiskRequest(**values)
def get_check(result, rule):
    return next(
        check
        for check in result.checks
        if check.rule == rule
    )
def test_accepts_valid_buy_trade():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request()
    )
    assert result.accepted is True
    assert result.risk_reward_ratio == 2
    assert result.projected_total_exposure_percent == 40
    assert result.rejection_reasons == []
    assert len(result.checks) == 9
    assert "passed" in result.summary.lower()
def test_accepts_valid_sell_trade():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            side="SELL",
            stop_loss_price=105,
            take_profit_price=90,
        )
    )
    assert result.accepted is True
    assert result.side == "SELL"
    assert result.risk_reward_ratio == 2
def test_rejects_when_trading_disabled():
    service = RiskManagementService(
        RiskConfiguration(
            trading_enabled=False,
        )
    )
    result = service.validate_pre_trade(
        build_request()
    )
    assert result.accepted is False
    check = get_check(
        result,
        "TRADING_ENABLED",
    )
    assert check.passed is False
def test_rejects_invalid_position_size():
    service = RiskManagementService()
    position_size = build_position_size(
        valid=False,
        rounded_quantity=0,
        position_notional=0,
        actual_risk_amount=0,
        actual_risk_percent=0,
        rejection_reasons=[
            "Calculated quantity is zero",
        ],
    )
    result = service.validate_pre_trade(
        build_request(
            position_size=position_size,
        )
    )
    assert result.accepted is False
    check = get_check(
        result,
        "POSITION_SIZE_VALID",
    )
    assert check.passed is False
    assert "Calculated quantity is zero" in (
        check.message
    )
def test_rejects_risk_above_configured_limit():
    service = RiskManagementService()
    position_size = build_position_size(
        actual_risk_percent=2,
        actual_risk_amount=20,
    )
    result = service.validate_pre_trade(
        build_request(
            position_size=position_size,
        )
    )
    assert result.accepted is False
    check = get_check(
        result,
        "MAX_RISK_PER_TRADE",
    )
    assert check.passed is False
    assert check.actual_value == 2
    assert check.limit_value == 1
def test_rejects_excessive_leverage():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            requested_leverage=20,
        )
    )
    assert result.accepted is False
    check = get_check(
        result,
        "MAX_LEVERAGE",
    )
    assert check.passed is False
def test_rejects_open_position_limit():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            current_open_positions=5,
        )
    )
    assert result.accepted is False
    check = get_check(
        result,
        "MAX_OPEN_POSITIONS",
    )
    assert check.passed is False
def test_rejects_projected_exposure_limit():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            current_total_exposure_percent=90,
        )
    )
    assert result.accepted is False
    assert result.projected_total_exposure_percent == 110
    check = get_check(
        result,
        "MAX_TOTAL_EXPOSURE",
    )
    assert check.passed is False
def test_rejects_low_risk_reward():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            take_profit_price=105,
        )
    )
    assert result.accepted is False
    assert result.risk_reward_ratio == 1
    check = get_check(
        result,
        "MINIMUM_RISK_REWARD",
    )
    assert check.passed is False
def test_warns_near_exposure_limit():
    service = RiskManagementService()
    position_size = build_position_size(
        position_notional=100,
    )
    result = service.validate_pre_trade(
        build_request(
            current_total_exposure_percent=80,
            position_size=position_size,
        )
    )
    assert result.accepted is True
    assert result.projected_total_exposure_percent == 90
    assert len(result.warnings) == 1
    assert "within 10 percent" in result.warnings[0]
def test_warns_when_quantity_is_capped():
    service = RiskManagementService()
    position_size = build_position_size(
        capped_by_maximum_quantity=True,
    )
    result = service.validate_pre_trade(
        build_request(
            position_size=position_size,
        )
    )
    assert result.accepted is True
    assert any(
        "capped" in warning
        for warning in result.warnings
    )
def test_collects_multiple_rejections():
    service = RiskManagementService()
    position_size = build_position_size(
        actual_risk_percent=2,
        actual_risk_amount=20,
    )
    result = service.validate_pre_trade(
        build_request(
            requested_leverage=20,
            current_open_positions=5,
            current_total_exposure_percent=90,
            take_profit_price=105,
            position_size=position_size,
        )
    )
    assert result.accepted is False
    assert len(result.rejection_reasons) == 5
    assert "5 risk checks" in result.summary
def test_buy_rejects_stop_above_entry():
    with pytest.raises(
        ValidationError,
        match=(
            "BUY stop_loss_price must be below "
            "entry_price"
        ),
    ):
        build_request(
            stop_loss_price=101,
        )
def test_buy_rejects_take_profit_below_entry():
    with pytest.raises(
        ValidationError,
        match=(
            "BUY take_profit_price must be above "
            "entry_price"
        ),
    ):
        build_request(
            take_profit_price=99,
        )
def test_sell_rejects_stop_below_entry():
    with pytest.raises(
        ValidationError,
        match=(
            "SELL stop_loss_price must be above "
            "entry_price"
        ),
    ):
        build_request(
            side="SELL",
            stop_loss_price=99,
            take_profit_price=90,
        )
def test_sell_rejects_take_profit_above_entry():
    with pytest.raises(
        ValidationError,
        match=(
            "SELL take_profit_price must be below "
            "entry_price"
        ),
    ):
        build_request(
            side="SELL",
            stop_loss_price=105,
            take_profit_price=101,
        )
@pytest.mark.parametrize(
    "side",
    [
        "buy",
        "sell",
        "LONG",
        "SHORT",
    ],
)
def test_rejects_invalid_side_values(side):
    with pytest.raises(ValidationError):
        build_request(side=side)
