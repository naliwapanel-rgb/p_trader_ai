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
from app.schemas.trading_bot_strategy import (
    TradingBotMarketSample,
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
    21,
    20,
    0,
    tzinfo=UTC,
)
class CaptureHistoryStrategy:
    strategy_type = "HISTORY_TEST"
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
            reason="Market history captured",
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
        strategy_type="HISTORY_TEST",
        strategy_config={},
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
    )
def build_ticker():
    return MarketTickerSnapshot(
        exchange="BACKTEST",
        category="linear",
        symbol="BTCUSDT",
        last_price=100,
        bid_price=100,
        ask_price=100,
        observed_at_ms=int(
            NOW.timestamp() * 1000
        ),
    )
def build_sample():
    return TradingBotMarketSample(
        observed_at=NOW,
        open_price=100,
        high_price=101,
        low_price=99,
        close_price=100,
        source="CANDLE",
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
async def test_runner_defaults_empty_history():
    strategy = CaptureHistoryStrategy()
    await build_runner(
        strategy
    ).run(
        bot=build_bot(),
        ticker=build_ticker(),
    )
    assert (
        strategy.context
        .market_history
        == []
    )
@pytest.mark.asyncio
async def test_runner_forwards_market_history():
    strategy = CaptureHistoryStrategy()
    history = [
        build_sample()
    ]
    await build_runner(
        strategy
    ).run(
        bot=build_bot(),
        ticker=build_ticker(),
        market_history=history,
    )
    assert (
        strategy.context
        .market_history
        == history
    )
