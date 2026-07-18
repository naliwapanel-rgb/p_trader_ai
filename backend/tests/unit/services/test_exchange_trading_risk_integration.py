from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException
from app.schemas.exchange_trade import (
    LimitOrderRequest,
    MarketOrderRequest,
)
from app.schemas.order_risk import OrderRiskContext
from app.schemas.risk_management import (
    RiskConfigurationUpdate,
)
from app.services.exchange_trading_service import (
    ExchangeTradingService,
)
from app.services.risk_management_registry import (
    _risk_management_services,
    get_user_risk_management_service,
)
@pytest.fixture(autouse=True)
def clear_risk_registry():
    _risk_management_services.clear()
    yield
    _risk_management_services.clear()
def build_risk_context(
    *,
    leverage: float = 5,
    daily_loss: float = 0,
    drawdown: float = 0,
    estimated_entry_price: float | None = 100,
) -> OrderRiskContext:
    return OrderRiskContext(
        account_equity=10000,
        requested_leverage=leverage,
        estimated_entry_price=(
            estimated_entry_price
        ),
        stop_loss_price=95,
        take_profit_price=110,
        current_open_positions=0,
        current_total_exposure_percent=10,
        current_daily_loss_percent=daily_loss,
        current_drawdown_percent=drawdown,
    )
def build_service():
    service = ExchangeTradingService(
        db=MagicMock()
    )
    service.settings = SimpleNamespace(
        max_order_quantity=1000,
        max_order_value_usd=1000000,
        exchange_dry_run=True,
        exchange_trading_enabled=False,
    )
    client = SimpleNamespace(
        place_market_order=AsyncMock(
            return_value={
                "exchange": "BYBIT",
                "symbol": "BTCUSDT",
                "order_type": "MARKET",
                "dry_run": True,
                "accepted": False,
            }
        ),
        place_limit_order=AsyncMock(
            return_value={
                "exchange": "BYBIT",
                "symbol": "BTCUSDT",
                "order_type": "LIMIT",
                "dry_run": True,
                "accepted": False,
            }
        ),
    )
    service._get_client = MagicMock(
        return_value=client
    )
    return service, client
@pytest.mark.asyncio
async def test_opening_market_order_requires_risk_context():
    service, client = build_service()
    request = MarketOrderRequest(
        symbol="btcusdt",
        side="BUY",
        quantity=20,
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.place_market_order(
            current_user=SimpleNamespace(id=1),
            account_id=1,
            data=request,
        )
    assert exc_info.value.status_code == 400
    assert "risk_context" in str(
        exc_info.value.detail
    )
    client.place_market_order.assert_not_awaited()
@pytest.mark.asyncio
async def test_safe_market_order_passes_risk_validation():
    service, client = build_service()
    request = MarketOrderRequest(
        symbol="btcusdt",
        side="BUY",
        quantity=20,
        risk_context=build_risk_context(),
    )
    result = await service.place_market_order(
        current_user=SimpleNamespace(id=1),
        account_id=1,
        data=request,
    )
    validation = result["risk_validation"]
    assert validation["accepted"] is True
    assert validation["risk_reward_ratio"] == 2
    assert (
        validation[
            "projected_total_exposure_percent"
        ]
        == 30
    )
    client.place_market_order.assert_awaited_once()
@pytest.mark.asyncio
async def test_daily_loss_rejects_market_order():
    service, client = build_service()
    request = MarketOrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=20,
        risk_context=build_risk_context(
            daily_loss=6
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.place_market_order(
            current_user=SimpleNamespace(id=1),
            account_id=1,
            data=request,
        )
    detail = exc_info.value.detail
    validation = detail["risk_validation"]
    failed_rules = {
        check["rule"]
        for check in validation["checks"]
        if not check["passed"]
    }
    assert validation["accepted"] is False
    assert "MAX_DAILY_LOSS" in failed_rules
    client.place_market_order.assert_not_awaited()
@pytest.mark.asyncio
async def test_user_risk_configuration_controls_orders():
    service, client = build_service()
    risk_service = (
        get_user_risk_management_service(7)
    )
    risk_service.update_configuration(
        RiskConfigurationUpdate(
            max_leverage=2
        )
    )
    request = MarketOrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=20,
        risk_context=build_risk_context(
            leverage=5
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.place_market_order(
            current_user=SimpleNamespace(id=7),
            account_id=1,
            data=request,
        )
    validation = (
        exc_info.value.detail[
            "risk_validation"
        ]
    )
    failed_rules = {
        check["rule"]
        for check in validation["checks"]
        if not check["passed"]
    }
    assert "MAX_LEVERAGE" in failed_rules
    client.place_market_order.assert_not_awaited()
@pytest.mark.asyncio
async def test_trading_disabled_rejects_order():
    service, client = build_service()
    risk_service = (
        get_user_risk_management_service(9)
    )
    risk_service.update_configuration(
        RiskConfigurationUpdate(
            trading_enabled=False
        )
    )
    request = MarketOrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        quantity=20,
        risk_context=build_risk_context(),
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.place_market_order(
            current_user=SimpleNamespace(id=9),
            account_id=1,
            data=request,
        )
    validation = (
        exc_info.value.detail[
            "risk_validation"
        ]
    )
    failed_rules = {
        check["rule"]
        for check in validation["checks"]
        if not check["passed"]
    }
    assert "TRADING_ENABLED" in failed_rules
    client.place_market_order.assert_not_awaited()
@pytest.mark.asyncio
async def test_safe_limit_order_uses_limit_price():
    service, client = build_service()
    request = LimitOrderRequest(
        symbol="btcusdt",
        side="BUY",
        quantity=20,
        price=100,
        risk_context=build_risk_context(
            estimated_entry_price=None
        ),
    )
    result = await service.place_limit_order(
        current_user=SimpleNamespace(id=1),
        account_id=1,
        data=request,
    )
    validation = result["risk_validation"]
    assert validation["accepted"] is True
    assert validation["risk_reward_ratio"] == 2
    client.place_limit_order.assert_awaited_once()
@pytest.mark.asyncio
async def test_reduce_only_order_bypasses_opening_risk():
    service, client = build_service()
    request = MarketOrderRequest(
        symbol="BTCUSDT",
        side="SELL",
        quantity=1,
        reduce_only=True,
    )
    result = await service.place_market_order(
        current_user=SimpleNamespace(id=1),
        account_id=1,
        data=request,
    )
    assert "risk_validation" not in result
    client.place_market_order.assert_awaited_once()
