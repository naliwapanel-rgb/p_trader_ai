from types import (
    SimpleNamespace,
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
BASE_URL = (
    "/api/v1/ai-assistant/"
    "contextual-query"
)
class AsyncExternalService:
    def __init__(self):
        self.calls = []
    async def analyze(
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
        return AIAnalysisResponse(
            status="SUCCESS",
            answer=(
                "External advisory result."
            ),
            sections=[
                AIAnalysisSection(
                    title=(
                        "External AI Provider"
                    ),
                    summary=(
                        "External provider "
                        "completed safely."
                    ),
                    metrics={
                        "provider": (
                            "TEST_PROVIDER"
                        ),
                        "model_name": (
                            "test-model"
                        ),
                        "latency_ms": 10,
                        "error_code": None,
                        "fallback_used": False,
                        "execution_enabled": (
                            False
                        ),
                    },
                ),
            ],
            warnings=[],
            metadata=AIAnalysisMetadata(
                analysis_type="GENERAL",
                generated_at_ms=100,
                confidence_score=0.8,
                data_sources=[
                    "USER_QUERY",
                    "EXTERNAL_AI",
                ],
                provider="TEST_PROVIDER",
                model_name="test-model",
                advisory_only=True,
                execution_enabled=False,
            ),
            execution_allowed=False,
        )
def test_contextual_endpoint_awaits_external_service():
    service = AsyncExternalService()
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=99,
        is_active=True,
    )
    app.dependency_overrides[
        get_context_aware_analysis_service
    ] = lambda: service
    app.dependency_overrides[
        get_ai_conversation_service
    ] = lambda: SimpleNamespace()
    try:
        with TestClient(app) as client:
            response = client.post(
                BASE_URL,
                json={
                    "question": (
                        "Review my account."
                    ),
                    (
                        "use_external_"
                        "provider"
                    ): True,
                },
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()["data"]
    assert (
        data["metadata"]["provider"]
        == "TEST_PROVIDER"
    )
    assert (
        data["metadata"]["model_name"]
        == "test-model"
    )
    assert data["execution_allowed"] is False
    assert len(service.calls) == 1
    assert (
        service.calls[0][1]
        .use_external_provider
        is True
    )
