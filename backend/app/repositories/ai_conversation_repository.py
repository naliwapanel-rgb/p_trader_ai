from datetime import (
    UTC,
    datetime,
)
from typing import Any
from sqlalchemy import (
    func,
)
from sqlalchemy.orm import Session
from app.models.ai_conversation import (
    AIConversation,
    AIMessage,
)
class AIConversationRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
    def create_conversation(
        self,
        *,
        user_id: int,
        title: str,
    ) -> AIConversation:
        conversation = AIConversation(
            user_id=user_id,
            title=title,
            status="ACTIVE",
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    def get_by_id_and_user(
        self,
        *,
        conversation_id: int,
        user_id: int,
    ) -> AIConversation | None:
        return (
            self.db.query(
                AIConversation
            )
            .filter(
                AIConversation.id
                == conversation_id,
                AIConversation.user_id
                == user_id,
            )
            .first()
        )
    def list_by_user(
        self,
        *,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AIConversation]:
        return (
            self.db.query(
                AIConversation
            )
            .filter(
                AIConversation.user_id
                == user_id
            )
            .order_by(
                AIConversation
                .updated_at
                .desc(),
                AIConversation.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
    def update_conversation(
        self,
        *,
        conversation: AIConversation,
        title: str | None = None,
        status: str | None = None,
    ) -> AIConversation:
        if title is not None:
            conversation.title = title
        if status is not None:
            conversation.status = status
        conversation.updated_at = (
            datetime.now(UTC)
        )
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    def count_messages(
        self,
        *,
        conversation_id: int,
        user_id: int,
    ) -> int:
        return int(
            self.db.query(
                func.count(AIMessage.id)
            )
            .filter(
                AIMessage.conversation_id
                == conversation_id,
                AIMessage.user_id
                == user_id,
            )
            .scalar()
            or 0
        )
    def get_last_message(
        self,
        *,
        conversation_id: int,
        user_id: int,
    ) -> AIMessage | None:
        return (
            self.db.query(AIMessage)
            .filter(
                AIMessage.conversation_id
                == conversation_id,
                AIMessage.user_id
                == user_id,
            )
            .order_by(
                AIMessage.id.desc()
            )
            .first()
        )
    def list_messages(
        self,
        *,
        conversation_id: int,
        user_id: int,
        limit: int = 200,
        offset: int = 0,
    ) -> list[AIMessage]:
        return (
            self.db.query(AIMessage)
            .filter(
                AIMessage.conversation_id
                == conversation_id,
                AIMessage.user_id
                == user_id,
            )
            .order_by(
                AIMessage.id.asc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
    def append_exchange(
        self,
        *,
        conversation: AIConversation,
        user_id: int,
        user_content: str,
        assistant_content: str,
        analysis_type: str,
        user_metadata: dict[str, Any],
        assistant_metadata: dict[
            str,
            Any,
        ],
        generated_title: str | None = None,
    ) -> tuple[
        AIMessage,
        AIMessage,
    ]:
        if (
            generated_title is not None
            and conversation.title
            == "New conversation"
        ):
            conversation.title = (
                generated_title
            )
        user_message = AIMessage(
            conversation_id=conversation.id,
            user_id=user_id,
            role="USER",
            content=user_content,
            analysis_type=analysis_type,
            message_metadata=user_metadata,
        )
        assistant_message = AIMessage(
            conversation_id=conversation.id,
            user_id=user_id,
            role="ASSISTANT",
            content=assistant_content,
            analysis_type=analysis_type,
            message_metadata=(
                assistant_metadata
            ),
        )
        conversation.updated_at = (
            datetime.now(UTC)
        )
        self.db.add_all([
            user_message,
            assistant_message,
        ])
        self.db.commit()
        self.db.refresh(conversation)
        self.db.refresh(user_message)
        self.db.refresh(
            assistant_message
        )
        return (
            user_message,
            assistant_message,
        )
    def delete_conversation(
        self,
        conversation: AIConversation,
    ) -> None:
        (
            self.db.query(AIMessage)
            .filter(
                AIMessage.conversation_id
                == conversation.id
            )
            .delete(
                synchronize_session=False
            )
        )
        self.db.delete(conversation)
        self.db.commit()
