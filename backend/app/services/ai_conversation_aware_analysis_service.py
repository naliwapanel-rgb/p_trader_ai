from app.models.user import User
from app.schemas.ai_assistant import (
    AIAnalysisResponse,
    AIAnalysisSection,
    AIAssistantRequest,
)
from app.schemas.ai_conversation import (
    AIConversationHistoryResponse,
)
from app.services.ai_contextual_analysis_service import (
    AIContextAwareAnalysisService,
)
from app.services.ai_conversation_service import (
    AIConversationService,
)
class AIConversationAwareAnalysisService:
    """
    Add recent, authenticated conversation
    history to deterministic contextual analysis.
    The service is read-only with respect to
    conversation history. Message persistence is
    still handled separately after analysis.
    """
    FOLLOW_UP_PREFIXES = (
        "and ",
        "also ",
        "continue",
        "what about",
        "how about",
        "explain that",
        "explain this",
        "why is that",
        "why did",
        "can you expand",
        "tell me more",
        "use that",
        "based on that",
    )
    FOLLOW_UP_TERMS = {
        "it",
        "that",
        "this",
        "those",
        "these",
        "again",
        "previous",
        "earlier",
        "continue",
    }
    def __init__(
        self,
        *,
        contextual_service: (
            AIContextAwareAnalysisService
        ),
        conversation_service: (
            AIConversationService
        ),
    ):
        self.contextual_service = (
            contextual_service
        )
        self.conversation_service = (
            conversation_service
        )
    @staticmethod
    def _truncate(
        value: str,
        limit: int,
    ) -> str:
        normalized = " ".join(
            value.split()
        )
        if len(normalized) <= limit:
            return normalized
        return (
            normalized[
                : limit - 3
            ].rstrip()
            + "..."
        )
    @classmethod
    def _looks_like_follow_up(
        cls,
        question: str,
    ) -> bool:
        normalized = (
            question.strip().lower()
        )
        if normalized.startswith(
            cls.FOLLOW_UP_PREFIXES
        ):
            return True
        words = {
            word.strip(
                ".,?!:;()[]{}"
            )
            for word in normalized.split()
        }
        return bool(
            words & cls.FOLLOW_UP_TERMS
        )
    @staticmethod
    def _recent_messages(
        history: AIConversationHistoryResponse,
    ):
        return history.messages
    def _conversation_section(
        self,
        history: AIConversationHistoryResponse,
    ) -> AIAnalysisSection:
        messages = self._recent_messages(
            history
        )
        user_messages = [
            message
            for message in messages
            if message.role == "USER"
        ]
        assistant_messages = [
            message
            for message in messages
            if message.role == "ASSISTANT"
        ]
        bullets = []
        if user_messages:
            bullets.append(
                "Previous user message: "
                + self._truncate(
                    user_messages[-1].content,
                    300,
                )
            )
        if assistant_messages:
            bullets.append(
                "Previous assistant response: "
                + self._truncate(
                    assistant_messages[
                        -1
                    ].content,
                    400,
                )
            )
        return AIAnalysisSection(
            title="Conversation History",
            summary=(
                "Recent messages from the "
                "authenticated, user-owned "
                "conversation were reviewed."
            ),
            bullet_points=bullets,
            metrics={
                "conversation_id": (
                    history.conversation.id
                ),
                "total_message_count": (
                    history.conversation
                    .message_count
                ),
                "loaded_message_count": (
                    len(messages)
                ),
                "loaded_user_messages": (
                    len(user_messages)
                ),
                (
                    "loaded_assistant_"
                    "messages"
                ): len(
                    assistant_messages
                ),
            },
        )
    def _follow_up_answer(
        self,
        *,
        request: AIAssistantRequest,
        result: AIAnalysisResponse,
        history: AIConversationHistoryResponse,
    ) -> str:
        if not self._looks_like_follow_up(
            request.question
        ):
            return result.answer
        assistant_messages = [
            message
            for message in history.messages
            if message.role == "ASSISTANT"
        ]
        if not assistant_messages:
            return result.answer
        previous_context = self._truncate(
            assistant_messages[-1].content,
            240,
        )
        return (
            "This request was treated as a "
            "follow-up to the recent "
            "conversation. Previous assistant "
            f"context: {previous_context} "
            f"{result.answer}"
        )
    @staticmethod
    def _data_sources(
        result: AIAnalysisResponse,
    ) -> list:
        sources = list(
            result.metadata.data_sources
        )
        if (
            "CONVERSATION_HISTORY"
            not in sources
        ):
            sources.append(
                "CONVERSATION_HISTORY"
            )
        return sources
    def analyze(
        self,
        *,
        current_user: User,
        request: AIAssistantRequest,
    ) -> AIAnalysisResponse:
        history = None
        if (
            request.conversation_id
            is not None
            and request
            .include_conversation_history
        ):
            history = (
                self.conversation_service
                .get_history(
                    current_user=current_user,
                    conversation_id=(
                        request
                        .conversation_id
                    ),
                    limit=(
                        request
                        .conversation_history_limit
                    ),
                    offset=0,
                )
            )
        result = (
            self.contextual_service.analyze(
                current_user=current_user,
                request=request,
            )
        )
        if history is None:
            return result
        metadata = (
            result.metadata.model_copy(
                update={
                    "data_sources": (
                        self._data_sources(
                            result
                        )
                    ),
                    "confidence_score": min(
                        1.0,
                        (
                            result.metadata
                            .confidence_score
                            + 0.05
                        ),
                    ),
                    "advisory_only": True,
                    "execution_enabled": False,
                }
            )
        )
        return result.model_copy(
            update={
                "answer": (
                    self._follow_up_answer(
                        request=request,
                        result=result,
                        history=history,
                    )
                ),
                "sections": [
                    self._conversation_section(
                        history
                    ),
                    *result.sections,
                ],
                "metadata": metadata,
                "execution_allowed": False,
            }
        )
