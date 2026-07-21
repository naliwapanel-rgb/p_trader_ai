import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.trading_bot import (
    TradingBotCreateRequest,
    TradingBotUpdateRequest,
)
def test_create_request_normalizes_values():
    request = TradingBotCreateRequest(
        name="  BTC Momentum Bot  ",
        description="  Test bot  ",
        exchange_account_id=3,
        strategy_type="MOMENTUM",
        symbol=" btcusdt ",
        category="linear",
        timeframe="5m",
        strategy_config={
            "period": 14,
        },
    )
    assert request.name == (
        "BTC Momentum Bot"
    )
    assert request.description == (
        "Test bot"
    )
    assert request.symbol == "BTCUSDT"
    assert request.paper_trading is True
    assert request.dry_run is True
def test_create_request_rejects_timeframe():
    with pytest.raises(
        ValidationError
    ):
        TradingBotCreateRequest(
            name="Bad Timeframe Bot",
            symbol="BTCUSDT",
            timeframe="7m",
        )
def test_create_request_rejects_live_execution():
    with pytest.raises(
        ValidationError,
        match=(
            "paper_trading or "
            "dry_run"
        ),
    ):
        TradingBotCreateRequest(
            name="Unsafe Bot",
            symbol="BTCUSDT",
            paper_trading=False,
            dry_run=False,
        )
def test_create_request_validates_risk_hierarchy():
    with pytest.raises(
        ValidationError,
        match=(
            "risk_per_trade_percent"
        ),
    ):
        TradingBotCreateRequest(
            name="Risk Bot",
            symbol="BTCUSDT",
            risk_per_trade_percent=5,
            max_daily_loss_percent=3,
            max_drawdown_percent=10,
        )
    with pytest.raises(
        ValidationError,
        match=(
            "max_daily_loss_percent"
        ),
    ):
        TradingBotCreateRequest(
            name="Drawdown Bot",
            symbol="BTCUSDT",
            risk_per_trade_percent=1,
            max_daily_loss_percent=12,
            max_drawdown_percent=10,
        )
def test_update_request_requires_value():
    with pytest.raises(
        ValidationError,
        match=(
            "At least one trading bot"
        ),
    ):
        TradingBotUpdateRequest()
