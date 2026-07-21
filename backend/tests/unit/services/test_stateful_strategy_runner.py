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
    TradingBotStrategyDecision,
    TradingBotStrategyState,
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
    18,
    0,
    tzinfo=UTC,
)
class CaptureStateStrategy:
    strategy_type = "STATEFUL"
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
                "State captured for test"
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
        strategy_type="STATEFUL",
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
        spread=0,
        spread_percent=0,
        volume_24h=1000,
        turnover_24h=100000,
        observed_at_ms=1,
    )
def build_runner(
    strategy,
):
    return TradingBotStrategyRunner(
        registry=(
            TradingBotStrategyRegistry([
                strategy
            ])
        ),
        clock=lambda: NOW,
    )
@pytest.mark.asyncio
async def test_runner_supplies_empty_state():
    strategy = CaptureStateStrategy()
    runner = build_runner(strategy)
    decision = await runner.run(
        bot=build_bot(),
        ticker=build_ticker(),
    )
    assert decision.action == "HOLD"
    assert (
        strategy.context.state
        == TradingBotStrategyState()
    )
@pytest.mark.asyncio
async def test_runner_forwards_supplied_state():
    strategy = CaptureStateStrategy()
    runner = build_runner(strategy)
    state = TradingBotStrategyState(
        order_count=3,
        completed_trade_count=1,
        last_order_action="SELL",
        last_order_reference_price=105,
        last_order_at=NOW,
    )
    await runner.run(
        bot=build_bot(),
        ticker=build_ticker(),
        state=state,
    )
    assert (
        strategy.context.state
        == state
    )
