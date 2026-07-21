from datetime import (
    UTC,
    datetime,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.orm import (
    Session,
)
from app.models.paper_trading import (
    PaperTradingAccount,
    PaperTradingOrder,
    PaperTradingPosition,
)
from app.schemas.paper_trading import (
    PaperTradingAccountCreate,
    PaperTradingOrderCreate,
    PaperTradingPositionCreate,
)
class PaperTradingRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
    def _persist(
        self,
        instance,
        *,
        commit: bool,
    ):
        if commit:
            self.db.commit()
            self.db.refresh(instance)
        else:
            self.db.flush()
        return instance
    def get_account_by_bot(
        self,
        *,
        user_id: int,
        trading_bot_id: int,
    ) -> PaperTradingAccount | None:
        return (
            self.db
            .query(PaperTradingAccount)
            .filter(
                PaperTradingAccount.user_id
                == user_id,
                (
                    PaperTradingAccount
                    .trading_bot_id
                    == trading_bot_id
                ),
            )
            .first()
        )
    def create_account(
        self,
        data: PaperTradingAccountCreate,
        *,
        commit: bool = True,
    ) -> PaperTradingAccount:
        account = PaperTradingAccount(
            user_id=data.user_id,
            trading_bot_id=(
                data.trading_bot_id
            ),
            currency=data.currency,
            initial_balance_usd=(
                data.initial_balance_usd
            ),
            cash_balance_usd=(
                data.initial_balance_usd
            ),
            reserved_balance_usd=0.0,
            equity_usd=(
                data.initial_balance_usd
            ),
            realized_pnl_usd=0.0,
            unrealized_pnl_usd=0.0,
            total_fees_usd=0.0,
            status="ACTIVE",
        )
        self.db.add(account)
        return self._persist(
            account,
            commit=commit,
        )
    def get_or_create_account(
        self,
        data: PaperTradingAccountCreate,
        *,
        commit: bool = True,
    ) -> tuple[
        PaperTradingAccount,
        bool,
    ]:
        existing = self.get_account_by_bot(
            user_id=data.user_id,
            trading_bot_id=(
                data.trading_bot_id
            ),
        )
        if existing is not None:
            return existing, False
        if not commit:
            return (
                self.create_account(
                    data,
                    commit=False,
                ),
                True,
            )
        try:
            return (
                self.create_account(
                    data,
                    commit=True,
                ),
                True,
            )
        except IntegrityError:
            self.db.rollback()
            existing = (
                self.get_account_by_bot(
                    user_id=data.user_id,
                    trading_bot_id=(
                        data.trading_bot_id
                    ),
                )
            )
            if existing is None:
                raise
            return existing, False
    def save_account(
        self,
        *,
        account: PaperTradingAccount,
        commit: bool = True,
        **fields,
    ) -> PaperTradingAccount:
        for key, value in fields.items():
            setattr(
                account,
                key,
                value,
            )
        account.updated_at = datetime.now(
            UTC
        )
        return self._persist(
            account,
            commit=commit,
        )
    def get_open_position(
        self,
        *,
        paper_account_id: int,
        symbol: str,
    ) -> PaperTradingPosition | None:
        normalized_symbol = (
            symbol.strip().upper()
        )
        return (
            self.db
            .query(PaperTradingPosition)
            .filter(
                (
                    PaperTradingPosition
                    .paper_account_id
                    == paper_account_id
                ),
                (
                    PaperTradingPosition.symbol
                    == normalized_symbol
                ),
                (
                    PaperTradingPosition.status
                    == "OPEN"
                ),
            )
            .order_by(
                PaperTradingPosition.id.desc()
            )
            .first()
        )
    def create_position(
        self,
        data: PaperTradingPositionCreate,
        *,
        commit: bool = True,
    ) -> PaperTradingPosition:
        position = PaperTradingPosition(
            status="OPEN",
            **data.model_dump(),
        )
        self.db.add(position)
        return self._persist(
            position,
            commit=commit,
        )
    def save_position(
        self,
        *,
        position: PaperTradingPosition,
        commit: bool = True,
        **fields,
    ) -> PaperTradingPosition:
        for key, value in fields.items():
            setattr(
                position,
                key,
                value,
            )
        position.updated_at = datetime.now(
            UTC
        )
        return self._persist(
            position,
            commit=commit,
        )
    def list_positions(
        self,
        *,
        paper_account_id: int,
        status: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[PaperTradingPosition]:
        query = (
            self.db
            .query(PaperTradingPosition)
            .filter(
                (
                    PaperTradingPosition
                    .paper_account_id
                    == paper_account_id
                )
            )
        )
        if status is not None:
            query = query.filter(
                PaperTradingPosition.status
                == status
            )
        query = (
            query
            .order_by(
                (
                    PaperTradingPosition
                    .created_at
                    .desc()
                ),
                PaperTradingPosition.id.desc(),
            )
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()
    def count_positions(
        self,
        *,
        paper_account_id: int,
        status: str | None = None,
    ) -> int:
        query = (
            self.db
            .query(PaperTradingPosition)
            .filter(
                (
                    PaperTradingPosition
                    .paper_account_id
                    == paper_account_id
                )
            )
        )
        if status is not None:
            query = query.filter(
                PaperTradingPosition.status
                == status
            )
        return query.count()
    def create_order(
        self,
        data: PaperTradingOrderCreate,
        *,
        commit: bool = True,
    ) -> PaperTradingOrder:
        order = PaperTradingOrder(
            status="FILLED",
            **data.model_dump(),
        )
        self.db.add(order)
        return self._persist(
            order,
            commit=commit,
        )
    def list_orders(
        self,
        *,
        paper_account_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PaperTradingOrder]:
        return (
            self.db
            .query(PaperTradingOrder)
            .filter(
                (
                    PaperTradingOrder
                    .paper_account_id
                    == paper_account_id
                )
            )
            .order_by(
                PaperTradingOrder.created_at.desc(),
                PaperTradingOrder.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
    def count_orders(
        self,
        *,
        paper_account_id: int,
    ) -> int:
        return (
            self.db
            .query(PaperTradingOrder)
            .filter(
                (
                    PaperTradingOrder
                    .paper_account_id
                    == paper_account_id
                )
            )
            .count()
        )
