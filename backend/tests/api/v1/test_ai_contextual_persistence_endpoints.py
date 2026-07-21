from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
import pytest
from fastapi import (
    HTTPException,
)
from fastapi.testclient import (
    TestClient,
)
from app.api.dependencies import (
    get_current_user,
)
from app.api.v1.endpoints.ai_contextual_analysis import (
    get_context_aware_analysis_service,
)
from app.api.v1.endpoints.ai_conversations import (
    get_ai_conversation_service,
)
from app.main import app
from app.schemas.ai_assistant import (
    AIAnalysisMetadata,
    AIAnalysisResponse,
    AIAnalysisSection,
)
from app.schemas.ai_conversation import (
    AIConversationExchangeResponse,
    AIConversationSummaryResponse,
    AIMessageResponse,
)
BASE_URL = (
    "/api/v1/ai-assistant/"
    "contextual-query"
)
def _now():
    return datetime.now(UTC)
def _analysis_response():
    return AIAnalysisResponse(
        status="SUCCESS",
        answer=(
            "Authenticated context reviewed."
        ),
        sections=[
            AIAnalysisSection(
                title="Context",
                summary=(
                    "Authenticated user "
                    "context summary."
                ),
            ),
        ],
        warnings=[],
        metadata=AIAnalysisMetadata(
            analysis_type="GENERAL",
            generated_at_ms=123456789,
            confidence_score=0.85,
            data_sources=[
                "USER_QUERY",
                "RISK_ENGINE",
            ],
            provider="DETERMINISTIC",
            advisory_only=True,
            execution_enabled=False,
        ),
        execution_allowed=False,
    )
def _summary(
    *,
    conversation_id=10,
    title="Review my account.",
    message_count=2,
):
    return AIConversationSummaryResponse(
        id=conversation_id,
        user_id=99,
        title=title,
        status="ACTIVE",
        created_at=_now(),
        updated_at=_now(),
        message_count=message_count,
        last_message_at=(
            _now()
            if message_count > 0
            else None
        ),
    )
def _message(
    *,
    message_id,
    conversation_id,
    role,
    content,
):
    return AIMessageResponse(
        id=message_id,
        conversation_id=(
            conversation_id
        ),
        user_id=99,
        role=role,
        content=content,
        analysis_type="GENERAL",
        message_metadata={},
        created_at=_now(),
    )
def _exchange(
    *,
    conversation_id=10,
):
    return AIConversationExchangeResponse(
        conversation=_summary(
            conversation_id=(
                conversation_id
            ),
        ),
        user_message=_message(
            message_id=101,
            conversation_id=(
                conversation_id
            ),
            role="USER",
            content="Review my account.",
        ),
        assistant_message=_message(
            message_id=102,
            conversation_id=(
                conversation_id
            ),
            role="ASSISTANT",
            content=(
                "Authenticated context "
                "reviewed."
            ),
        ),
    )
class FakeAnalysisService:
    def __init__(self):
        self.calls = []
    def analyze(
        self,
        *,
        current_user,
        request,
    ):
        self.calls.append(
            (
                current_user,
                request,
            )
        )
        return _analysis_response()
class FakeConversationService:
    def __init__(self):
        self.calls = []
    def create_conversation(
        self,
        *,
        current_user,
        data,
    ):
        self.calls.append(
            (
                "create",
                current_user,
                data,
            )
        )
        return _summary(
            conversation_id=10,
            title="New conversation",
            message_count=0,
        )
    def append_exchange(
        self,
        *,
        current_user,
        conversation_id,
        data,
    ):
        self.calls.append(
            (
                "append",
                current_user,
                conversation_id,
                data,
            )
        )
        return _exchange(
            conversation_id=(
                conversation_id
            )
        )
@pytest.fixture
def client_services():
    analysis = FakeAnalysisService()
    conversations = (
        FakeConversationService()
    )
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=99,
        is_active=True,
    )
    app.dependency_overrides[
        get_context_aware_analysis_service
    ] = lambda: analysis
    app.dependency_overrides[
        get_ai_conversation_service
    ] = lambda: conversations
    try:
        with TestClient(app) as client:
            yield (
                client,
                analysis,
                conversations,
            )
    finally:
        app.dependency_overrides.clear()
def test_contextual_query_does_not_persist_by_default(
    client_services,
):
    client, analysis, conversations = (
        client_services
    )
    response = client.post(
        BASE_URL,
        json={
            "question": (
                "Review my account."
            ),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert (
        payload["data"]["conversation"]
        ["persisted"]
        is False
    )
    assert conversations.calls == []
    assert len(analysis.calls) == 1
def test_contextual_query_creates_new_conversation(
    client_services,
):
    client, _, conversations = (
        client_services
    )
    response = client.post(
        BASE_URL,
        json={
            "question": (
                "Review my account."
            ),
            "persist_conversation": True,
        },
    )
    assert response.status_code == 200
    persistence = (
        response.json()["data"]
        ["conversation"]
    )
    assert persistence == {
        "persisted": True,
        "conversation_id": 10,
        "user_message_id": 101,
        "assistant_message_id": 102,
    }
    assert [
        call[0]
        for call in conversations.calls
    ] == [
        "create",
        "append",
    ]
def test_contextual_query_appends_existing_conversation(
    client_services,
):
    client, _, conversations = (
        client_services
    )
    response = client.post(
        BASE_URL,
        json={
            "question": (
                "Review my account."
            ),
            "conversation_id": 55,
            "persist_conversation": True,
        },
    )
    assert response.status_code == 200
    persistence = (
        response.json()["data"]
        ["conversation"]
    )
    assert (
        persistence["conversation_id"]
        == 55
    )
    assert len(conversations.calls) == 1
    assert conversations.calls[0][0] == "append"
    assert conversations.calls[0][2] == 55
def test_persisted_metadata_remains_safe(
    client_services,
):
    client, _, conversations = (
        client_services
    )
    response = client.post(
        BASE_URL,
        json={
            "question": (
                "Review BTC."
            ),
            "symbols": ["btcusdt"],
            "persist_conversation": True,
        },
    )
    assert response.status_code == 200
    append_call = conversations.calls[1]
    exchange_data = append_call[3]
    assert exchange_data.user_metadata == {
        "symbols": ["BTCUSDT"],
        "portfolio_id": None,
        "exchange_account_id": None,
        "include_user_context": True,
        "include_conversation_history": True,
        "conversation_history_limit": 12,
        "use_external_provider": False,
    }
    assert (
        exchange_data
        .assistant_metadata
        ["execution_allowed"]
        is False
    )
    assert (
        exchange_data
        .assistant_metadata
        ["execution_enabled"]
        is False
    )
    metadata_text = str(
        exchange_data.assistant_metadata
    ).lower()
    assert "api_key" not in metadata_text
    assert "secret" not in metadata_text
    assert "token" not in metadata_text
def test_conversation_ownership_error_is_preserved():
    analysis = FakeAnalysisService()
    class MissingConversationService:
        def append_exchange(
            self,
            *,
            current_user,
            conversation_id,
            data,
        ):
            raise HTTPException(
                status_code=404,
                detail=(
                    "AI conversation not found"
                ),
            )
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=99,
        is_active=True,
    )
    app.dependency_overrides[
        get_context_aware_analysis_service
    ] = lambda: analysis
    app.dependency_overrides[
        get_ai_conversation_service
    ] = lambda: MissingConversationService()
    try:
        with TestClient(app) as client:
            response = client.post(
                BASE_URL,
                json={
                    "question": (
                        "Review my account."
                    ),
                    "conversation_id": 999,
                    "persist_conversation": True,
                },
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert (
        payload["message"]
        == "AI conversation not found"
    )
