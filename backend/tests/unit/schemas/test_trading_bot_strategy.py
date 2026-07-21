from datetime import (
    UTC,
    datetime,
)
import pytest
from pydantic import (
    ValidationError,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    RuleBasedStrategyConfig,
    TradingBotStrategyContext,
    TradingBotStrategyDecision,
)
NOW = datetime(
    2026,
    7,
    21,
    15,
    0,
    tzinfo=UTC,
)
def build_ticker(
    *,
    symbol: str = "BTCUSDT",
):
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="linear",
        symbol=symbol,
        last_price=60000,
        bid_price=59999,
        ask_price=60001,
        spread=2,
        spread_percent=0.003333,
        price_change_percent_24h=2,
        volume_24h=100,
        turnover_24h=6000000,
        observed_at_ms=123456789,
    )
def test_rule_config_defaults():
    config = RuleBasedStrategyConfig()
    assert (
        config.buy_change_percent_24h
        == 1
    )
    assert (
        config.sell_change_percent_24h
        == -1
    )
def test_rule_config_rejects_bad_thresholds():
    with pytest.raises(
        ValidationError,
        match="must be below",
    ):
        RuleBasedStrategyConfig(
            buy_change_percent_24h=-2,
            sell_change_percent_24h=1,
        )
def test_rule_config_rejects_unknown_fields():
    with pytest.raises(
        ValidationError,
    ):
        RuleBasedStrategyConfig(
            unsupported_rule=True
        )
def test_context_requires_matching_symbol():
    with pytest.raises(
        ValidationError,
        match="Ticker symbol",
    ):
        TradingBotStrategyContext(
            bot_id=10,
            user_id=7,
            strategy_type="RULE_BASED",
            symbol="ETHUSDT",
            category="linear",
            timeframe="5m",
            config={},
            ticker=build_ticker(),
            evaluated_at=NOW,
        )
def test_decision_validates_confidence():
    with pytest.raises(
        ValidationError,
    ):
        TradingBotStrategyDecision(
            action="BUY",
            confidence=1.5,
            reason="Invalid confidence",
            reference_price=60000,
            evaluated_at=NOW,
        )
