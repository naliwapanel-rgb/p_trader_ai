import asyncio
from types import SimpleNamespace
import pytest
from app.api.v1.endpoints.risk_management import (
    _risk_management_services,
    calculate_position_size,
    get_risk_configuration,
    get_risk_management_service,
    reset_risk_configuration,
    update_risk_configuration,
    validate_pre_trade_risk,
)
from app.main import app
from app.schemas.risk_management import (
    PositionSizeRequest,
    PreTradeRiskRequest,
    RiskConfiguration,
    RiskConfigurationUpdate,
)
from app.services.risk_management_service import (
    PositionSizeCalculator,
    RiskManagementService,
)
@pytest.fixture(autouse=True)
def clear_risk_management_services():
    _risk_management_services.clear()
    yield
    _risk_management_services.clear()
def build_position_size_request(
    *,
    risk_percent: float = 1.0,
    leverage: float = 5.0,
) -> PositionSizeRequest:
    return PositionSizeRequest(
        account_equity=10000,
        risk_percent=risk_percent,
        entry_price=100,
        stop_loss_price=95,
        quantity_step=0.001,
        minimum_quantity=0.001,
        maximum_quantity=1000,
        minimum_notional=5,
        leverage=leverage,
    )
def build_position_size_result():
    return PositionSizeCalculator.calculate(
        build_position_size_request()
    )
def build_pre_trade_request(
    *,
    current_daily_loss_percent: float = 0,
    current_drawdown_percent: float = 0,
) -> PreTradeRiskRequest:
    return PreTradeRiskRequest(
        side="BUY",
        account_equity=10000,
        requested_leverage=5,
        current_open_positions=0,
        current_total_exposure_percent=10,
        current_daily_loss_percent=(
            current_daily_loss_percent
        ),
        current_drawdown_percent=(
            current_drawdown_percent
        ),
        entry_price=100,
        stop_loss_price=95,
        take_profit_price=110,
        position_size=build_position_size_result(),
    )
def test_risk_management_routes_are_registered():
    paths = app.openapi()["paths"]
    expected_routes = {
        "/api/v1/risk-management/configuration",
        (
            "/api/v1/risk-management/"
            "configuration/reset"
        ),
        "/api/v1/risk-management/position-size",
        (
            "/api/v1/risk-management/"
            "pre-trade-validation"
        ),
    }
    assert expected_routes.issubset(paths)
def test_risk_configuration_route_supports_get_and_put():
    operations = app.openapi()["paths"][
        "/api/v1/risk-management/configuration"
    ]
    assert "get" in operations
    assert "put" in operations
def test_risk_management_routes_require_authentication():
    paths = app.openapi()["paths"]
    risk_paths = {
        path: operations
        for path, operations in paths.items()
        if "/risk-management/" in path
    }
    assert risk_paths
    for operations in risk_paths.values():
        for operation in operations.values():
            assert operation.get("security")
def test_user_receives_reusable_risk_service():
    user = SimpleNamespace(id=1)
    first_service = get_risk_management_service(
        current_user=user
    )
    second_service = get_risk_management_service(
        current_user=user
    )
    assert first_service is second_service
def test_users_receive_separate_risk_services():
    first_user = SimpleNamespace(id=1)
    second_user = SimpleNamespace(id=2)
    first_service = get_risk_management_service(
        current_user=first_user
    )
    second_service = get_risk_management_service(
        current_user=second_user
    )
    first_service.update_configuration(
        RiskConfigurationUpdate(
            max_risk_per_trade_percent=2,
        )
    )
    assert first_service is not second_service
    assert (
        first_service
        .get_configuration()
        .max_risk_per_trade_percent
        == 2
    )
    assert (
        second_service
        .get_configuration()
        .max_risk_per_trade_percent
        == RiskConfiguration()
        .max_risk_per_trade_percent
    )
def test_get_risk_configuration_endpoint():
    service = RiskManagementService()
    response = asyncio.run(
        get_risk_configuration(service=service)
    )
    assert response["success"] is True
    assert response["message"] == (
        "Risk configuration retrieved successfully"
    )
    assert (
        response["data"].max_risk_per_trade_percent
        == 1
    )
    assert response["data"].trading_enabled is True
def test_update_risk_configuration_endpoint():
    service = RiskManagementService()
    response = asyncio.run(
        update_risk_configuration(
            data=RiskConfigurationUpdate(
                max_risk_per_trade_percent=2,
                max_daily_loss_percent=6,
                max_drawdown_percent=25,
                max_leverage=15,
            ),
            service=service,
        )
    )
    configuration = response["data"]
    assert response["success"] is True
    assert configuration.max_risk_per_trade_percent == 2
    assert configuration.max_daily_loss_percent == 6
    assert configuration.max_drawdown_percent == 25
    assert configuration.max_leverage == 15
def test_reset_risk_configuration_endpoint():
    service = RiskManagementService(
        configuration=RiskConfiguration(
            max_risk_per_trade_percent=2,
            max_daily_loss_percent=10,
            max_drawdown_percent=30,
            max_leverage=20,
        )
    )
    response = asyncio.run(
        reset_risk_configuration(service=service)
    )
    defaults = RiskConfiguration()
    configuration = response["data"]
    assert response["success"] is True
    assert (
        configuration.max_risk_per_trade_percent
        == defaults.max_risk_per_trade_percent
    )
    assert (
        configuration.max_daily_loss_percent
        == defaults.max_daily_loss_percent
    )
    assert (
        configuration.max_drawdown_percent
        == defaults.max_drawdown_percent
    )
    assert (
        configuration.max_leverage
        == defaults.max_leverage
    )
def test_position_size_endpoint_applies_risk_limits():
    service = RiskManagementService()
    response = asyncio.run(
        calculate_position_size(
            data=build_position_size_request(
                risk_percent=5,
                leverage=25,
            ),
            service=service,
        )
    )
    result = response["data"]
    assert response["success"] is True
    assert result.valid is True
    assert result.requested_risk_percent == pytest.approx(
        1
    )
    assert result.leverage == pytest.approx(10)
    assert result.requested_risk_amount == pytest.approx(
        100
    )
    assert result.rounded_quantity == pytest.approx(
        20
    )
    assert result.position_notional == pytest.approx(
        2000
    )
    assert result.required_margin == pytest.approx(
        200
    )
def test_pre_trade_validation_endpoint_accepts_safe_trade():
    service = RiskManagementService()
    response = asyncio.run(
        validate_pre_trade_risk(
            data=build_pre_trade_request(),
            service=service,
        )
    )
    result = response["data"]
    assert response["success"] is True
    assert result.accepted is True
    assert result.rejection_reasons == []
    assert result.risk_reward_ratio == pytest.approx(2)
    assert result.projected_total_exposure_percent == (
        pytest.approx(30)
    )
def test_pre_trade_endpoint_rejects_account_loss_limits():
    service = RiskManagementService()
    response = asyncio.run(
        validate_pre_trade_risk(
            data=build_pre_trade_request(
                current_daily_loss_percent=6,
                current_drawdown_percent=21,
            ),
            service=service,
        )
    )
    result = response["data"]
    failed_rules = {
        check.rule
        for check in result.checks
        if not check.passed
    }
    assert response["success"] is True
    assert result.accepted is False
    assert "MAX_DAILY_LOSS" in failed_rules
    assert "MAX_DRAWDOWN" in failed_rules
    assert len(result.rejection_reasons) == 2
