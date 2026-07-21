from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
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
class TradingBot(Base):
    __tablename__ = "trading_bots"
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
    exchange_account_id = Column(
        Integer,
        ForeignKey(
            "exchange_accounts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    name = Column(
        String(150),
        nullable=False,
    )
    description = Column(
        Text,
        nullable=True,
    )
    strategy_type = Column(
        String(50),
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
        default="linear",
        nullable=False,
    )
    timeframe = Column(
        String(20),
        default="5m",
        nullable=False,
        index=True,
    )
    status = Column(
        String(20),
        default="DRAFT",
        nullable=False,
        index=True,
    )
    paper_trading = Column(
        Boolean,
        default=True,
        nullable=False,
    )
    dry_run = Column(
        Boolean,
        default=True,
        nullable=False,
    )
    risk_per_trade_percent = Column(
        Float,
        default=1.0,
        nullable=False,
    )
    max_position_value_usd = Column(
        Float,
        default=25.0,
        nullable=False,
    )
    max_daily_loss_percent = Column(
        Float,
        default=3.0,
        nullable=False,
    )
    max_drawdown_percent = Column(
        Float,
        default=10.0,
        nullable=False,
    )
    stop_loss_percent = Column(
        Float,
        nullable=True,
    )
    take_profit_percent = Column(
        Float,
        nullable=True,
    )
    strategy_config = Column(
        JSON,
        default=dict,
        nullable=False,
    )
    last_error = Column(
        Text,
        nullable=True,
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    stopped_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_run_at = Column(
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
    exchange_account = relationship(
        "ExchangeAccount",
    )
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "name",
            name=(
                "uq_trading_bots_"
                "user_name"
            ),
        ),
        CheckConstraint(
            "paper_trading OR dry_run",
            name=(
                "ck_trading_bots_"
                "execution_safety"
            ),
        ),
        CheckConstraint(
            (
                "risk_per_trade_percent "
                "> 0"
            ),
            name=(
                "ck_trading_bots_"
                "risk_positive"
            ),
        ),
        CheckConstraint(
            (
                "max_position_value_usd "
                "> 0"
            ),
            name=(
                "ck_trading_bots_"
                "position_value_positive"
            ),
        ),
        CheckConstraint(
            (
                "risk_per_trade_percent "
                "<= max_daily_loss_percent"
            ),
            name=(
                "ck_trading_bots_"
                "risk_daily_loss"
            ),
        ),
        CheckConstraint(
            (
                "max_daily_loss_percent "
                "<= max_drawdown_percent"
            ),
            name=(
                "ck_trading_bots_"
                "daily_loss_drawdown"
            ),
        ),
        CheckConstraint(
            (
                "stop_loss_percent IS NULL "
                "OR stop_loss_percent > 0"
            ),
            name=(
                "ck_trading_bots_"
                "stop_loss_positive"
            ),
        ),
        CheckConstraint(
            (
                "take_profit_percent IS NULL "
                "OR take_profit_percent > 0"
            ),
            name=(
                "ck_trading_bots_"
                "take_profit_positive"
            ),
        ),
        Index(
            "ix_trading_bots_user_status",
            "user_id",
            "status",
        ),
        Index(
            "ix_trading_bots_user_updated",
            "user_id",
            "updated_at",
        ),
    )
