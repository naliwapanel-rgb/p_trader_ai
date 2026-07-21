from datetime import (
    UTC,
    datetime,
    timedelta,
)
from types import (
    SimpleNamespace,
)
import pytest
from app.schemas.trading_bot_backtest import (
    HistoricalMarketCandle,
    TradingBotBacktestRequest,
)
from app.services.backtest_execution_engine import (
    BacktestExecutionEngine,
)
BASE_TIME = datetime(
    2026,
    6,
    1,
    tzinfo=UTC,
)
def build_candles(
    prices,
):
    candles = []
    for index, price in enumerate(
        prices
    ):
        opened_at = (
            BASE_TIME
            + timedelta(days=index)
        )
        candles.append(
            HistoricalMarketCandle(
                opened_at=opened_at,
                closed_at=(
                    opened_at
                    + timedelta(days=1)
                ),
                open_price=price,
                high_price=price + 2,
                low_price=max(
                    price - 2,
                    0.01,
                ),
                close_price=price,
                volume=100,
                turnover_usd=(
                    price * 100
                ),
            )
        )
    return candles
def build_request():
    return TradingBotBacktestRequest(
        initial_balance_usd=1000,
        fee_rate=0.0006,
        slippage_rate=0.0001,
        minimum_order_notional_usd=1,
        force_close_at_end=True,
        candles=build_candles([
            100,
            100,
            97,
            104,
        ]),
    )
def build_bot(
    *,
    strategy_type,
    strategy_config,
):
    return SimpleNamespace(
        id=10,
        user_id=7,
        strategy_type=strategy_type,
        strategy_config=(
            strategy_config
        ),
        symbol="BTCUSDT",
        category="linear",
        timeframe="1d",
        risk_per_trade_percent=20,
        max_position_value_usd=1000,
    )
def evaluated_actions(
    result,
):
    return [
        step.decision.action
        for step in result.steps
        if step.decision is not None
    ]
@pytest.mark.asyncio
async def test_dca_backtest_uses_position_state():
    bot = build_bot(
        strategy_type="DCA",
        strategy_config={
            "direction": "LONG",
            "entry_spacing_percent": 2,
            "maximum_entries": 3,
            "take_profit_percent": 3,
        },
    )
    result = await (
        BacktestExecutionEngine()
        .run(
            bot=bot,
            data=build_request(),
        )
    )
    assert evaluated_actions(result) == [
        "BUY",
        "BUY",
        "SELL",
    ]
    assert [
        order.position_effect
        for order in result.orders
    ] == [
        "OPEN",
        "INCREASE",
        "CLOSE",
    ]
    assert result.completed_trade_count == 1
    assert (
        result.final_portfolio
        .open_position
        is None
    )
@pytest.mark.asyncio
async def test_grid_backtest_uses_position_state():
    bot = build_bot(
        strategy_type="GRID",
        strategy_config={
            "direction": "LONG",
            "lower_price": 90,
            "upper_price": 110,
            "grid_levels": 11,
            "maximum_entries": 3,
            "take_profit_percent": 2,
        },
    )
    result = await (
        BacktestExecutionEngine()
        .run(
            bot=bot,
            data=build_request(),
        )
    )
    assert evaluated_actions(result) == [
        "BUY",
        "BUY",
        "SELL",
    ]
    assert [
        order.position_effect
        for order in result.orders
    ] == [
        "OPEN",
        "INCREASE",
        "CLOSE",
    ]
    assert result.completed_trade_count == 1
    assert (
        result.final_portfolio
        .open_position
        is None
    )
