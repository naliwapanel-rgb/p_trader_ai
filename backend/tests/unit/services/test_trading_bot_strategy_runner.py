from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
import pytest
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.services.trading_bot_strategy_runner import (
    TradingBotStrategyRunner,
)
from app.strategies.registry import (
    TradingBotStrategyRegistry,
)
from app.strategies.rule_based import (
    RuleBasedTradingStrategy,
)
NOW = datetime(
    2026,
    7,
    21,
    15,
    0,
    tzinfo=UTC,
)
def build_bot(
    *,
    strategy_type: str = "RULE_BASED",
):
    return SimpleNamespace(
        id=10,
        user_id=7,
        strategy_type=strategy_type,
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        strategy_config={
            "buy_change_percent_24h": 2,
            "sell_change_percent_24h": -2,
        },
    )
def build_ticker():
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="linear",
        symbol="BTCUSDT",
        last_price=60000,
        bid_price=59999,
        ask_price=60001,
        spread=2,
        spread_percent=0.003333,
        price_change_percent_24h=3,
        volume_24h=100,
        turnover_24h=6000000,
        observed_at_ms=123456789,
    )
def test_default_registry_contains_rule_based():
    registry = (
        TradingBotStrategyRegistry
        .default()
    )
    assert registry.list_types() == [
        "RULE_BASED"
    ]
def test_duplicate_strategy_is_rejected():
    registry = TradingBotStrategyRegistry(
        strategies=[
            RuleBasedTradingStrategy(),
        ]
    )
    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        registry.register(
            RuleBasedTradingStrategy()
        )
def test_unknown_strategy_is_rejected():
    registry = (
        TradingBotStrategyRegistry
        .default()
    )
    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        registry.get("MOMENTUM")
def test_runner_validates_configuration():
    runner = TradingBotStrategyRunner(
        clock=lambda: NOW
    )
    config = runner.validate_bot(
        build_bot()
    )
    assert (
        config[
            "buy_change_percent_24h"
        ]
        == 2
    )
@pytest.mark.asyncio
async def test_runner_returns_strategy_decision():
    runner = TradingBotStrategyRunner(
        clock=lambda: NOW
    )
    decision = await runner.run(
        bot=build_bot(),
        ticker=build_ticker(),
    )
    assert decision.action == "BUY"
    assert decision.evaluated_at == NOW
