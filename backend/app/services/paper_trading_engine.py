from collections.abc import (
    Callable,
)
from datetime import (
    UTC,
    datetime,
)
from decimal import (
    Decimal,
    ROUND_DOWN,
)
from sqlalchemy.orm import (
    Session,
)
from app.repositories.paper_trading_repository import (
    PaperTradingRepository,
)
from app.schemas.paper_trading import (
    PaperTradingAccountCreate,
    PaperTradingAccountResponse,
    PaperTradingEngineSettings,
    PaperTradingExecutionResult,
    PaperTradingOrderCreate,
    PaperTradingOrderResponse,
    PaperTradingPositionCreate,
    PaperTradingPositionResponse,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyDecision,
)
PaperTradingClock = Callable[
    [],
    datetime,
]
class PaperTradingEngine:
    def __init__(
        self,
        db: Session,
        *,
        repository: (
            PaperTradingRepository | None
        ) = None,
        settings: (
            PaperTradingEngineSettings | None
        ) = None,
        clock: PaperTradingClock | None = None,
    ):
        self.db = db
        self.repository = (
            repository
            or PaperTradingRepository(db)
        )
        self.settings = (
            settings
            or PaperTradingEngineSettings()
        )
        self.clock = (
            clock
            or (
                lambda: datetime.now(UTC)
            )
        )
    @staticmethod
    def _decimal(
        value,
    ) -> Decimal:
        return Decimal(str(value))
    def _quantity(
        self,
        *,
        notional: Decimal,
        fill_price: Decimal,
    ) -> Decimal:
        places = (
            self.settings
            .quantity_decimal_places
        )
        quantum = Decimal(1).scaleb(
            -places
        )
        return (
            notional
            / fill_price
        ).quantize(
            quantum,
            rounding=ROUND_DOWN,
        )
    def _fill_price(
        self,
        *,
        action: str,
        reference_price: Decimal,
    ) -> Decimal:
        slippage = self._decimal(
            self.settings.slippage_rate
        )
        if action == "BUY":
            return (
                reference_price
                * (
                    Decimal("1")
                    + slippage
                )
            )
        return (
            reference_price
            * (
                Decimal("1")
                - slippage
            )
        )
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
    def _refresh_entities(
        self,
        *entities,
    ) -> None:
        for entity in entities:
            if entity is not None:
                self.db.refresh(entity)
    def _result(
        self,
        *,
        outcome: str,
        action: str,
        message: str,
        account_created: bool,
        account,
        position=None,
        order=None,
    ) -> PaperTradingExecutionResult:
        return PaperTradingExecutionResult(
            outcome=outcome,
            decision_action=action,
            message=message,
            account_created=(
                account_created
            ),
            account=(
                PaperTradingAccountResponse
                .model_validate(account)
            ),
            position=(
                PaperTradingPositionResponse
                .model_validate(position)
                if position is not None
                else None
            ),
            order=(
                PaperTradingOrderResponse
                .model_validate(order)
                if order is not None
                else None
            ),
        )
    def _commit_result(
        self,
        *,
        outcome: str,
        action: str,
        message: str,
        account_created: bool,
        account,
        position=None,
        order=None,
    ) -> PaperTradingExecutionResult:
        self.db.commit()
        self._refresh_entities(
            account,
            position,
            order,
        )
        return self._result(
            outcome=outcome,
            action=action,
            message=message,
            account_created=(
                account_created
            ),
            account=account,
            position=position,
            order=order,
        )
    def _mark_to_market(
        self,
        *,
        account,
        position,
        current_price: Decimal,
    ) -> None:
        if position is None:
            self.repository.save_account(
                account=account,
                commit=False,
                unrealized_pnl_usd=0.0,
                equity_usd=(
                    float(
                        self._decimal(
                            account.cash_balance_usd
                        )
                        + self._decimal(
                            account
                            .reserved_balance_usd
                        )
                    )
                ),
            )
            return
        quantity = self._decimal(
            position.quantity
        )
        entry_price = self._decimal(
            position.average_entry_price
        )
        unrealized = self._position_pnl(
            side=position.side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
        )
        position_value = (
            quantity
            * current_price
        )
        self.repository.save_position(
            position=position,
            commit=False,
            current_price=float(
                current_price
            ),
            position_value_usd=float(
                position_value
            ),
            unrealized_pnl_usd=float(
                unrealized
            ),
        )
        equity = (
            self._decimal(
                account.cash_balance_usd
            )
            + self._decimal(
                account.reserved_balance_usd
            )
            + unrealized
        )
        self.repository.save_account(
            account=account,
            commit=False,
            unrealized_pnl_usd=float(
                unrealized
            ),
            equity_usd=float(equity),
        )
    def _available_notional(
        self,
        *,
        account,
        bot,
        position,
        reference_price: Decimal,
    ) -> Decimal:
        equity = max(
            self._decimal(
                account.equity_usd
            ),
            Decimal("0"),
        )
        risk_percent = self._decimal(
            bot.risk_per_trade_percent
        )
        risk_notional = (
            equity
            * risk_percent
            / Decimal("100")
        )
        maximum_position = self._decimal(
            bot.max_position_value_usd
        )
        existing_notional = Decimal("0")
        if position is not None:
            existing_notional = (
                self._decimal(
                    position.quantity
                )
                * reference_price
            )
        remaining_capacity = max(
            maximum_position
            - existing_notional,
            Decimal("0"),
        )
        fee_multiplier = (
            Decimal("1")
            + self._decimal(
                self.settings.fee_rate
            )
        )
        cash_capacity = (
            self._decimal(
                account.cash_balance_usd
            )
            / fee_multiplier
        )
        return min(
            risk_notional,
            remaining_capacity,
            cash_capacity,
        )
    def _open_or_increase(
        self,
        *,
        bot,
        account,
        position,
        decision: TradingBotStrategyDecision,
        account_created: bool,
    ) -> PaperTradingExecutionResult:
        action = decision.action
        desired_side = (
            "LONG"
            if action == "BUY"
            else "SHORT"
        )
        reference_price = self._decimal(
            decision.reference_price
        )
        target_notional = (
            self._available_notional(
                account=account,
                bot=bot,
                position=position,
                reference_price=(
                    reference_price
                ),
            )
        )
        minimum_notional = self._decimal(
            self.settings
            .minimum_order_notional_usd
        )
        if target_notional < minimum_notional:
            return self._commit_result(
                outcome="REJECTED",
                action=action,
                message=(
                    "Available paper balance or "
                    "position capacity is below "
                    "the minimum order notional"
                ),
                account_created=(
                    account_created
                ),
                account=account,
                position=position,
            )
        fill_price = self._fill_price(
            action=action,
            reference_price=(
                reference_price
            ),
        )
        quantity = self._quantity(
            notional=target_notional,
            fill_price=fill_price,
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
            return self._commit_result(
                outcome="REJECTED",
                action=action,
                message=(
                    "Calculated paper quantity "
                    "is below the minimum order "
                    "notional"
                ),
                account_created=(
                    account_created
                ),
                account=account,
                position=position,
            )
        fee_rate = self._decimal(
            self.settings.fee_rate
        )
        fee = (
            gross_value
            * fee_rate
        )
        required_cash = (
            gross_value
            + fee
        )
        current_cash = self._decimal(
            account.cash_balance_usd
        )
        if required_cash > current_cash:
            return self._commit_result(
                outcome="REJECTED",
                action=action,
                message=(
                    "Paper account has "
                    "insufficient available cash"
                ),
                account_created=(
                    account_created
                ),
                account=account,
                position=position,
            )
        now = self.clock()
        if position is None:
            position = (
                self.repository
                .create_position(
                    PaperTradingPositionCreate(
                        user_id=bot.user_id,
                        trading_bot_id=bot.id,
                        paper_account_id=(
                            account.id
                        ),
                        symbol=bot.symbol,
                        category=bot.category,
                        side=desired_side,
                        quantity=float(
                            quantity
                        ),
                        average_entry_price=float(
                            fill_price
                        ),
                        current_price=float(
                            reference_price
                        ),
                        position_value_usd=float(
                            quantity
                            * reference_price
                        ),
                        reserved_margin_usd=float(
                            gross_value
                        ),
                        unrealized_pnl_usd=float(
                            self._position_pnl(
                                side=desired_side,
                                quantity=quantity,
                                entry_price=(
                                    fill_price
                                ),
                                current_price=(
                                    reference_price
                                ),
                            )
                        ),
                        realized_pnl_usd=0.0,
                        total_fees_usd=float(
                            fee
                        ),
                        opened_at=now,
                    ),
                    commit=False,
                )
            )
            position_effect = "OPEN"
            outcome = "OPENED"
            message = (
                f"Paper {desired_side.lower()} "
                "position opened"
            )
        else:
            old_quantity = self._decimal(
                position.quantity
            )
            old_entry = self._decimal(
                position
                .average_entry_price
            )
            new_quantity = (
                old_quantity
                + quantity
            )
            new_entry = (
                (
                    old_quantity
                    * old_entry
                )
                + (
                    quantity
                    * fill_price
                )
            ) / new_quantity
            new_reserved = (
                self._decimal(
                    position
                    .reserved_margin_usd
                )
                + gross_value
            )
            unrealized = (
                self._position_pnl(
                    side=position.side,
                    quantity=new_quantity,
                    entry_price=new_entry,
                    current_price=(
                        reference_price
                    ),
                )
            )
            position = (
                self.repository
                .save_position(
                    position=position,
                    commit=False,
                    quantity=float(
                        new_quantity
                    ),
                    average_entry_price=float(
                        new_entry
                    ),
                    current_price=float(
                        reference_price
                    ),
                    position_value_usd=float(
                        new_quantity
                        * reference_price
                    ),
                    reserved_margin_usd=float(
                        new_reserved
                    ),
                    unrealized_pnl_usd=float(
                        unrealized
                    ),
                    total_fees_usd=float(
                        self._decimal(
                            position.total_fees_usd
                        )
                        + fee
                    ),
                )
            )
            position_effect = "INCREASE"
            outcome = "INCREASED"
            message = (
                f"Paper {desired_side.lower()} "
                "position increased"
            )
        position_unrealized = self._decimal(
            position.unrealized_pnl_usd
        )
        new_cash = (
            current_cash
            - required_cash
        )
        new_reserved = (
            self._decimal(
                account.reserved_balance_usd
            )
            + gross_value
        )
        account = (
            self.repository.save_account(
                account=account,
                commit=False,
                cash_balance_usd=float(
                    new_cash
                ),
                reserved_balance_usd=float(
                    new_reserved
                ),
                unrealized_pnl_usd=float(
                    position_unrealized
                ),
                total_fees_usd=float(
                    self._decimal(
                        account.total_fees_usd
                    )
                    + fee
                ),
                equity_usd=float(
                    new_cash
                    + new_reserved
                    + position_unrealized
                ),
            )
        )
        slippage_usd = (
            abs(
                fill_price
                - reference_price
            )
            * quantity
        )
        order = (
            self.repository.create_order(
                PaperTradingOrderCreate(
                    user_id=bot.user_id,
                    trading_bot_id=bot.id,
                    paper_account_id=(
                        account.id
                    ),
                    paper_position_id=(
                        position.id
                    ),
                    symbol=bot.symbol,
                    category=bot.category,
                    side=action,
                    position_effect=(
                        position_effect
                    ),
                    quantity=float(
                        quantity
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
                    fee_rate=float(
                        fee_rate
                    ),
                    fee_usd=float(fee),
                    slippage_rate=(
                        self.settings
                        .slippage_rate
                    ),
                    slippage_usd=float(
                        slippage_usd
                    ),
                    realized_pnl_usd=0.0,
                    decision_reason=(
                        decision.reason
                    ),
                    filled_at=now,
                ),
                commit=False,
            )
        )
        return self._commit_result(
            outcome=outcome,
            action=action,
            message=message,
            account_created=(
                account_created
            ),
            account=account,
            position=position,
            order=order,
        )
    def _close_position(
        self,
        *,
        bot,
        account,
        position,
        decision: TradingBotStrategyDecision,
        account_created: bool,
    ) -> PaperTradingExecutionResult:
        action = decision.action
        reference_price = self._decimal(
            decision.reference_price
        )
        fill_price = self._fill_price(
            action=action,
            reference_price=(
                reference_price
            ),
        )
        quantity = self._decimal(
            position.quantity
        )
        entry_price = self._decimal(
            position.average_entry_price
        )
        gross_value = (
            quantity
            * fill_price
        )
        fee_rate = self._decimal(
            self.settings.fee_rate
        )
        fee = (
            gross_value
            * fee_rate
        )
        realized_pnl = (
            self._position_pnl(
                side=position.side,
                quantity=quantity,
                entry_price=entry_price,
                current_price=fill_price,
            )
        )
        released_margin = self._decimal(
            position.reserved_margin_usd
        )
        new_cash = (
            self._decimal(
                account.cash_balance_usd
            )
            + released_margin
            + realized_pnl
            - fee
        )
        if new_cash < Decimal("0"):
            raise ValueError(
                "Paper account cannot absorb "
                "the simulated closing loss"
            )
        new_reserved = max(
            self._decimal(
                account.reserved_balance_usd
            )
            - released_margin,
            Decimal("0"),
        )
        now = self.clock()
        position = (
            self.repository.save_position(
                position=position,
                commit=False,
                status="CLOSED",
                current_price=float(
                    fill_price
                ),
                position_value_usd=0.0,
                reserved_margin_usd=0.0,
                unrealized_pnl_usd=0.0,
                realized_pnl_usd=float(
                    self._decimal(
                        position
                        .realized_pnl_usd
                    )
                    + realized_pnl
                ),
                total_fees_usd=float(
                    self._decimal(
                        position.total_fees_usd
                    )
                    + fee
                ),
                closed_at=now,
            )
        )
        account = (
            self.repository.save_account(
                account=account,
                commit=False,
                cash_balance_usd=float(
                    new_cash
                ),
                reserved_balance_usd=float(
                    new_reserved
                ),
                realized_pnl_usd=float(
                    self._decimal(
                        account.realized_pnl_usd
                    )
                    + realized_pnl
                ),
                unrealized_pnl_usd=0.0,
                total_fees_usd=float(
                    self._decimal(
                        account.total_fees_usd
                    )
                    + fee
                ),
                equity_usd=float(
                    new_cash
                    + new_reserved
                ),
            )
        )
        slippage_usd = (
            abs(
                fill_price
                - reference_price
            )
            * quantity
        )
        order = (
            self.repository.create_order(
                PaperTradingOrderCreate(
                    user_id=bot.user_id,
                    trading_bot_id=bot.id,
                    paper_account_id=(
                        account.id
                    ),
                    paper_position_id=(
                        position.id
                    ),
                    symbol=bot.symbol,
                    category=bot.category,
                    side=action,
                    position_effect="CLOSE",
                    quantity=float(
                        quantity
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
                    fee_rate=float(
                        fee_rate
                    ),
                    fee_usd=float(fee),
                    slippage_rate=(
                        self.settings
                        .slippage_rate
                    ),
                    slippage_usd=float(
                        slippage_usd
                    ),
                    realized_pnl_usd=float(
                        realized_pnl
                    ),
                    decision_reason=(
                        decision.reason
                    ),
                    filled_at=now,
                ),
                commit=False,
            )
        )
        return self._commit_result(
            outcome="CLOSED",
            action=action,
            message=(
                f"Paper {position.side.lower()} "
                "position closed"
            ),
            account_created=(
                account_created
            ),
            account=account,
            position=position,
            order=order,
        )
    def execute(
        self,
        *,
        bot,
        decision: TradingBotStrategyDecision,
    ) -> PaperTradingExecutionResult:
        if not bot.paper_trading:
            raise ValueError(
                "Paper trading is disabled "
                "for this trading bot"
            )
        if decision.reference_price <= 0:
            raise ValueError(
                "Paper execution requires "
                "a positive reference price"
            )
        try:
            account, account_created = (
                self.repository
                .get_or_create_account(
                    PaperTradingAccountCreate(
                        user_id=bot.user_id,
                        trading_bot_id=bot.id,
                        currency=(
                            self.settings.currency
                        ),
                        initial_balance_usd=(
                            self.settings
                            .initial_balance_usd
                        ),
                    ),
                    commit=False,
                )
            )
            if account.status != "ACTIVE":
                raise ValueError(
                    "Paper trading account "
                    "is not active"
                )
            position = (
                self.repository
                .get_open_position(
                    paper_account_id=(
                        account.id
                    ),
                    symbol=bot.symbol,
                )
            )
            reference_price = self._decimal(
                decision.reference_price
            )
            self._mark_to_market(
                account=account,
                position=position,
                current_price=(
                    reference_price
                ),
            )
            if decision.action == "HOLD":
                return self._commit_result(
                    outcome="NO_ACTION",
                    action="HOLD",
                    message=(
                        "Paper position was "
                        "marked to market; no "
                        "order was created"
                    ),
                    account_created=(
                        account_created
                    ),
                    account=account,
                    position=position,
                )
            desired_side = (
                "LONG"
                if decision.action == "BUY"
                else "SHORT"
            )
            if (
                position is not None
                and position.side
                != desired_side
            ):
                return self._close_position(
                    bot=bot,
                    account=account,
                    position=position,
                    decision=decision,
                    account_created=(
                        account_created
                    ),
                )
            return self._open_or_increase(
                bot=bot,
                account=account,
                position=position,
                decision=decision,
                account_created=(
                    account_created
                ),
            )
        except Exception:
            self.db.rollback()
            raise
