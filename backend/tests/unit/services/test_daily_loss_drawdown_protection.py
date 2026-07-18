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
        "current_daily_loss_percent": 0,
        "current_drawdown_percent": 0,
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
def test_daily_loss_passes_below_limit():
    service = RiskManagementService()
    check = service.validate_daily_loss(4)
    assert check.rule == "MAX_DAILY_LOSS"
    assert check.passed is True
    assert check.actual_value == 4
    assert check.limit_value == 5
def test_daily_loss_passes_at_limit():
    service = RiskManagementService()
    check = service.validate_daily_loss(5)
    assert check.passed is True
def test_daily_loss_fails_above_limit():
    service = RiskManagementService()
    check = service.validate_daily_loss(5.01)
    assert check.passed is False
    assert "exceeds" in check.message
def test_drawdown_passes_below_limit():
    service = RiskManagementService()
    check = service.validate_drawdown(15)
    assert check.rule == "MAX_DRAWDOWN"
    assert check.passed is True
    assert check.actual_value == 15
    assert check.limit_value == 20
def test_drawdown_passes_at_limit():
    service = RiskManagementService()
    check = service.validate_drawdown(20)
    assert check.passed is True
def test_drawdown_fails_above_limit():
    service = RiskManagementService()
    check = service.validate_drawdown(20.01)
    assert check.passed is False
    assert "exceeds" in check.message
def test_pre_trade_rejects_daily_loss_limit():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            current_daily_loss_percent=6,
        )
    )
    assert result.accepted is False
    check = get_check(
        result,
        "MAX_DAILY_LOSS",
    )
    assert check.passed is False
    assert check.actual_value == 6
def test_pre_trade_rejects_drawdown_limit():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            current_drawdown_percent=25,
        )
    )
    assert result.accepted is False
    check = get_check(
        result,
        "MAX_DRAWDOWN",
    )
    assert check.passed is False
    assert check.actual_value == 25
def test_pre_trade_rejects_both_protection_limits():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            current_daily_loss_percent=6,
            current_drawdown_percent=25,
        )
    )
    assert result.accepted is False
    assert len(result.rejection_reasons) == 2
    assert "2 risk checks" in result.summary
def test_result_exposes_account_risk_metrics():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            current_daily_loss_percent=2.5,
            current_drawdown_percent=8,
        )
    )
    assert result.accepted is True
    assert result.current_daily_loss_percent == 2.5
    assert result.current_drawdown_percent == 8
def test_warns_near_daily_loss_limit():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            current_daily_loss_percent=4.5,
        )
    )
    assert result.accepted is True
    assert any(
        "Daily loss is within 10 percent"
        in warning
        for warning in result.warnings
    )
def test_warns_near_drawdown_limit():
    service = RiskManagementService()
    result = service.validate_pre_trade(
        build_request(
            current_drawdown_percent=18,
        )
    )
    assert result.accepted is True
    assert any(
        "Account drawdown is within 10 percent"
        in warning
        for warning in result.warnings
    )
def test_custom_daily_loss_configuration():
    service = RiskManagementService(
        RiskConfiguration(
            max_daily_loss_percent=3,
        )
    )
    result = service.validate_pre_trade(
        build_request(
            current_daily_loss_percent=3.1,
        )
    )
    assert result.accepted is False
    check = get_check(
        result,
        "MAX_DAILY_LOSS",
    )
    assert check.limit_value == 3
def test_custom_drawdown_configuration():
    service = RiskManagementService(
        RiskConfiguration(
            max_drawdown_percent=10,
        )
    )
    result = service.validate_pre_trade(
        build_request(
            current_drawdown_percent=10.1,
        )
    )
    assert result.accepted is False
    check = get_check(
        result,
        "MAX_DRAWDOWN",
    )
    assert check.limit_value == 10
@pytest.mark.parametrize(
    "field",
    [
        "current_daily_loss_percent",
        "current_drawdown_percent",
    ],
)
def test_rejects_negative_account_risk_metrics(field):
    with pytest.raises(ValidationError):
        build_request(
            **{field: -0.01}
        )
