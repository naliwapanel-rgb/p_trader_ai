from collections.abc import (
    Callable,
)
from dataclasses import (
    dataclass,
)
from datetime import (
    datetime,
)
from decimal import (
    Decimal,
    ROUND_DOWN,
)
from app.schemas.trading_bot_backtest import (
    BacktestCompletedTrade,
    BacktestExecutionStep,
    BacktestOrderFill,
    BacktestPortfolioSnapshot,
    BacktestPositionSnapshot,
    TradingBotBacktestExecutionResult,
    TradingBotBacktestRequest,
)
from app.services.backtest_market_replay_service import (
    BacktestMarketReplayService,
)
from app.services.trading_bot_strategy_runner import (
    TradingBotStrategyRunner,
)
StrategyRunnerFactory = Callable[
    [datetime],
    TradingBotStrategyRunner,
]
@dataclass
class _BacktestPosition:
    side: str
    quantity: Decimal
    average_entry_price: Decimal
    current_price: Decimal
    reserved_margin: Decimal
    unrealized_pnl: Decimal
    entry_fees: Decimal
    opened_at: datetime
@dataclass
class _BacktestPortfolio:
    initial_balance: Decimal
    cash: Decimal
    reserved: Decimal
    equity: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_fees: Decimal
    position: _BacktestPosition | None
class BacktestExecutionEngine:
    def __init__(
        self,
        *,
        strategy_runner_factory: (
            StrategyRunnerFactory | None
        ) = None,
    ):
        self.strategy_runner_factory = (
            strategy_runner_factory
            or self._default_runner
        )
    @staticmethod
    def _default_runner(
        evaluated_at: datetime,
    ) -> TradingBotStrategyRunner:
        return TradingBotStrategyRunner(
            clock=lambda: evaluated_at
        )
    @staticmethod
    def _decimal(
        value,
    ) -> Decimal:
        return Decimal(str(value))
    @staticmethod
    def _position_pnl(
        *,
        side: str,
        quantity: Decimal,
        entry_price: Decimal,
        current_price: Decimal,
    ) -> Decimal:
        if side == "LONG":
            return (
                current_price
                - entry_price
            ) * quantity
        return (
            entry_price
            - current_price
        ) * quantity
    @classmethod
    def _fill_price(
        cls,
        *,
        action: str,
        reference_price: Decimal,
        slippage_rate: Decimal,
    ) -> Decimal:
        if action == "BUY":
            return (
                reference_price
                * (
                    Decimal("1")
                    + slippage_rate
                )
            )
        return (
            reference_price
            * (
                Decimal("1")
                - slippage_rate
            )
        )
    @staticmethod
    def _quantity(
        *,
        notional: Decimal,
        fill_price: Decimal,
        decimal_places: int,
    ) -> Decimal:
        quantum = Decimal(1).scaleb(
            -decimal_places
        )
        return (
            notional
            / fill_price
        ).quantize(
            quantum,
            rounding=ROUND_DOWN,
        )
    @classmethod
    def _mark_to_market(
        cls,
        *,
        portfolio: _BacktestPortfolio,
        current_price: Decimal,
    ) -> None:
        position = portfolio.position
        if position is None:
            portfolio.unrealized_pnl = (
                Decimal("0")
            )
            portfolio.equity = (
                portfolio.cash
                + portfolio.reserved
            )
            return
        unrealized = cls._position_pnl(
            side=position.side,
            quantity=position.quantity,
            entry_price=(
                position
                .average_entry_price
            ),
            current_price=current_price,
        )
        position.current_price = (
            current_price
        )
        position.unrealized_pnl = (
            unrealized
        )
        portfolio.unrealized_pnl = (
            unrealized
        )
        portfolio.equity = (
            portfolio.cash
            + portfolio.reserved
            + unrealized
        )
    @classmethod
    def _position_snapshot(
        cls,
        position: (
            _BacktestPosition | None
        ),
    ) -> BacktestPositionSnapshot | None:
        if position is None:
            return None
        return BacktestPositionSnapshot(
            side=position.side,
            quantity=float(
                position.quantity
            ),
            average_entry_price=float(
                position
                .average_entry_price
            ),
            current_price=float(
                position.current_price
            ),
            position_value_usd=float(
                position.quantity
                * position.current_price
            ),
            reserved_margin_usd=float(
                position.reserved_margin
            ),
            unrealized_pnl_usd=float(
                position.unrealized_pnl
            ),
            entry_fees_usd=float(
                position.entry_fees
            ),
            opened_at=position.opened_at,
        )
    @classmethod
    def _portfolio_snapshot(
        cls,
        portfolio: _BacktestPortfolio,
    ) -> BacktestPortfolioSnapshot:
        return BacktestPortfolioSnapshot(
            initial_balance_usd=float(
                portfolio.initial_balance
            ),
            cash_balance_usd=float(
                portfolio.cash
            ),
            reserved_balance_usd=float(
                portfolio.reserved
            ),
            equity_usd=float(
                portfolio.equity
            ),
            realized_pnl_usd=float(
                portfolio.realized_pnl
            ),
            unrealized_pnl_usd=float(
                portfolio.unrealized_pnl
            ),
            total_fees_usd=float(
                portfolio.total_fees
            ),
            open_position=(
                cls._position_snapshot(
                    portfolio.position
                )
            ),
        )
    @classmethod
    def _available_notional(
        cls,
        *,
        bot,
        portfolio: _BacktestPortfolio,
        reference_price: Decimal,
        fee_rate: Decimal,
    ) -> Decimal:
        equity = max(
            portfolio.equity,
            Decimal("0"),
        )
        risk_notional = (
            equity
            * cls._decimal(
                bot.risk_per_trade_percent
            )
            / Decimal("100")
        )
        maximum_position = cls._decimal(
            bot.max_position_value_usd
        )
        existing_notional = Decimal("0")
        if portfolio.position is not None:
            existing_notional = (
                portfolio
                .position
                .quantity
                * reference_price
            )
        remaining_capacity = max(
            maximum_position
            - existing_notional,
            Decimal("0"),
        )
        cash_capacity = (
            portfolio.cash
            / (
                Decimal("1")
                + fee_rate
            )
        )
        return min(
            risk_notional,
            remaining_capacity,
            cash_capacity,
        )
    @classmethod
    def _open_or_increase(
        cls,
        *,
        bot,
        data: TradingBotBacktestRequest,
        portfolio: _BacktestPortfolio,
        sequence: int,
        evaluated_at: datetime,
        action: str,
        reference_price: Decimal,
        reason: str,
    ) -> tuple[
        str,
        BacktestOrderFill | None,
    ]:
        desired_side = (
            "LONG"
            if action == "BUY"
            else "SHORT"
        )
        fee_rate = cls._decimal(
            data.fee_rate
        )
        slippage_rate = cls._decimal(
            data.slippage_rate
        )
        target_notional = (
            cls._available_notional(
                bot=bot,
                portfolio=portfolio,
                reference_price=(
                    reference_price
                ),
                fee_rate=fee_rate,
            )
        )
        minimum_notional = cls._decimal(
            data.minimum_order_notional_usd
        )
        if target_notional < minimum_notional:
            return "REJECTED", None
        fill_price = cls._fill_price(
            action=action,
            reference_price=(
                reference_price
            ),
            slippage_rate=(
                slippage_rate
            ),
        )
        quantity = cls._quantity(
            notional=target_notional,
            fill_price=fill_price,
            decimal_places=(
                data.quantity_decimal_places
            ),
        )
        gross_value = (
            quantity
            * fill_price
        )
        if (
            quantity <= 0
            or gross_value
            < minimum_notional
        ):
            return "REJECTED", None
        fee = (
            gross_value
            * fee_rate
        )
        required_cash = (
            gross_value
            + fee
        )
        if required_cash > portfolio.cash:
            return "REJECTED", None
        position = portfolio.position
        if position is None:
            position = _BacktestPosition(
                side=desired_side,
                quantity=quantity,
                average_entry_price=(
                    fill_price
                ),
                current_price=(
                    reference_price
                ),
                reserved_margin=(
                    gross_value
                ),
                unrealized_pnl=(
                    cls._position_pnl(
                        side=desired_side,
                        quantity=quantity,
                        entry_price=fill_price,
                        current_price=(
                            reference_price
                        ),
                    )
                ),
                entry_fees=fee,
                opened_at=evaluated_at,
            )
            portfolio.position = position
            position_effect = "OPEN"
            outcome = "OPENED"
        else:
            old_quantity = (
                position.quantity
            )
            new_quantity = (
                old_quantity
                + quantity
            )
            new_entry = (
                (
                    old_quantity
                    * position
                    .average_entry_price
                )
                + (
                    quantity
                    * fill_price
                )
            ) / new_quantity
            position.quantity = new_quantity
            position.average_entry_price = (
                new_entry
            )
            position.current_price = (
                reference_price
            )
            position.reserved_margin += (
                gross_value
            )
            position.entry_fees += fee
            position.unrealized_pnl = (
                cls._position_pnl(
                    side=position.side,
                    quantity=new_quantity,
                    entry_price=new_entry,
                    current_price=(
                        reference_price
                    ),
                )
            )
            position_effect = "INCREASE"
            outcome = "INCREASED"
        portfolio.cash -= required_cash
        portfolio.reserved += gross_value
        portfolio.total_fees += fee
        cls._mark_to_market(
            portfolio=portfolio,
            current_price=reference_price,
        )
        slippage_usd = (
            abs(
                fill_price
                - reference_price
            )
            * quantity
        )
        order = BacktestOrderFill(
            sequence=sequence,
            filled_at=evaluated_at,
            side=action,
            position_side=desired_side,
            position_effect=(
                position_effect
            ),
            quantity=float(quantity),
            reference_price=float(
                reference_price
            ),
            fill_price=float(
                fill_price
            ),
            gross_value_usd=float(
                gross_value
            ),
            fee_usd=float(fee),
            slippage_usd=float(
                slippage_usd
            ),
            realized_pnl_usd=0.0,
            forced=False,
            reason=reason,
        )
        return outcome, order
    @classmethod
    def _close_position(
        cls,
        *,
        data: TradingBotBacktestRequest,
        portfolio: _BacktestPortfolio,
        sequence: int,
        evaluated_at: datetime,
        reference_price: Decimal,
        reason: str,
        forced: bool,
    ) -> tuple[
        BacktestOrderFill,
        BacktestCompletedTrade,
    ]:
        position = portfolio.position
        if position is None:
            raise ValueError(
                "Backtest position is missing"
            )
        action = (
            "SELL"
            if position.side == "LONG"
            else "BUY"
        )
        fee_rate = cls._decimal(
            data.fee_rate
        )
        slippage_rate = cls._decimal(
            data.slippage_rate
        )
        fill_price = cls._fill_price(
            action=action,
            reference_price=(
                reference_price
            ),
            slippage_rate=(
                slippage_rate
            ),
        )
        gross_value = (
            position.quantity
            * fill_price
        )
        closing_fee = (
            gross_value
            * fee_rate
        )
        realized_pnl = (
            cls._position_pnl(
                side=position.side,
                quantity=position.quantity,
                entry_price=(
                    position
                    .average_entry_price
                ),
                current_price=fill_price,
            )
        )
        new_cash = (
            portfolio.cash
            + position.reserved_margin
            + realized_pnl
            - closing_fee
        )
        if new_cash < 0:
            raise ValueError(
                "Backtest portfolio cannot "
                "absorb the closing loss"
            )
        total_trade_fees = (
            position.entry_fees
            + closing_fee
        )
        trade = BacktestCompletedTrade(
            side=position.side,
            opened_at=position.opened_at,
            closed_at=evaluated_at,
            quantity=float(
                position.quantity
            ),
            average_entry_price=float(
                position
                .average_entry_price
            ),
            exit_price=float(
                fill_price
            ),
            gross_realized_pnl_usd=float(
                realized_pnl
            ),
            total_fees_usd=float(
                total_trade_fees
            ),
            net_realized_pnl_usd=float(
                realized_pnl
                - total_trade_fees
            ),
            forced_exit=forced,
        )
        slippage_usd = (
            abs(
                fill_price
                - reference_price
            )
            * position.quantity
        )
        order = BacktestOrderFill(
            sequence=sequence,
            filled_at=evaluated_at,
            side=action,
            position_side=position.side,
            position_effect="CLOSE",
            quantity=float(
                position.quantity
            ),
            reference_price=float(
                reference_price
            ),
            fill_price=float(
                fill_price
            ),
            gross_value_usd=float(
                gross_value
            ),
            fee_usd=float(
                closing_fee
            ),
            slippage_usd=float(
                slippage_usd
            ),
            realized_pnl_usd=float(
                realized_pnl
            ),
            forced=forced,
            reason=reason,
        )
        portfolio.cash = new_cash
        portfolio.reserved = max(
            portfolio.reserved
            - position.reserved_margin,
            Decimal("0"),
        )
        portfolio.realized_pnl += (
            realized_pnl
        )
        portfolio.total_fees += (
            closing_fee
        )
        portfolio.unrealized_pnl = (
            Decimal("0")
        )
        portfolio.position = None
        portfolio.equity = (
            portfolio.cash
            + portfolio.reserved
        )
        return order, trade
    @classmethod
    def _execute_decision(
        cls,
        *,
        bot,
        data: TradingBotBacktestRequest,
        portfolio: _BacktestPortfolio,
        sequence: int,
        evaluated_at: datetime,
        decision,
    ) -> tuple[
        str,
        BacktestOrderFill | None,
        BacktestCompletedTrade | None,
    ]:
        reference_price = cls._decimal(
            decision.reference_price
        )
        if decision.action == "HOLD":
            cls._mark_to_market(
                portfolio=portfolio,
                current_price=(
                    reference_price
                ),
            )
            return (
                "NO_ACTION",
                None,
                None,
            )
        desired_side = (
            "LONG"
            if decision.action == "BUY"
            else "SHORT"
        )
        if (
            portfolio.position is not None
            and portfolio.position.side
            != desired_side
        ):
            order, trade = (
                cls._close_position(
                    data=data,
                    portfolio=portfolio,
                    sequence=sequence,
                    evaluated_at=(
                        evaluated_at
                    ),
                    reference_price=(
                        reference_price
                    ),
                    reason=decision.reason,
                    forced=False,
                )
            )
            return (
                "CLOSED",
                order,
                trade,
            )
        outcome, order = (
            cls._open_or_increase(
                bot=bot,
                data=data,
                portfolio=portfolio,
                sequence=sequence,
                evaluated_at=evaluated_at,
                action=decision.action,
                reference_price=(
                    reference_price
                ),
                reason=decision.reason,
            )
        )
        return outcome, order, None
    async def run(
        self,
        *,
        bot,
        data: TradingBotBacktestRequest,
    ) -> TradingBotBacktestExecutionResult:
        frames = (
            BacktestMarketReplayService
            .build_frames(
                bot=bot,
                data=data,
            )
        )
        validation_runner = (
            self.strategy_runner_factory(
                frames[0].candle.closed_at
            )
        )
        validate_bot = getattr(
            validation_runner,
            "validate_bot",
            None,
        )
        if callable(validate_bot):
            validate_bot(bot)
        initial_balance = self._decimal(
            data.initial_balance_usd
        )
        portfolio = _BacktestPortfolio(
            initial_balance=(
                initial_balance
            ),
            cash=initial_balance,
            reserved=Decimal("0"),
            equity=initial_balance,
            realized_pnl=Decimal("0"),
            unrealized_pnl=Decimal("0"),
            total_fees=Decimal("0"),
            position=None,
        )
        all_orders = []
        completed_trades = []
        steps = []
        warmup_count = 0
        evaluated_count = 0
        for index, frame in enumerate(
            frames
        ):
            reference_price = self._decimal(
                frame.ticker.last_price
            )
            self._mark_to_market(
                portfolio=portfolio,
                current_price=reference_price,
            )
            step_orders = []
            outcomes = []
            decision = None
            if not frame.warmup_complete:
                warmup_count += 1
                outcomes.append("WARMUP")
            else:
                evaluated_count += 1
                runner = (
                    self.strategy_runner_factory(
                        frame.candle.closed_at
                    )
                )
                decision = await runner.run(
                    bot=bot,
                    ticker=frame.ticker,
                )
                (
                    outcome,
                    order,
                    trade,
                ) = self._execute_decision(
                    bot=bot,
                    data=data,
                    portfolio=portfolio,
                    sequence=frame.sequence,
                    evaluated_at=(
                        frame.candle.closed_at
                    ),
                    decision=decision,
                )
                outcomes.append(outcome)
                if order is not None:
                    step_orders.append(order)
                    all_orders.append(order)
                if trade is not None:
                    completed_trades.append(
                        trade
                    )
            is_final = (
                index
                == len(frames) - 1
            )
            if (
                is_final
                and data.force_close_at_end
                and portfolio.position
                is not None
            ):
                forced_order, forced_trade = (
                    self._close_position(
                        data=data,
                        portfolio=portfolio,
                        sequence=frame.sequence,
                        evaluated_at=(
                            frame.candle.closed_at
                        ),
                        reference_price=(
                            reference_price
                        ),
                        reason=(
                            "Backtest forced close "
                            "at the end of the "
                            "historical series"
                        ),
                        forced=True,
                    )
                )
                outcomes.append(
                    "FORCED_CLOSED"
                )
                step_orders.append(
                    forced_order
                )
                all_orders.append(
                    forced_order
                )
                completed_trades.append(
                    forced_trade
                )
            steps.append(
                BacktestExecutionStep(
                    sequence=frame.sequence,
                    candle_closed_at=(
                        frame.candle.closed_at
                    ),
                    warmup_complete=(
                        frame.warmup_complete
                    ),
                    decision=decision,
                    outcomes=outcomes,
                    orders=step_orders,
                    portfolio=(
                        self._portfolio_snapshot(
                            portfolio
                        )
                    ),
                )
            )
        return (
            TradingBotBacktestExecutionResult(
                bot_id=bot.id,
                symbol=(
                    str(bot.symbol)
                    .strip()
                    .upper()
                ),
                category=bot.category,
                timeframe=bot.timeframe,
                started_at=(
                    frames[0]
                    .candle
                    .opened_at
                ),
                ended_at=(
                    frames[-1]
                    .candle
                    .closed_at
                ),
                frames_processed=len(
                    frames
                ),
                warmup_frame_count=(
                    warmup_count
                ),
                evaluated_frame_count=(
                    evaluated_count
                ),
                order_count=len(
                    all_orders
                ),
                completed_trade_count=len(
                    completed_trades
                ),
                orders=all_orders,
                completed_trades=(
                    completed_trades
                ),
                steps=steps,
                final_portfolio=(
                    self._portfolio_snapshot(
                        portfolio
                    )
                ),
            )
        )
