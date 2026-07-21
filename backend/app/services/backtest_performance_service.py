from decimal import (
    Decimal,
)
from app.schemas.trading_bot_backtest import (
    BacktestEquityPoint,
    BacktestPerformanceSummary,
    TradingBotBacktestExecutionResult,
    TradingBotBacktestResult,
)
class BacktestPerformanceService:
    @staticmethod
    def _decimal(
        value,
    ) -> Decimal:
        return Decimal(str(value))
    @classmethod
    def _build_equity_curve(
        cls,
        execution: (
            TradingBotBacktestExecutionResult
        ),
    ) -> list[BacktestEquityPoint]:
        initial_equity = cls._decimal(
            execution
            .final_portfolio
            .initial_balance_usd
        )
        peak_equity = initial_equity
        points = [
            BacktestEquityPoint(
                sequence=0,
                recorded_at=(
                    execution.started_at
                ),
                equity_usd=float(
                    initial_equity
                ),
                peak_equity_usd=float(
                    peak_equity
                ),
                drawdown_usd=0.0,
                drawdown_percent=0.0,
            )
        ]
        for step in execution.steps:
            equity = cls._decimal(
                step.portfolio.equity_usd
            )
            peak_equity = max(
                peak_equity,
                equity,
            )
            drawdown = max(
                peak_equity - equity,
                Decimal("0"),
            )
            drawdown_percent = (
                (
                    drawdown
                    / peak_equity
                    * Decimal("100")
                )
                if peak_equity > 0
                else Decimal("0")
            )
            points.append(
                BacktestEquityPoint(
                    sequence=step.sequence,
                    recorded_at=(
                        step.candle_closed_at
                    ),
                    equity_usd=float(
                        equity
                    ),
                    peak_equity_usd=float(
                        peak_equity
                    ),
                    drawdown_usd=float(
                        drawdown
                    ),
                    drawdown_percent=float(
                        drawdown_percent
                    ),
                )
            )
        return points
    @classmethod
    def analyze(
        cls,
        execution: (
            TradingBotBacktestExecutionResult
        ),
    ) -> TradingBotBacktestResult:
        equity_curve = (
            cls._build_equity_curve(
                execution
            )
        )
        net_results = [
            cls._decimal(
                trade.net_realized_pnl_usd
            )
            for trade
            in execution.completed_trades
        ]
        winning_results = [
            result
            for result in net_results
            if result > 0
        ]
        losing_results = [
            result
            for result in net_results
            if result < 0
        ]
        breakeven_results = [
            result
            for result in net_results
            if result == 0
        ]
        gross_profit = sum(
            winning_results,
            Decimal("0"),
        )
        gross_loss = abs(
            sum(
                losing_results,
                Decimal("0"),
            )
        )
        net_realized = sum(
            net_results,
            Decimal("0"),
        )
        winning_count = len(
            winning_results
        )
        losing_count = len(
            losing_results
        )
        completed_count = len(
            net_results
        )
        win_rate = (
            (
                Decimal(winning_count)
                / Decimal(completed_count)
                * Decimal("100")
            )
            if completed_count
            else Decimal("0")
        )
        average_win = (
            gross_profit
            / Decimal(winning_count)
            if winning_count
            else Decimal("0")
        )
        average_loss = (
            -gross_loss
            / Decimal(losing_count)
            if losing_count
            else Decimal("0")
        )
        profit_factor = (
            gross_profit
            / gross_loss
            if gross_loss > 0
            else None
        )
        maximum_drawdown_usd = max(
            (
                cls._decimal(
                    point.drawdown_usd
                )
                for point
                in equity_curve
            ),
            default=Decimal("0"),
        )
        maximum_drawdown_percent = max(
            (
                cls._decimal(
                    point.drawdown_percent
                )
                for point
                in equity_curve
            ),
            default=Decimal("0"),
        )
        initial_balance = cls._decimal(
            execution
            .final_portfolio
            .initial_balance_usd
        )
        final_equity = cls._decimal(
            execution
            .final_portfolio
            .equity_usd
        )
        total_net_pnl = (
            final_equity
            - initial_balance
        )
        return_percent = (
            (
                total_net_pnl
                / initial_balance
                * Decimal("100")
            )
            if initial_balance > 0
            else Decimal("0")
        )
        forced_exit_count = sum(
            1
            for trade
            in execution.completed_trades
            if trade.forced_exit
        )
        performance = (
            BacktestPerformanceSummary(
                initial_balance_usd=float(
                    initial_balance
                ),
                final_equity_usd=float(
                    final_equity
                ),
                total_net_pnl_usd=float(
                    total_net_pnl
                ),
                return_percent=float(
                    return_percent
                ),
                maximum_drawdown_usd=float(
                    maximum_drawdown_usd
                ),
                maximum_drawdown_percent=float(
                    maximum_drawdown_percent
                ),
                order_count=(
                    execution.order_count
                ),
                completed_trade_count=(
                    completed_count
                ),
                winning_trade_count=(
                    winning_count
                ),
                losing_trade_count=(
                    losing_count
                ),
                breakeven_trade_count=len(
                    breakeven_results
                ),
                forced_exit_count=(
                    forced_exit_count
                ),
                gross_profit_usd=float(
                    gross_profit
                ),
                gross_loss_usd=float(
                    gross_loss
                ),
                net_realized_pnl_usd=float(
                    net_realized
                ),
                unrealized_pnl_usd=(
                    execution
                    .final_portfolio
                    .unrealized_pnl_usd
                ),
                total_fees_usd=(
                    execution
                    .final_portfolio
                    .total_fees_usd
                ),
                win_rate_percent=float(
                    win_rate
                ),
                average_win_usd=float(
                    average_win
                ),
                average_loss_usd=float(
                    average_loss
                ),
                profit_factor=(
                    float(profit_factor)
                    if profit_factor
                    is not None
                    else None
                ),
            )
        )
        return TradingBotBacktestResult(
            execution=execution,
            equity_curve=equity_curve,
            performance=performance,
        )
