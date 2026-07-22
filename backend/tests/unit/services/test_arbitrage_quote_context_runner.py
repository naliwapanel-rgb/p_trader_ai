from datetime import (
    UTC,
    datetime,
)
from decimal import (
    Decimal,
)
from types import (
    SimpleNamespace,
)
import pytest
from app.schemas.arbitrage import (
    ArbitrageMarketQuote,
)
from app.schemas.market_scanner import (
    MarketTickerSnapshot,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyDecision,
)
from app.services.trading_bot_strategy_runner import (
    TradingBotStrategyRunner,
)
from app.strategies.registry import (
    TradingBotStrategyRegistry,
)
NOW = datetime(
    2026,
    7,
    22,
    9,
    30,
    tzinfo=UTC,
)
class CaptureArbitrageContextStrategy:
    strategy_type = (
        "ARBITRAGE_CONTEXT_TEST"
    )
    def __init__(self):
        self.context = None
    def validate_config(
        self,
        config,
    ):
        return dict(config)
    async def evaluate(
        self,
        context,
    ):
        self.context = context
        return TradingBotStrategyDecision(
            action="HOLD",
            confidence=0,
            reason=(
                "Arbitrage quote context "
                "captured"
            ),
            reference_price=(
                context.ticker.last_price
            ),
            evaluated_at=(
                context.evaluated_at
            ),
        )
def build_bot():
    return SimpleNamespace(
        id=10,
        user_id=7,
        strategy_type=(
            "ARBITRAGE_CONTEXT_TEST"
        ),
        strategy_config={},
        symbol="BTCUSDT",
        category="spot",
        timeframe="1m",
    )
def build_ticker():
    return MarketTickerSnapshot(
        exchange="BYBIT",
        category="spot",
        symbol="BTCUSDT",
        last_price=100,
        bid_price=99,
        bid_size=10,
        ask_price=100,
        ask_size=10,
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def build_quote():
    return ArbitrageMarketQuote(
        exchange="BYBIT",
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        bid_price=Decimal("99"),
        ask_price=Decimal("100"),
        bid_size=Decimal("10"),
        ask_size=Decimal("10"),
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def build_runner(
    strategy,
):
    return TradingBotStrategyRunner(
        registry=(
            TradingBotStrategyRegistry([
                strategy,
            ])
        ),
        clock=lambda: NOW,
    )
@pytest.mark.asyncio
async def test_runner_defaults_empty_quotes():
    strategy = (
        CaptureArbitrageContextStrategy()
    )
    await build_runner(
        strategy
    ).run(
        bot=build_bot(),
        ticker=build_ticker(),
    )
    assert (
        strategy.context
        .arbitrage_quotes
        == []
    )
@pytest.mark.asyncio
async def test_runner_forwards_arbitrage_quotes():
    strategy = (
        CaptureArbitrageContextStrategy()
    )
    quotes = [
        build_quote()
    ]
    await build_runner(
        strategy
    ).run(
        bot=build_bot(),
        ticker=build_ticker(),
        arbitrage_quotes=quotes,
    )
    assert (
        strategy.context
        .arbitrage_quotes
        == quotes
    )
