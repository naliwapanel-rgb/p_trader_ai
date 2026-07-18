import pytest
from pydantic import ValidationError
from app.schemas.risk_management import (
    RiskConfiguration,
    RiskConfigurationUpdate,
)
def test_default_risk_configuration():
    config = RiskConfiguration()
    assert config.max_risk_per_trade_percent == 1.0
    assert config.max_daily_loss_percent == 5.0
    assert config.max_drawdown_percent == 20.0
    assert config.max_leverage == 10.0
    assert config.max_open_positions == 5
    assert config.max_total_exposure_percent == 100.0
    assert config.minimum_risk_reward_ratio == 1.5
    assert config.trading_enabled is True
@pytest.mark.parametrize(
    "field,value",
    [
        ("max_risk_per_trade_percent", 0),
        ("max_daily_loss_percent", 0),
        ("max_drawdown_percent", 0),
        ("max_leverage", 0),
        ("max_open_positions", 0),
        ("max_total_exposure_percent", 0),
        ("minimum_risk_reward_ratio", 0),
    ],
)
def test_risk_configuration_rejects_non_positive_values(
    field,
    value,
):
    data = {}
    data[field] = value
    with pytest.raises(ValidationError):
        RiskConfiguration(**data)
def test_risk_per_trade_cannot_exceed_daily_loss():
    with pytest.raises(
        ValidationError,
        match=(
            "max_risk_per_trade_percent cannot exceed "
            "max_daily_loss_percent"
        ),
    ):
        RiskConfiguration(
            max_risk_per_trade_percent=6,
            max_daily_loss_percent=5,
        )
def test_daily_loss_cannot_exceed_drawdown():
    with pytest.raises(
        ValidationError,
        match=(
            "max_daily_loss_percent cannot exceed "
            "max_drawdown_percent"
        ),
    ):
        RiskConfiguration(
            max_daily_loss_percent=25,
            max_drawdown_percent=20,
        )
def test_risk_configuration_update_requires_value():
    with pytest.raises(
        ValidationError,
        match=(
            "At least one risk configuration field "
            "must be provided"
        ),
    ):
        RiskConfigurationUpdate()
def test_risk_configuration_update_accepts_partial_data():
    update = RiskConfigurationUpdate(
        max_leverage=5,
    )
    assert update.max_leverage == 5
    assert update.max_open_positions is None
