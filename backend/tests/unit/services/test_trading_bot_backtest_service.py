from datetime import (
    UTC,
    datetime,
    timedelta,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
)
import pytest
from fastapi import (
    HTTPException,
)
from app.schemas.trading_bot_backtest import (
    BacktestExecutionStep,
    BacktestPortfolioSnapshot,
    HistoricalMarketCandle,
    TradingBotBacktestExecutionResult,
    TradingBotBacktestRequest,
)
from app.services.backtest_performance_service import (
    BacktestPerformanceService,
)
from app.services.trading_bot_backtest_service import (
    TradingBotBacktestService,
)
BASE_TIME = datetime(
    2026,
    6,
    1,
    tzinfo=UTC,
)
def build_request():
    candles = []
    for index, price in enumerate([
        100,
        105,
    ]):
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
                low_price=price - 2,
                close_price=price,
                volume=100,
                turnover_usd=(
                    price * 100
                ),
            )
        )
    return TradingBotBacktestRequest(
        candles=candles
    )
def build_portfolio():
    return BacktestPortfolioSnapshot(
        initial_balance_usd=10000,
        cash_balance_usd=10000,
        reserved_balance_usd=0,
        equity_usd=10000,
        realized_pnl_usd=0,
        unrealized_pnl_usd=0,
        total_fees_usd=0,
        open_position=None,
    )
def build_execution():
    portfolio = build_portfolio()
    steps = [
        BacktestExecutionStep(
            sequence=1,
            candle_closed_at=(
                BASE_TIME
                + timedelta(days=1)
            ),
            warmup_complete=False,
            decision=None,
            outcomes=["WARMUP"],
            orders=[],
            portfolio=portfolio,
        ),
        BacktestExecutionStep(
            sequence=2,
            candle_closed_at=(
                BASE_TIME
                + timedelta(days=2)
            ),
            warmup_complete=True,
            decision=None,
            outcomes=["NO_ACTION"],
            orders=[],
            portfolio=portfolio,
        ),
    ]
    return (
        TradingBotBacktestExecutionResult(
            bot_id=10,
            symbol="BTCUSDT",
            category="linear",
            timeframe="1d",
            started_at=BASE_TIME,
            ended_at=(
                BASE_TIME
                + timedelta(days=2)
            ),
            frames_processed=2,
            warmup_frame_count=1,
            evaluated_frame_count=1,
            order_count=0,
            completed_trade_count=0,
            orders=[],
            completed_trades=[],
            steps=steps,
            final_portfolio=portfolio,
        )
    )
@pytest.mark.asyncio
async def test_backtest_is_user_and_bot_scoped():
    db = MagicMock()
    current_user = SimpleNamespace(
        id=7
    )
    bot = SimpleNamespace(
        id=10,
        user_id=7,
    )
    bot_service = MagicMock()
    bot_service.get_bot.return_value = (
        bot
    )
    execution = build_execution()
    engine = MagicMock()
    engine.run = AsyncMock(
        return_value=execution
    )
    expected = (
        BacktestPerformanceService
        .analyze(execution)
    )
    performance_service = MagicMock()
    performance_service.analyze.return_value = (
        expected
    )
    service = TradingBotBacktestService(
        db,
        bot_service=bot_service,
        execution_engine=engine,
        performance_service=(
            performance_service
        ),
    )
    data = build_request()
    result = await service.run_backtest(
        current_user=current_user,
        bot_id=10,
        data=data,
    )
    assert result == expected
    bot_service.get_bot.assert_called_once_with(
        current_user=current_user,
        bot_id=10,
    )
    engine.run.assert_awaited_once_with(
        bot=bot,
        data=data,
    )
    performance_service.analyze.assert_called_once_with(
        execution
    )
    db.commit.assert_not_called()
@pytest.mark.asyncio
async def test_missing_bot_error_is_preserved():
    bot_service = MagicMock()
    bot_service.get_bot.side_effect = (
        HTTPException(
            status_code=404,
            detail="Trading bot not found",
        )
    )
    engine = MagicMock()
    engine.run = AsyncMock()
    service = TradingBotBacktestService(
        MagicMock(),
        bot_service=bot_service,
        execution_engine=engine,
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        await service.run_backtest(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=999,
            data=build_request(),
        )
    assert error.value.status_code == 404
    engine.run.assert_not_awaited()
@pytest.mark.asyncio
async def test_execution_failure_is_preserved():
    db = MagicMock()
    bot_service = MagicMock()
    bot_service.get_bot.return_value = (
        SimpleNamespace(
            id=10,
            user_id=7,
        )
    )
    engine = MagicMock()
    engine.run = AsyncMock(
        side_effect=ValueError(
            "Invalid historical data"
        )
    )
    service = TradingBotBacktestService(
        db,
        bot_service=bot_service,
        execution_engine=engine,
    )
    with pytest.raises(
        ValueError,
        match="Invalid historical data",
    ):
        await service.run_backtest(
            current_user=(
                SimpleNamespace(id=7)
            ),
            bot_id=10,
            data=build_request(),
        )
    db.commit.assert_not_called()
    db.rollback.assert_not_called()
