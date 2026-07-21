from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    relationship,
)
from app.database.session import Base
class AIConversation(Base):
    __tablename__ = "ai_conversations"
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
    title = Column(
        String(200),
        default="New conversation",
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
    messages = relationship(
        "AIMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AIMessage.id",
    )
    __table_args__ = (
        Index(
            "ix_ai_conversations_user_updated",
            "user_id",
            "updated_at",
        ),
    )
class AIMessage(Base):
    __tablename__ = "ai_messages"
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )
    conversation_id = Column(
        Integer,
        ForeignKey(
            "ai_conversations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
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
    role = Column(
        String(20),
        nullable=False,
        index=True,
    )
    content = Column(
        Text,
        nullable=False,
    )
    analysis_type = Column(
        String(30),
        nullable=True,
        index=True,
    )
    message_metadata = Column(
        JSON,
        default=dict,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    conversation = relationship(
        "AIConversation",
        back_populates="messages",
    )
    owner = relationship(
        "User",
    )
    __table_args__ = (
        Index(
            "ix_ai_messages_conversation_created",
            "conversation_id",
            "created_at",
        ),
    )
