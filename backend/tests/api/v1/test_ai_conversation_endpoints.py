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
from app.api.v1.endpoints.ai_conversations import (
    get_ai_conversation_service,
)
from app.main import app
from app.schemas.ai_conversation import (
    AIConversationHistoryResponse,
    AIConversationSummaryResponse,
    AIMessageResponse,
)
BASE_URL = (
    "/api/v1/ai-assistant/"
    "conversations"
)
def _now():
    return datetime.now(UTC)
def _summary(
    *,
    title="New conversation",
    status="ACTIVE",
):
    return AIConversationSummaryResponse(
        id=10,
        user_id=99,
        title=title,
        status=status,
        created_at=_now(),
        updated_at=_now(),
        message_count=2,
        last_message_at=_now(),
    )
def _history():
    return AIConversationHistoryResponse(
        conversation=_summary(),
        messages=[
            AIMessageResponse(
                id=1,
                conversation_id=10,
                user_id=99,
                role="USER",
                content="Review my portfolio.",
                analysis_type="PORTFOLIO",
                message_metadata={},
                created_at=_now(),
            ),
            AIMessageResponse(
                id=2,
                conversation_id=10,
                user_id=99,
                role="ASSISTANT",
                content="Portfolio reviewed.",
                analysis_type="PORTFOLIO",
                message_metadata={
                    "execution_allowed": False,
                },
                created_at=_now(),
            ),
        ],
    )
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
            title=(
                data.title
                or "New conversation"
            )
        )
    def list_conversations(
        self,
        *,
        current_user,
        limit,
        offset,
    ):
        self.calls.append(
            (
                "list",
                current_user,
                limit,
                offset,
            )
        )
        return [_summary()]
    def get_history(
        self,
        *,
        current_user,
        conversation_id,
        limit,
        offset,
    ):
        self.calls.append(
            (
                "history",
                current_user,
                conversation_id,
                limit,
                offset,
            )
        )
        return _history()
    def update_conversation(
        self,
        *,
        current_user,
        conversation_id,
        data,
    ):
        self.calls.append(
            (
                "update",
                current_user,
                conversation_id,
                data,
            )
        )
        return _summary(
            title=(
                data.title
                or "New conversation"
            ),
            status=(
                data.status
                or "ACTIVE"
            ),
        )
    def delete_conversation(
        self,
        *,
        current_user,
        conversation_id,
    ):
        self.calls.append(
            (
                "delete",
                current_user,
                conversation_id,
            )
        )
@pytest.fixture
def authenticated_client():
    service = FakeConversationService()
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=99,
        is_active=True,
    )
    app.dependency_overrides[
        get_ai_conversation_service
    ] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.clear()
def test_conversation_routes_require_authentication():
    service = FakeConversationService()
    app.dependency_overrides[
        get_ai_conversation_service
    ] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get(
                BASE_URL
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401
    assert service.calls == []
def test_create_conversation(
    authenticated_client,
):
    client, service = authenticated_client
    response = client.post(
        BASE_URL,
        json={
            "title": "Trading research",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert (
        payload["data"]["title"]
        == "Trading research"
    )
    assert service.calls[0][0] == "create"
def test_list_conversations_forwards_pagination(
    authenticated_client,
):
    client, service = authenticated_client
    response = client.get(
        BASE_URL,
        params={
            "limit": 25,
            "offset": 5,
        },
    )
    assert response.status_code == 200
    call = service.calls[0]
    assert call[0] == "list"
    assert call[2] == 25
    assert call[3] == 5
def test_get_conversation_history(
    authenticated_client,
):
    client, service = authenticated_client
    response = client.get(
        f"{BASE_URL}/10",
        params={
            "limit": 100,
            "offset": 0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert (
        len(payload["data"]["messages"])
        == 2
    )
    assert (
        payload["data"]["messages"][0]
        ["role"]
        == "USER"
    )
    assert service.calls[0][0] == "history"
def test_update_conversation(
    authenticated_client,
):
    client, service = authenticated_client
    response = client.patch(
        f"{BASE_URL}/10",
        json={
            "title": "Updated research",
            "status": "ARCHIVED",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert (
        payload["data"]["title"]
        == "Updated research"
    )
    assert (
        payload["data"]["status"]
        == "ARCHIVED"
    )
    assert service.calls[0][0] == "update"
def test_delete_conversation(
    authenticated_client,
):
    client, service = authenticated_client
    response = client.delete(
        f"{BASE_URL}/10"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] is None
    assert service.calls[0][0] == "delete"
def test_invalid_pagination_is_rejected(
    authenticated_client,
):
    client, service = authenticated_client
    response = client.get(
        BASE_URL,
        params={
            "limit": 0,
        },
    )
    assert response.status_code == 422
    assert service.calls == []
def test_service_error_is_preserved():
    class MissingConversationService:
        def get_history(
            self,
            *,
            current_user,
            conversation_id,
            limit,
            offset,
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
        get_ai_conversation_service
    ] = lambda: MissingConversationService()
    try:
        with TestClient(app) as client:
            response = client.get(
                f"{BASE_URL}/999"
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
