from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database.session import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(30), nullable=False, index=True)
    exchange = Column(String(50), default="BINANCE", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "symbol",
            "exchange",
            name="uq_user_symbol_exchange",
        ),
    )