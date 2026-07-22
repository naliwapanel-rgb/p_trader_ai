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
            + timedelta(minutes=index)
        )
        candles.append(
            HistoricalMarketCandle(
                opened_at=opened_at,
                closed_at=(
                    opened_at
                    + timedelta(minutes=1)
                ),
                open_price=price,
                high_price=price + 0.5,
                low_price=max(
                    price - 0.5,
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
):
    return TradingBotBacktestRequest(
        initial_balance_usd=1000,
        fee_rate=0.0006,
        slippage_rate=0.0001,
        minimum_order_notional_usd=1,
        force_close_at_end=True,
        candles=build_candles(
            prices
        ),
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
        timeframe="1m",
        risk_per_trade_percent=20,
        max_position_value_usd=1000,
    )
class HistoryCaptureRunner:
    def __init__(self):
        self.calls = []
    def validate_bot(
        self,
        bot,
    ):
        return {}
    async def run(
        self,
        *,
        bot,
        ticker,
        market_history,
        state,
    ):
        self.calls.append({
            "ticker": ticker.last_price,
            "history": [
                sample.close_price
                for sample
                in market_history
            ],
            "state": state,
        })
        return TradingBotStrategyDecision(
            action="HOLD",
            confidence=0,
            reason="History captured",
            reference_price=(
                ticker.last_price
            ),
            evaluated_at=(
                market_history[
                    -1
                ].observed_at
            ),
        )
def position_effects(
    result,
):
    return [
        order.position_effect
        for order in result.orders
    ]
@pytest.mark.asyncio
async def test_backtest_history_has_no_lookahead():
    runner = HistoryCaptureRunner()
    engine = BacktestExecutionEngine(
        strategy_runner_factory=(
            lambda evaluated_at:
            runner
        )
    )
    await engine.run(
        bot=build_bot(
            strategy_type="TREND",
            strategy_config={},
        ),
        data=build_request([
            100,
            101,
            102,
            103,
        ]),
    )
    assert [
        call["history"]
        for call in runner.calls
    ] == [
        [100, 101],
        [100, 101, 102],
        [100, 101, 102, 103],
    ]
    assert all(
        call["history"][-1]
        == call["ticker"]
        for call in runner.calls
    )
@pytest.mark.asyncio
async def test_trend_backtest_uses_history_and_state():
    bot = build_bot(
        strategy_type="TREND",
        strategy_config={
            "fast_ema_period": 2,
            "slow_ema_period": 4,
            "momentum_lookback": 2,
            "minimum_momentum_percent": 0.1,
            (
                "minimum_ema_"
                "separation_percent"
            ): 0.01,
        },
    )
    result = await (
        BacktestExecutionEngine()
        .run(
            bot=bot,
            data=build_request([
                100,
                101,
                102,
                104,
                106,
            ]),
        )
    )
    assert position_effects(
        result
    ) == [
        "OPEN",
        "CLOSE",
    ]
    assert (
        result.orders[-1].forced
        is True
    )
@pytest.mark.asyncio
async def test_mean_reversion_backtest_cycle():
    bot = build_bot(
        strategy_type="MEAN_REVERSION",
        strategy_config={
            "lookback_period": 5,
            "rsi_period": 3,
            "entry_z_score": 1,
            "exit_z_score": 0.75,
            "oversold_rsi": 35,
            "overbought_rsi": 65,
        },
    )
    result = await (
        BacktestExecutionEngine()
        .run(
            bot=bot,
            data=build_request([
                100,
                100,
                100,
                100,
                90,
                100,
            ]),
        )
    )
    assert position_effects(
        result
    ) == [
        "OPEN",
        "CLOSE",
    ]
    assert (
        result.completed_trade_count
        == 1
    )
@pytest.mark.asyncio
async def test_scalping_backtest_cycle():
    bot = build_bot(
        strategy_type="SCALPING",
        strategy_config={
            "fast_ema_period": 2,
            "slow_ema_period": 4,
            "rsi_period": 3,
            "atr_period": 3,
            "momentum_lookback": 2,
            "minimum_momentum_percent": 0.1,
            "exit_momentum_percent": 0.05,
            "long_rsi_minimum": 50,
            "long_rsi_maximum": 100,
            "short_rsi_minimum": 0,
            "short_rsi_maximum": 50,
            "minimum_atr_percent": 0.01,
            "maximum_atr_percent": 5,
        },
    )
    result = await (
        BacktestExecutionEngine()
        .run(
            bot=bot,
            data=build_request([
                100,
                101,
                102,
                103,
                104,
                100,
            ]),
        )
    )
    assert position_effects(
        result
    ) == [
        "OPEN",
        "CLOSE",
    ]
    assert (
        result.completed_trade_count
        == 1
    )
