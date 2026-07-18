from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from app.database.session import Base
class PortfolioSyncSnapshot(Base):
    __tablename__ = "portfolio_sync_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_id",
            "exchange_account_id",
            "fingerprint",
            name=(
                "uq_portfolio_sync_snapshot_"
                "fingerprint"
            ),
        ),
    )
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    portfolio_id = Column(
        Integer,
        ForeignKey("portfolios.id"),
        nullable=False,
        index=True,
    )
    exchange_account_id = Column(
        Integer,
        ForeignKey("exchange_accounts.id"),
        nullable=False,
        index=True,
    )
    exchange_name = Column(
        String(50),
        nullable=False,
        index=True,
    )
    account_type = Column(
        String(30),
        default="UNIFIED",
        nullable=False,
    )
    category = Column(
        String(20),
        default="linear",
        nullable=False,
    )
    settle_coin = Column(
        String(20),
        default="USDT",
        nullable=False,
    )
    status = Column(
        String(20),
        default="SUCCESS",
        nullable=False,
        index=True,
    )
    fingerprint = Column(
        String(64),
        nullable=False,
    )
    sync_version = Column(
        Integer,
        default=1,
        nullable=False,
    )
    total_equity_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    total_wallet_balance_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    total_available_balance_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    total_unrealized_pnl_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    total_realized_pnl_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    total_position_value_usd = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    coin_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    open_position_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    open_order_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    balance_payload = Column(
        JSON,
        default=dict,
        nullable=False,
    )
    positions_payload = Column(
        JSON,
        default=list,
        nullable=False,
    )
    orders_payload = Column(
        JSON,
        default=list,
        nullable=False,
    )
    error_message = Column(
        Text,
        nullable=True,
    )
    synced_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    owner = relationship("User")
    portfolio = relationship("Portfolio")
    exchange_account = relationship("ExchangeAccount")
