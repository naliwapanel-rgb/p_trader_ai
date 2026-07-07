from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database.session import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    symbol = Column(String(30), nullable=False, index=True)
    exchange = Column(String(50), default="BINANCE", nullable=False)

    alert_type = Column(String(50), nullable=False)
    target_value = Column(Float, nullable=False)

    is_enabled = Column(Boolean, default=True, nullable=False)
    triggered = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    owner = relationship("User")