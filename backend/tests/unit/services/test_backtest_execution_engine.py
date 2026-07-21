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
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyDecision,
)
from app.services.backtest_execution_engine import (
    BacktestExecutionEngine,
)
BASE_TIME = datetime(
    2026,
    6,
    1,
    0,
    0,
    tzinfo=UTC,
)
class SequenceStrategyRunner:
    def __init__(
        self,
        actions,
    ):
        self.actions = list(actions)
        self.calls = []
    def validate_bot(
        self,
        bot,
    ):
        return dict(
            bot.strategy_config or {}
        )
    async def run(
        self,
        *,
        bot,
        ticker,
    ):
        self.calls.append(
            ticker.last_price
        )
        action = self.actions.pop(0)
        evaluated_at = (
            datetime.fromtimestamp(
                ticker.observed_at_ms
                / 1000,
                tz=UTC,
            )
        )
        return TradingBotStrategyDecision(
            action=action,
            confidence=0.8,
            reason=(
                f"Backtest {action} signal"
            ),
            reference_price=(
                ticker.last_price
            ),
            evaluated_at=evaluated_at,
        )
def build_bot(
    *,
    risk_percent=10,
    max_position=250,
):
    return SimpleNamespace(
        id=10,
        user_id=7,
        strategy_type="RULE_BASED",
        strategy_config={},
        symbol="BTCUSDT",
        category="linear",
        timeframe="1d",
        risk_per_trade_percent=(
            risk_percent
        ),
        max_position_value_usd=(
            max_position
        ),
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
def build_request(
    prices,
    *,
    force_close=True,
    minimum_notional=1,
):
    return TradingBotBacktestRequest(
        initial_balance_usd=1000,
        fee_rate=0.0006,
        slippage_rate=0.0001,
        minimum_order_notional_usd=(
            minimum_notional
        ),
        force_close_at_end=(
            force_close
        ),
        candles=build_candles(
            prices
        ),
    )
@pytest.mark.asyncio
async def test_warmup_frame_is_not_evaluated():
    runner = SequenceStrategyRunner([
        "HOLD",
        "HOLD",
    ])
    engine = BacktestExecutionEngine(
        strategy_runner_factory=(
            lambda evaluated_at: runner
        )
    )
    result = await engine.run(
        bot=build_bot(),
        data=build_request([
            100,
            101,
            102,
        ]),
    )
    assert result.frames_processed == 3
    assert result.warmup_frame_count == 1
    assert result.evaluated_frame_count == 2
    assert len(runner.calls) == 2
    assert (
        result.steps[0].outcomes
        == ["WARMUP"]
    )
    assert result.order_count == 0
@pytest.mark.asyncio
async def test_buy_opens_and_increases_long():
    runner = SequenceStrategyRunner([
        "BUY",
        "BUY",
        "HOLD",
    ])
    engine = BacktestExecutionEngine(
        strategy_runner_factory=(
            lambda evaluated_at: runner
        )
    )
    result = await engine.run(
        bot=build_bot(),
        data=build_request(
            [
                100,
                101,
                103,
                105,
            ],
            force_close=False,
        ),
    )
    assert result.order_count == 2
    assert (
        result.orders[0]
        .position_effect
        == "OPEN"
    )
    assert (
        result.orders[1]
        .position_effect
        == "INCREASE"
    )
    position = (
        result
        .final_portfolio
        .open_position
    )
    assert position is not None
    assert position.side == "LONG"
    assert (
        position.quantity
        > result.orders[0].quantity
    )
    assert (
        position.average_entry_price
        > result.orders[0].fill_price
    )
@pytest.mark.asyncio
async def test_opposite_signal_closes_long():
    runner = SequenceStrategyRunner([
        "BUY",
        "SELL",
    ])
    engine = BacktestExecutionEngine(
        strategy_runner_factory=(
            lambda evaluated_at: runner
        )
    )
    result = await engine.run(
        bot=build_bot(),
        data=build_request([
            100,
            100,
            110,
        ]),
    )
    assert result.order_count == 2
    assert result.completed_trade_count == 1
    assert (
        result.orders[-1]
        .position_effect
        == "CLOSE"
    )
    assert (
        result.orders[-1]
        .realized_pnl_usd
        > 0
    )
    trade = result.completed_trades[0]
    assert trade.side == "LONG"
    assert (
        trade.net_realized_pnl_usd
        < trade.gross_realized_pnl_usd
    )
    assert (
        result.final_portfolio
        .open_position
        is None
    )
@pytest.mark.asyncio
async def test_sell_opens_and_buy_closes_short():
    runner = SequenceStrategyRunner([
        "SELL",
        "BUY",
    ])
    engine = BacktestExecutionEngine(
        strategy_runner_factory=(
            lambda evaluated_at: runner
        )
    )
    result = await engine.run(
        bot=build_bot(),
        data=build_request([
            110,
            110,
            100,
        ]),
    )
    assert result.completed_trade_count == 1
    trade = result.completed_trades[0]
    assert trade.side == "SHORT"
    assert trade.gross_realized_pnl_usd > 0
    assert (
        result.orders[0].side
        == "SELL"
    )
    assert (
        result.orders[-1].side
        == "BUY"
    )
@pytest.mark.asyncio
async def test_force_close_at_end():
    runner = SequenceStrategyRunner([
        "BUY",
        "HOLD",
    ])
    engine = BacktestExecutionEngine(
        strategy_runner_factory=(
            lambda evaluated_at: runner
        )
    )
    result = await engine.run(
        bot=build_bot(),
        data=build_request([
            100,
            100,
            105,
        ]),
    )
    assert result.completed_trade_count == 1
    assert result.orders[-1].forced is True
    assert (
        result.completed_trades[0]
        .forced_exit
        is True
    )
    assert (
        "FORCED_CLOSED"
        in result.steps[-1].outcomes
    )
    assert (
        result.final_portfolio
        .open_position
        is None
    )
@pytest.mark.asyncio
async def test_minimum_notional_rejects_trade():
    runner = SequenceStrategyRunner([
        "BUY",
    ])
    engine = BacktestExecutionEngine(
        strategy_runner_factory=(
            lambda evaluated_at: runner
        )
    )
    result = await engine.run(
        bot=build_bot(
            risk_percent=0.01,
            max_position=0.50,
        ),
        data=build_request(
            [
                100,
                100,
            ],
            minimum_notional=1,
        ),
    )
    assert result.order_count == 0
    assert (
        result.steps[-1].outcomes
        == ["REJECTED"]
    )
    assert (
        result.final_portfolio
        .equity_usd
        == pytest.approx(1000)
    )
@pytest.mark.asyncio
async def test_backtest_execution_is_deterministic():
    async def execute_once():
        runner = SequenceStrategyRunner([
            "BUY",
            "HOLD",
            "SELL",
        ])
        engine = BacktestExecutionEngine(
            strategy_runner_factory=(
                lambda evaluated_at:
                runner
            )
        )
        return await engine.run(
            bot=build_bot(),
            data=build_request([
                100,
                100,
                105,
                110,
            ]),
        )
    first = await execute_once()
    second = await execute_once()
    assert (
        first.model_dump(
            mode="json"
        )
        == second.model_dump(
            mode="json"
        )
    )
