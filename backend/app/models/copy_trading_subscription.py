from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
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
class CopyTradingSubscription(Base):
    __tablename__ = (
        "copy_trading_subscriptions"
    )
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    follower_user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    source_template_id = Column(
        Integer,
        ForeignKey(
            "strategy_templates.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    follower_bot_id = Column(
        Integer,
        ForeignKey(
            "trading_bots.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    status = Column(
        String(20),
        default="ACTIVE",
        nullable=False,
        index=True,
    )
    execution_mode = Column(
        String(20),
        default="PAPER_ONLY",
        nullable=False,
    )
    subscribed_template_version = Column(
        Integer,
        nullable=False,
    )
    last_error = Column(
        Text,
        nullable=True,
    )
    last_mirrored_at = Column(
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
    follower = relationship(
        "User",
    )
    source_template = relationship(
        "StrategyTemplate",
    )
    follower_bot = relationship(
        "TradingBot",
    )
    __table_args__ = (
        UniqueConstraint(
            "follower_bot_id",
            name=(
                "uq_copy_trading_"
                "follower_bot"
            ),
        ),
        CheckConstraint(
            (
                "status IN "
                "('ACTIVE', 'PAUSED', "
                "'STOPPED')"
            ),
            name=(
                "ck_copy_trading_"
                "status"
            ),
        ),
        CheckConstraint(
            (
                "execution_mode = "
                "'PAPER_ONLY'"
            ),
            name=(
                "ck_copy_trading_"
                "paper_only"
            ),
        ),
        CheckConstraint(
            (
                "subscribed_template_version "
                ">= 1"
            ),
            name=(
                "ck_copy_trading_"
                "template_version"
            ),
        ),
        Index(
            (
                "ix_copy_trading_"
                "follower_status"
            ),
            "follower_user_id",
            "status",
        ),
        Index(
            (
                "ix_copy_trading_"
                "template_status"
            ),
            "source_template_id",
            "status",
        ),
        Index(
            (
                "ix_copy_trading_"
                "follower_updated"
            ),
            "follower_user_id",
            "updated_at",
        ),
    )
