import pytest
from pydantic import ValidationError
from app.schemas.risk_management import (
    RiskConfiguration,
    RiskConfigurationUpdate,
)
from app.services.risk_management_service import (
    RiskManagementService,
)
def test_service_uses_default_configuration():
    service = RiskManagementService()
    config = service.get_configuration()
    assert config.max_risk_per_trade_percent == 1.0
    assert config.max_leverage == 10.0
    assert config.max_open_positions == 5
def test_service_accepts_custom_configuration():
    service = RiskManagementService(
        RiskConfiguration(
            max_leverage=20,
            max_open_positions=8,
        )
    )
    config = service.get_configuration()
    assert config.max_leverage == 20
    assert config.max_open_positions == 8
def test_service_updates_configuration():
    service = RiskManagementService()
    result = service.update_configuration(
        RiskConfigurationUpdate(
            max_leverage=5,
            max_open_positions=3,
        )
    )
    assert result.max_leverage == 5
    assert result.max_open_positions == 3
    assert result.max_daily_loss_percent == 5.0
def test_service_revalidates_combined_configuration():
    service = RiskManagementService()
    with pytest.raises(
        ValidationError,
        match=(
            "max_risk_per_trade_percent cannot exceed "
            "max_daily_loss_percent"
        ),
    ):
        service.update_configuration(
            RiskConfigurationUpdate(
                max_risk_per_trade_percent=6,
            )
        )
def test_service_restores_defaults():
    service = RiskManagementService(
        RiskConfiguration(
            max_leverage=25,
        )
    )
    result = service.restore_defaults()
    assert result.max_leverage == 10.0
    assert result.max_open_positions == 5
def test_validate_leverage_passes():
    service = RiskManagementService()
    check = service.validate_leverage(5)
    assert check.rule == "MAX_LEVERAGE"
    assert check.passed is True
    assert check.actual_value == 5
    assert check.limit_value == 10.0
def test_validate_leverage_fails():
    service = RiskManagementService()
    check = service.validate_leverage(15)
    assert check.passed is False
    assert "exceeds" in check.message
def test_validate_open_positions_passes():
    service = RiskManagementService()
    check = service.validate_open_positions(4)
    assert check.passed is True
def test_validate_open_positions_fails_at_limit():
    service = RiskManagementService()
    check = service.validate_open_positions(5)
    assert check.passed is False
def test_validate_risk_reward_passes():
    service = RiskManagementService()
    check = service.validate_risk_reward(2.0)
    assert check.passed is True
def test_validate_risk_reward_fails():
    service = RiskManagementService()
    check = service.validate_risk_reward(1.0)
    assert check.passed is False
def test_build_validation_result_accepts_all_checks():
    service = RiskManagementService()
    result = service.build_validation_result(
        [
            service.validate_leverage(5),
            service.validate_open_positions(2),
            service.validate_risk_reward(2),
        ]
    )
    assert result.accepted is True
    assert result.rejection_reasons == []
    assert len(result.checks) == 3
def test_build_validation_result_collects_failures():
    service = RiskManagementService()
    result = service.build_validation_result(
        [
            service.validate_leverage(20),
            service.validate_open_positions(5),
            service.validate_risk_reward(1),
        ]
    )
    assert result.accepted is False
    assert len(result.rejection_reasons) == 3
