from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    Mock,
)
import pytest
from fastapi import HTTPException
from app.schemas.ai_assistant import (
    AIAnalysisMetadata,
    AIAnalysisResponse,
    AIAnalysisSection,
    AIAssistantRequest,
)
from app.schemas.ai_conversation import (
    AIConversationHistoryResponse,
    AIConversationSummaryResponse,
    AIMessageResponse,
)
from app.services.ai_conversation_aware_analysis_service import (
    AIConversationAwareAnalysisService,
)
def _now():
    return datetime.now(UTC)
def _response():
    return AIAnalysisResponse(
        status="SUCCESS",
        answer="Current analysis completed.",
        sections=[
            AIAnalysisSection(
                title="Current Analysis",
                summary=(
                    "Current deterministic "
                    "analysis."
                ),
            ),
        ],
        warnings=[],
        metadata=AIAnalysisMetadata(
            analysis_type="GENERAL",
            generated_at_ms=100,
            confidence_score=0.8,
            data_sources=[
                "USER_QUERY",
            ],
            provider="DETERMINISTIC",
            advisory_only=True,
            execution_enabled=False,
        ),
        execution_allowed=False,
    )
def _message(
    *,
    message_id,
    role,
    content,
):
    return AIMessageResponse(
        id=message_id,
        conversation_id=10,
        user_id=7,
        role=role,
        content=content,
        analysis_type="GENERAL",
        message_metadata={},
        created_at=_now(),
    )
def _history():
    return AIConversationHistoryResponse(
        conversation=(
            AIConversationSummaryResponse(
                id=10,
                user_id=7,
                title="Trading discussion",
                status="ACTIVE",
                created_at=_now(),
                updated_at=_now(),
                message_count=4,
                last_message_at=_now(),
            )
        ),
        messages=[
            _message(
                message_id=1,
                role="USER",
                content=(
                    "Review my portfolio."
                ),
            ),
            _message(
                message_id=2,
                role="ASSISTANT",
                content=(
                    "Your portfolio is "
                    "concentrated in BTC."
                ),
            ),
            _message(
                message_id=3,
                role="USER",
                content=(
                    "Explain the risk."
                ),
            ),
            _message(
                message_id=4,
                role="ASSISTANT",
                content=(
                    "Concentration increases "
                    "drawdown exposure."
                ),
            ),
        ],
    )
def _service():
    contextual = Mock()
    contextual.analyze.return_value = (
        _response()
    )
    conversations = Mock()
    conversations.get_history.return_value = (
        _history()
    )
    service = (
        AIConversationAwareAnalysisService(
            contextual_service=contextual,
            conversation_service=(
                conversations
            ),
        )
    )
    return (
        service,
        contextual,
        conversations,
    )
def test_without_conversation_delegates_only():
    service, contextual, conversations = (
        _service()
    )
    request = AIAssistantRequest(
        question="Review the market."
    )
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=request,
    )
    assert (
        result.answer
        == "Current analysis completed."
    )
    conversations.get_history.assert_not_called()
    contextual.analyze.assert_called_once()
def test_history_can_be_disabled():
    service, _, conversations = (
        _service()
    )
    request = AIAssistantRequest(
        question="Continue this.",
        conversation_id=10,
        include_conversation_history=False,
    )
    service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=request,
    )
    conversations.get_history.assert_not_called()
def test_owned_history_is_loaded_with_limit():
    service, _, conversations = (
        _service()
    )
    user = SimpleNamespace(id=7)
    request = AIAssistantRequest(
        question="Continue this.",
        conversation_id=10,
        conversation_history_limit=20,
    )
    service.analyze(
        current_user=user,
        request=request,
    )
    conversations.get_history.assert_called_once_with(
        current_user=user,
        conversation_id=10,
        limit=20,
        offset=0,
    )
def test_history_adds_safe_section_and_source():
    service, _, _ = _service()
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review this again.",
            conversation_id=10,
        ),
    )
    assert (
        result.sections[0].title
        == "Conversation History"
    )
    assert (
        "CONVERSATION_HISTORY"
        in result.metadata.data_sources
    )
    assert result.execution_allowed is False
    assert (
        result.metadata.execution_enabled
        is False
    )
    assert (
        result.metadata.advisory_only
        is True
    )
def test_follow_up_uses_previous_assistant_context():
    service, _, _ = _service()
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Explain that again.",
            conversation_id=10,
        ),
    )
    assert (
        "treated as a follow-up"
        in result.answer
    )
    assert (
        "Concentration increases "
        "drawdown exposure."
        in result.answer
    )
def test_non_follow_up_keeps_original_answer():
    service, _, _ = _service()
    result = service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question=(
                "Provide a new BTC "
                "market overview."
            ),
            conversation_id=10,
        ),
    )
    assert (
        result.answer
        == "Current analysis completed."
    )
def test_ownership_error_is_preserved():
    service, _, conversations = (
        _service()
    )
    conversations.get_history.side_effect = (
        HTTPException(
            status_code=404,
            detail=(
                "AI conversation not found"
            ),
        )
    )
    with pytest.raises(
        HTTPException,
        match="AI conversation not found",
    ) as exc_info:
        service.analyze(
            current_user=(
                SimpleNamespace(id=7)
            ),
            request=AIAssistantRequest(
                question="Continue this.",
                conversation_id=999,
            ),
        )
    assert (
        exc_info.value.status_code
        == 404
    )
