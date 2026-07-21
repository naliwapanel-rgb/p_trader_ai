from datetime import (
    UTC,
    datetime,
)
import pytest
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyContext,
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
def build_context(
    *,
    change: float = 0,
    spread: float = 0.01,
    turnover: float = 1000000,
    last_price: float = 60000,
    config: dict | None = None,
):
    ticker = MarketTickerSnapshot(
        exchange="BYBIT",
        category="linear",
        symbol="BTCUSDT",
        last_price=last_price,
        bid_price=59999,
        ask_price=60001,
        spread=2,
        spread_percent=spread,
        price_change_percent_24h=change,
        volume_24h=100,
        turnover_24h=turnover,
        observed_at_ms=123456789,
    )
    return TradingBotStrategyContext(
        bot_id=10,
        user_id=7,
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        config=config or {},
        ticker=ticker,
        evaluated_at=NOW,
    )
@pytest.mark.asyncio
async def test_rule_based_buy():
    decision = await (
        RuleBasedTradingStrategy()
        .evaluate(
            build_context(
                change=2.5
            )
        )
    )
    assert decision.action == "BUY"
    assert decision.reference_price == 60000
    assert decision.confidence == 0.5
@pytest.mark.asyncio
async def test_rule_based_sell():
    decision = await (
        RuleBasedTradingStrategy()
        .evaluate(
            build_context(
                change=-3
            )
        )
    )
    assert decision.action == "SELL"
    assert decision.confidence == 0.6
@pytest.mark.asyncio
async def test_rule_based_hold_between_thresholds():
    decision = await (
        RuleBasedTradingStrategy()
        .evaluate(
            build_context(
                change=0.25
            )
        )
    )
    assert decision.action == "HOLD"
@pytest.mark.asyncio
async def test_rule_based_holds_wide_spread():
    decision = await (
        RuleBasedTradingStrategy()
        .evaluate(
            build_context(
                change=5,
                spread=1,
            )
        )
    )
    assert decision.action == "HOLD"
    assert "spread" in decision.reason.lower()
@pytest.mark.asyncio
async def test_rule_based_holds_low_turnover():
    decision = await (
        RuleBasedTradingStrategy()
        .evaluate(
            build_context(
                change=5,
                turnover=100,
                config={
                    "minimum_turnover_24h": 1000,
                },
            )
        )
    )
    assert decision.action == "HOLD"
    assert "turnover" in decision.reason.lower()
@pytest.mark.asyncio
async def test_rule_based_holds_invalid_price():
    decision = await (
        RuleBasedTradingStrategy()
        .evaluate(
            build_context(
                change=5,
                last_price=0,
            )
        )
    )
    assert decision.action == "HOLD"
