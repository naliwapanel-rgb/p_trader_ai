from datetime import (
    UTC,
    datetime,
    timedelta,
)
import pytest
from app.schemas.trading_bot_backtest import (
    BacktestCompletedTrade,
    BacktestExecutionStep,
    BacktestPortfolioSnapshot,
    TradingBotBacktestExecutionResult,
)
from app.services.backtest_performance_service import (
    BacktestPerformanceService,
)
BASE_TIME = datetime(
    2026,
    6,
    1,
    0,
    0,
    tzinfo=UTC,
)
def portfolio(
    *,
    equity: float,
    fees: float = 4.0,
    unrealized: float = 0.0,
):
    return BacktestPortfolioSnapshot(
        initial_balance_usd=1000,
        cash_balance_usd=equity,
        reserved_balance_usd=0,
        equity_usd=equity,
        realized_pnl_usd=8,
        unrealized_pnl_usd=unrealized,
        total_fees_usd=fees,
        open_position=None,
    )
def step(
    *,
    sequence: int,
    equity: float,
):
    return BacktestExecutionStep(
        sequence=sequence,
        candle_closed_at=(
            BASE_TIME
            + timedelta(days=sequence)
        ),
        warmup_complete=(
            sequence > 1
        ),
        decision=None,
        outcomes=[
            (
                "WARMUP"
                if sequence == 1
                else "NO_ACTION"
            )
        ],
        orders=[],
        portfolio=portfolio(
            equity=equity
        ),
    )
def trade(
    *,
    side: str,
    gross_pnl: float,
    fees: float,
    net_pnl: float,
    forced: bool = False,
):
    return BacktestCompletedTrade(
        side=side,
        opened_at=BASE_TIME,
        closed_at=(
            BASE_TIME
            + timedelta(days=1)
        ),
        quantity=1,
        average_entry_price=100,
        exit_price=110,
        gross_realized_pnl_usd=(
            gross_pnl
        ),
        total_fees_usd=fees,
        net_realized_pnl_usd=(
            net_pnl
        ),
        forced_exit=forced,
    )
def execution_with_metrics():
    trades = [
        trade(
            side="LONG",
            gross_pnl=12,
            fees=2,
            net_pnl=10,
        ),
        trade(
            side="SHORT",
            gross_pnl=-5,
            fees=1,
            net_pnl=-6,
        ),
        trade(
            side="LONG",
            gross_pnl=1,
            fees=1,
            net_pnl=0,
            forced=True,
        ),
    ]
    steps = [
        step(
            sequence=1,
            equity=1000,
        ),
        step(
            sequence=2,
            equity=1015,
        ),
        step(
            sequence=3,
            equity=990,
        ),
        step(
            sequence=4,
            equity=1010,
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
                + timedelta(days=4)
            ),
            frames_processed=4,
            warmup_frame_count=1,
            evaluated_frame_count=3,
            order_count=6,
            completed_trade_count=3,
            orders=[],
            completed_trades=trades,
            steps=steps,
            final_portfolio=portfolio(
                equity=1010
            ),
        )
    )
def test_equity_curve_tracks_peak_and_drawdown():
    result = (
        BacktestPerformanceService
        .analyze(
            execution_with_metrics()
        )
    )
    curve = result.equity_curve
    assert len(curve) == 5
    assert curve[0].sequence == 0
    assert curve[0].equity_usd == 1000
    assert curve[2].equity_usd == 1015
    assert curve[2].peak_equity_usd == 1015
    assert curve[3].equity_usd == 990
    assert curve[3].drawdown_usd == 25
    assert (
        curve[3].drawdown_percent
        == pytest.approx(
            25 / 1015 * 100
        )
    )
def test_performance_calculates_trade_metrics():
    result = (
        BacktestPerformanceService
        .analyze(
            execution_with_metrics()
        )
    )
    metrics = result.performance
    assert metrics.order_count == 6
    assert metrics.completed_trade_count == 3
    assert metrics.winning_trade_count == 1
    assert metrics.losing_trade_count == 1
    assert metrics.breakeven_trade_count == 1
    assert metrics.forced_exit_count == 1
    assert (
        metrics.gross_profit_usd
        == pytest.approx(10)
    )
    assert (
        metrics.gross_loss_usd
        == pytest.approx(6)
    )
    assert (
        metrics.net_realized_pnl_usd
        == pytest.approx(4)
    )
    assert (
        metrics.win_rate_percent
        == pytest.approx(
            100 / 3
        )
    )
    assert (
        metrics.average_win_usd
        == pytest.approx(10)
    )
    assert (
        metrics.average_loss_usd
        == pytest.approx(-6)
    )
    assert (
        metrics.profit_factor
        == pytest.approx(
            10 / 6
        )
    )
def test_performance_calculates_return_and_drawdown():
    result = (
        BacktestPerformanceService
        .analyze(
            execution_with_metrics()
        )
    )
    metrics = result.performance
    assert metrics.initial_balance_usd == 1000
    assert metrics.final_equity_usd == 1010
    assert (
        metrics.total_net_pnl_usd
        == pytest.approx(10)
    )
    assert (
        metrics.return_percent
        == pytest.approx(1)
    )
    assert (
        metrics.maximum_drawdown_usd
        == pytest.approx(25)
    )
    assert (
        metrics.maximum_drawdown_percent
        == pytest.approx(
            25 / 1015 * 100
        )
    )
    assert metrics.total_fees_usd == 4
def test_performance_without_completed_trades_is_safe():
    execution = (
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
            steps=[
                step(
                    sequence=1,
                    equity=1000,
                ),
                step(
                    sequence=2,
                    equity=995,
                ),
            ],
            final_portfolio=portfolio(
                equity=995,
                fees=0,
                unrealized=-5,
            ),
        )
    )
    result = (
        BacktestPerformanceService
        .analyze(execution)
    )
    metrics = result.performance
    assert metrics.completed_trade_count == 0
    assert metrics.win_rate_percent == 0
    assert metrics.average_win_usd == 0
    assert metrics.average_loss_usd == 0
    assert metrics.profit_factor is None
    assert metrics.total_net_pnl_usd == -5
    assert metrics.return_percent == -0.5
    assert metrics.maximum_drawdown_usd == 5
    assert metrics.maximum_drawdown_percent == 0.5
def test_performance_analysis_is_deterministic():
    execution = execution_with_metrics()
    first = (
        BacktestPerformanceService
        .analyze(execution)
    )
    second = (
        BacktestPerformanceService
        .analyze(execution)
    )
    assert (
        first.model_dump(
            mode="json"
        )
        == second.model_dump(
            mode="json"
        )
    )
