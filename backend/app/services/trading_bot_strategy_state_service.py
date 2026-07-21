from decimal import (
    Decimal,
)
from sqlalchemy.orm import (
    Session,
)
from app.repositories.paper_trading_repository import (
    PaperTradingRepository,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyPositionState,
    TradingBotStrategyState,
)
class TradingBotStrategyStateService:
    ORDER_LOOKBACK = 101
    def __init__(
        self,
        db: Session,
        *,
        repository: (
            PaperTradingRepository | None
        ) = None,
    ):
        self.db = db
        self.repository = (
            repository
            or PaperTradingRepository(db)
        )
    @staticmethod
    def _decimal(
        value,
    ) -> Decimal:
        return Decimal(str(value))
    @classmethod
    def _position_pnl(
        cls,
        *,
        side: str,
        quantity,
        average_entry_price,
        current_price,
    ) -> Decimal:
        quantity_value = cls._decimal(
            quantity
        )
        entry_value = cls._decimal(
            average_entry_price
        )
        current_value = cls._decimal(
            current_price
        )
        if side == "LONG":
            return (
                current_value
                - entry_value
            ) * quantity_value
        return (
            entry_value
            - current_value
        ) * quantity_value
    def build_from_paper_ledger(
        self,
        *,
        bot,
        current_price: float,
    ) -> TradingBotStrategyState:
        account = (
            self.repository
            .get_account_by_bot(
                user_id=bot.user_id,
                trading_bot_id=bot.id,
            )
        )
        if account is None:
            return TradingBotStrategyState()
        orders = self.repository.list_orders(
            paper_account_id=account.id,
            limit=self.ORDER_LOOKBACK,
            offset=0,
        )
        order_count = (
            self.repository.count_orders(
                paper_account_id=account.id
            )
        )
        completed_trade_count = (
            self.repository.count_positions(
                paper_account_id=account.id,
                status="CLOSED",
            )
        )
        position = (
            self.repository
            .get_open_position(
                paper_account_id=account.id,
                symbol=bot.symbol,
            )
        )
        last_order = (
            orders[0]
            if orders
            else None
        )
        position_state = None
        if position is not None:
            entry_orders = [
                order
                for order in orders
                if (
                    order.paper_position_id
                    == position.id
                    and order.position_effect
                    in {
                        "OPEN",
                        "INCREASE",
                    }
                )
            ]
            latest_entry = (
                entry_orders[0]
                if entry_orders
                else None
            )
            entry_count = max(
                len(entry_orders),
                1,
            )
            last_entry_price = (
                latest_entry.reference_price
                if latest_entry is not None
                else (
                    position
                    .average_entry_price
                )
            )
            last_entry_at = (
                latest_entry.filled_at
                if latest_entry is not None
                else position.opened_at
            )
            quantity = self._decimal(
                position.quantity
            )
            market_price = self._decimal(
                current_price
            )
            unrealized = (
                self._position_pnl(
                    side=position.side,
                    quantity=quantity,
                    average_entry_price=(
                        position
                        .average_entry_price
                    ),
                    current_price=market_price,
                )
            )
            position_state = (
                TradingBotStrategyPositionState(
                    side=position.side,
                    quantity=float(
                        quantity
                    ),
                    average_entry_price=(
                        position
                        .average_entry_price
                    ),
                    current_price=float(
                        market_price
                    ),
                    position_value_usd=float(
                        quantity
                        * market_price
                    ),
                    unrealized_pnl_usd=float(
                        unrealized
                    ),
                    entry_count=entry_count,
                    last_entry_price=(
                        last_entry_price
                    ),
                    opened_at=(
                        position.opened_at
                    ),
                    last_entry_at=(
                        last_entry_at
                    ),
                )
            )
        return TradingBotStrategyState(
            order_count=order_count,
            completed_trade_count=(
                completed_trade_count
            ),
            last_order_action=(
                last_order.side
                if last_order is not None
                else None
            ),
            last_order_reference_price=(
                last_order.reference_price
                if last_order is not None
                else None
            ),
            last_order_at=(
                last_order.filled_at
                if last_order is not None
                else None
            ),
            position=position_state,
        )
