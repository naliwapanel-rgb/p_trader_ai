from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from app.models.ai_conversation import (
    AIConversation,
)
from app.models.user import User
from app.repositories.ai_conversation_repository import (
    AIConversationRepository,
)
from app.schemas.ai_conversation import (
    AIConversationCreateRequest,
    AIConversationExchangeCreate,
    AIConversationExchangeResponse,
    AIConversationHistoryResponse,
    AIConversationResponse,
    AIConversationSummaryResponse,
    AIConversationUpdateRequest,
    AIMessageResponse,
)
class AIConversationService:
    DEFAULT_TITLE = "New conversation"
    def __init__(
        self,
        db: Session | None,
        *,
        repository: (
            AIConversationRepository
            | None
        ) = None,
    ):
        self.repository = (
            repository
            or AIConversationRepository(db)
        )
    @staticmethod
    def _generated_title(
        content: str,
    ) -> str:
        first_line = (
            content.strip()
            .splitlines()[0]
            .strip()
        )
        if len(first_line) <= 80:
            return first_line
        return (
            first_line[:77].rstrip()
            + "..."
        )
    def _get_owned_conversation(
        self,
        *,
        current_user: User,
        conversation_id: int,
    ) -> AIConversation:
        conversation = (
            self.repository
            .get_by_id_and_user(
                conversation_id=(
                    conversation_id
                ),
                user_id=current_user.id,
            )
        )
        if conversation is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "AI conversation not found"
                ),
            )
        return conversation
    def _summary(
        self,
        *,
        conversation: AIConversation,
        user_id: int,
    ) -> AIConversationSummaryResponse:
        message_count = (
            self.repository
            .count_messages(
                conversation_id=(
                    conversation.id
                ),
                user_id=user_id,
            )
        )
        last_message = (
            self.repository
            .get_last_message(
                conversation_id=(
                    conversation.id
                ),
                user_id=user_id,
            )
        )
        base = (
            AIConversationResponse
            .model_validate(conversation)
        )
        return AIConversationSummaryResponse(
            **base.model_dump(),
            message_count=message_count,
            last_message_at=(
                last_message.created_at
                if last_message is not None
                else None
            ),
        )
    def create_conversation(
        self,
        *,
        current_user: User,
        data: AIConversationCreateRequest,
    ) -> AIConversationSummaryResponse:
        conversation = (
            self.repository
            .create_conversation(
                user_id=current_user.id,
                title=(
                    data.title
                    or self.DEFAULT_TITLE
                ),
            )
        )
        return self._summary(
            conversation=conversation,
            user_id=current_user.id,
        )
    def list_conversations(
        self,
        *,
        current_user: User,
        limit: int = 50,
        offset: int = 0,
    ) -> list[
        AIConversationSummaryResponse
    ]:
        conversations = (
            self.repository.list_by_user(
                user_id=current_user.id,
                limit=limit,
                offset=offset,
            )
        )
        return [
            self._summary(
                conversation=conversation,
                user_id=current_user.id,
            )
            for conversation
            in conversations
        ]
    def get_history(
        self,
        *,
        current_user: User,
        conversation_id: int,
        limit: int = 200,
        offset: int = 0,
    ) -> AIConversationHistoryResponse:
        conversation = (
            self._get_owned_conversation(
                current_user=current_user,
                conversation_id=(
                    conversation_id
                ),
            )
        )
        messages = (
            self.repository.list_messages(
                conversation_id=(
                    conversation.id
                ),
                user_id=current_user.id,
                limit=limit,
                offset=offset,
            )
        )
        return AIConversationHistoryResponse(
            conversation=self._summary(
                conversation=conversation,
                user_id=current_user.id,
            ),
            messages=[
                AIMessageResponse
                .model_validate(message)
                for message in messages
            ],
        )
    def update_conversation(
        self,
        *,
        current_user: User,
        conversation_id: int,
        data: AIConversationUpdateRequest,
    ) -> AIConversationSummaryResponse:
        conversation = (
            self._get_owned_conversation(
                current_user=current_user,
                conversation_id=(
                    conversation_id
                ),
            )
        )
        conversation = (
            self.repository
            .update_conversation(
                conversation=conversation,
                title=data.title,
                status=data.status,
            )
        )
        return self._summary(
            conversation=conversation,
            user_id=current_user.id,
        )
    def append_exchange(
        self,
        *,
        current_user: User,
        conversation_id: int,
        data: AIConversationExchangeCreate,
    ) -> AIConversationExchangeResponse:
        conversation = (
            self._get_owned_conversation(
                current_user=current_user,
                conversation_id=(
                    conversation_id
                ),
            )
        )
        if conversation.status != "ACTIVE":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "AI conversation is archived"
                ),
            )
        generated_title = (
            self._generated_title(
                data.user_content
            )
            if conversation.title
            == self.DEFAULT_TITLE
            else None
        )
        (
            user_message,
            assistant_message,
        ) = self.repository.append_exchange(
            conversation=conversation,
            user_id=current_user.id,
            user_content=(
                data.user_content
            ),
            assistant_content=(
                data.assistant_content
            ),
            analysis_type=(
                data.analysis_type
            ),
            user_metadata=(
                data.user_metadata
            ),
            assistant_metadata=(
                data.assistant_metadata
            ),
            generated_title=(
                generated_title
            ),
        )
        return AIConversationExchangeResponse(
            conversation=self._summary(
                conversation=conversation,
                user_id=current_user.id,
            ),
            user_message=(
                AIMessageResponse
                .model_validate(user_message)
            ),
            assistant_message=(
                AIMessageResponse
                .model_validate(
                    assistant_message
                )
            ),
        )
    def delete_conversation(
        self,
        *,
        current_user: User,
        conversation_id: int,
    ) -> None:
        conversation = (
            self._get_owned_conversation(
                current_user=current_user,
                conversation_id=(
                    conversation_id
                ),
            )
        )
        self.repository.delete_conversation(
            conversation
        )
