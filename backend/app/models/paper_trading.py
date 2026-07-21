from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    relationship,
)
from app.database.session import (
    Base,
)
class PaperTradingAccount(Base):
    __tablename__ = (
        "paper_trading_accounts"
    )
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    trading_bot_id = Column(
        Integer,
        ForeignKey(
            "trading_bots.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    currency = Column(
        String(20),
        default="USDT",
        nullable=False,
    )
    initial_balance_usd = Column(
        Float,
        default=10000.0,
        nullable=False,
    )
    cash_balance_usd = Column(
        Float,
        default=10000.0,
        nullable=False,
    )
    reserved_balance_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    equity_usd = Column(
        Float,
        default=10000.0,
        nullable=False,
    )
    realized_pnl_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    unrealized_pnl_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    total_fees_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    status = Column(
        String(20),
        default="ACTIVE",
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
    owner = relationship(
        "User",
    )
    trading_bot = relationship(
        "TradingBot",
    )
    __table_args__ = (
        UniqueConstraint(
            "trading_bot_id",
            name=(
                "uq_paper_accounts_"
                "trading_bot"
            ),
        ),
        CheckConstraint(
            "initial_balance_usd > 0",
            name=(
                "ck_paper_accounts_"
                "initial_positive"
            ),
        ),
        CheckConstraint(
            "cash_balance_usd >= 0",
            name=(
                "ck_paper_accounts_"
                "cash_nonnegative"
            ),
        ),
        CheckConstraint(
            "reserved_balance_usd >= 0",
            name=(
                "ck_paper_accounts_"
                "reserved_nonnegative"
            ),
        ),
        CheckConstraint(
            "total_fees_usd >= 0",
            name=(
                "ck_paper_accounts_"
                "fees_nonnegative"
            ),
        ),
        Index(
            "ix_paper_accounts_user_status",
            "user_id",
            "status",
        ),
    )
class PaperTradingPosition(Base):
    __tablename__ = (
        "paper_trading_positions"
    )
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    trading_bot_id = Column(
        Integer,
        ForeignKey(
            "trading_bots.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    paper_account_id = Column(
        Integer,
        ForeignKey(
            "paper_trading_accounts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    symbol = Column(
        String(30),
        nullable=False,
        index=True,
    )
    category = Column(
        String(20),
        nullable=False,
    )
    side = Column(
        String(10),
        nullable=False,
    )
    status = Column(
        String(20),
        default="OPEN",
        nullable=False,
        index=True,
    )
    quantity = Column(
        Float,
        nullable=False,
    )
    average_entry_price = Column(
        Float,
        nullable=False,
    )
    current_price = Column(
        Float,
        nullable=False,
    )
    position_value_usd = Column(
        Float,
        nullable=False,
    )
    reserved_margin_usd = Column(
        Float,
        nullable=False,
    )
    unrealized_pnl_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    realized_pnl_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    total_fees_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    opened_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )
    closed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )
    owner = relationship(
        "User",
    )
    trading_bot = relationship(
        "TradingBot",
    )
    paper_account = relationship(
        "PaperTradingAccount",
    )
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name=(
                "ck_paper_positions_"
                "quantity_positive"
            ),
        ),
        CheckConstraint(
            "average_entry_price > 0",
            name=(
                "ck_paper_positions_"
                "entry_positive"
            ),
        ),
        CheckConstraint(
            "current_price >= 0",
            name=(
                "ck_paper_positions_"
                "current_nonnegative"
            ),
        ),
        CheckConstraint(
            "position_value_usd >= 0",
            name=(
                "ck_paper_positions_"
                "value_nonnegative"
            ),
        ),
        CheckConstraint(
            "reserved_margin_usd >= 0",
            name=(
                "ck_paper_positions_"
                "margin_nonnegative"
            ),
        ),
        CheckConstraint(
            "total_fees_usd >= 0",
            name=(
                "ck_paper_positions_"
                "fees_nonnegative"
            ),
        ),
        Index(
            "ix_paper_positions_account_status",
            "paper_account_id",
            "status",
        ),
        Index(
            "ix_paper_positions_bot_symbol",
            "trading_bot_id",
            "symbol",
        ),
    )
class PaperTradingOrder(Base):
    __tablename__ = (
        "paper_trading_orders"
    )
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    trading_bot_id = Column(
        Integer,
        ForeignKey(
            "trading_bots.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    paper_account_id = Column(
        Integer,
        ForeignKey(
            "paper_trading_accounts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    paper_position_id = Column(
        Integer,
        ForeignKey(
            "paper_trading_positions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    symbol = Column(
        String(30),
        nullable=False,
        index=True,
    )
    category = Column(
        String(20),
        nullable=False,
    )
    side = Column(
        String(10),
        nullable=False,
    )
    position_effect = Column(
        String(20),
        nullable=False,
    )
    status = Column(
        String(20),
        default="FILLED",
        nullable=False,
        index=True,
    )
    quantity = Column(
        Float,
        nullable=False,
    )
    reference_price = Column(
        Float,
        nullable=False,
    )
    fill_price = Column(
        Float,
        nullable=False,
    )
    gross_value_usd = Column(
        Float,
        nullable=False,
    )
    fee_rate = Column(
        Float,
        nullable=False,
    )
    fee_usd = Column(
        Float,
        nullable=False,
    )
    slippage_rate = Column(
        Float,
        nullable=False,
    )
    slippage_usd = Column(
        Float,
        nullable=False,
    )
    realized_pnl_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    decision_reason = Column(
        Text,
        nullable=True,
    )
    filled_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    owner = relationship(
        "User",
    )
    trading_bot = relationship(
        "TradingBot",
    )
    paper_account = relationship(
        "PaperTradingAccount",
    )
    paper_position = relationship(
        "PaperTradingPosition",
    )
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name=(
                "ck_paper_orders_"
                "quantity_positive"
            ),
        ),
        CheckConstraint(
            "reference_price > 0",
            name=(
                "ck_paper_orders_"
                "reference_positive"
            ),
        ),
        CheckConstraint(
            "fill_price > 0",
            name=(
                "ck_paper_orders_"
                "fill_positive"
            ),
        ),
        CheckConstraint(
            "gross_value_usd > 0",
            name=(
                "ck_paper_orders_"
                "gross_positive"
            ),
        ),
        CheckConstraint(
            "fee_rate >= 0",
            name=(
                "ck_paper_orders_"
                "fee_rate_nonnegative"
            ),
        ),
        CheckConstraint(
            "fee_usd >= 0",
            name=(
                "ck_paper_orders_"
                "fee_nonnegative"
            ),
        ),
        CheckConstraint(
            "slippage_rate >= 0",
            name=(
                "ck_paper_orders_"
                "slippage_rate_nonnegative"
            ),
        ),
        CheckConstraint(
            "slippage_usd >= 0",
            name=(
                "ck_paper_orders_"
                "slippage_nonnegative"
            ),
        ),
        Index(
            "ix_paper_orders_account_created",
            "paper_account_id",
            "created_at",
        ),
        Index(
            "ix_paper_orders_bot_symbol",
            "trading_bot_id",
            "symbol",
        ),
    )
