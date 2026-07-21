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
from app.main import app
from app.schemas.ai_assistant import (
    AIAnalysisMetadata,
    AIAnalysisResponse,
    AIAnalysisSection,
)
BASE_URL = (
    "/api/v1/ai-assistant/"
    "contextual-query"
)
def _response():
    return AIAnalysisResponse(
        status="SUCCESS",
        answer=(
            "Authenticated context reviewed."
        ),
        sections=[
            AIAnalysisSection(
                title="Context",
                summary=(
                    "Authenticated context "
                    "summary."
                ),
            ),
        ],
        warnings=[],
        metadata=AIAnalysisMetadata(
            analysis_type="GENERAL",
            generated_at_ms=123456789,
            confidence_score=0.8,
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
class FakeContextAwareService:
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
        return _response()
@pytest.fixture
def authenticated_client():
    service = FakeContextAwareService()
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=99,
        is_active=True,
    )
    app.dependency_overrides[
        get_context_aware_analysis_service
    ] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.clear()
def test_contextual_query_requires_authentication():
    service = FakeContextAwareService()
    app.dependency_overrides[
        get_context_aware_analysis_service
    ] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post(
                BASE_URL,
                json={
                    "question": (
                        "Review my account."
                    ),
                },
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401
    assert service.calls == []
def test_contextual_query_returns_safe_response(
    authenticated_client,
):
    client, service = (
        authenticated_client
    )
    response = client.post(
        BASE_URL,
        json={
            "question": (
                "Review my account."
            ),
            "analysis_type": "GENERAL",
            "symbols": [
                "btcusdt",
            ],
            "include_user_context": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert (
        payload["data"]
        ["execution_allowed"]
        is False
    )
    assert (
        payload["data"]
        ["metadata"]
        ["execution_enabled"]
        is False
    )
    user, request = service.calls[0]
    assert user.id == 99
    assert request.symbols == [
        "BTCUSDT",
    ]
def test_contextual_query_rejects_invalid_body(
    authenticated_client,
):
    client, service = (
        authenticated_client
    )
    response = client.post(
        BASE_URL,
        json={
            "question": " ",
        },
    )
    assert response.status_code == 422
    assert service.calls == []
def test_contextual_service_error_is_preserved():
    class MissingPortfolioService:
        def analyze(
            self,
            *,
            current_user,
            request,
        ):
            raise HTTPException(
                status_code=404,
                detail="Portfolio not found",
            )
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=99,
        is_active=True,
    )
    app.dependency_overrides[
        get_context_aware_analysis_service
    ] = lambda: MissingPortfolioService()
    try:
        with TestClient(app) as client:
            response = client.post(
                BASE_URL,
                json={
                    "question": (
                        "Review portfolio."
                    ),
                    "analysis_type": (
                        "PORTFOLIO"
                    ),
                    "portfolio_id": 10,
                },
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert (
        payload["message"]
        == "Portfolio not found"
    )
