from types import (
    SimpleNamespace,
)
import pytest
from app.ai.providers.base import (
    BaseAIProvider,
)
from app.schemas.ai_assistant import (
    AIAnalysisMetadata,
    AIAnalysisResponse,
    AIAnalysisSection,
    AIAnalysisWarning,
    AIAssistantRequest,
)
from app.schemas.ai_provider import (
    AIProviderRequest,
    AIProviderResponse,
)
from app.services.ai_external_orchestration_service import (
    AIExternalOrchestrationService,
)
def _deterministic_response(
    *,
    status="SUCCESS",
    data_sources=None,
):
    return AIAnalysisResponse(
        status=status,
        answer=(
            "Deterministic account "
            "analysis completed."
        ),
        sections=[
            AIAnalysisSection(
                title=(
                    "Authenticated Context"
                ),
                summary=(
                    "Safe authenticated "
                    "context summary."
                ),
                bullet_points=[
                    (
                        "Trading remains "
                        "disabled."
                    ),
                ],
            ),
        ],
        warnings=[
            AIAnalysisWarning(
                code="ADVISORY_ONLY",
                severity="INFO",
                message=(
                    "Analysis is advisory "
                    "only."
                ),
            ),
        ],
        metadata=AIAnalysisMetadata(
            analysis_type="GENERAL",
            generated_at_ms=100,
            confidence_score=0.8,
            data_sources=(
                data_sources
                or [
                    "USER_QUERY",
                    "RISK_ENGINE",
                ]
            ),
            provider="DETERMINISTIC",
            model_name=None,
            advisory_only=True,
            execution_enabled=False,
        ),
        execution_allowed=False,
    )
class FakeDeterministicService:
    def __init__(
        self,
        result=None,
    ):
        self.result = (
            result
            or _deterministic_response()
        )
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
        return self.result
class FakeProvider(
    BaseAIProvider
):
    def __init__(
        self,
        response,
    ):
        self.response = response
        self.calls = []
    @property
    def provider_name(self) -> str:
        return "TEST_PROVIDER"
    @property
    def model_name(self) -> str:
        return "test-model"
    async def generate(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        self.calls.append(request)
        if isinstance(
            self.response,
            Exception,
        ):
            raise self.response
        return self.response
def _success_response():
    return AIProviderResponse(
        status="SUCCESS",
        content=(
            "External explanation of "
            "the deterministic analysis."
        ),
        provider="TEST_PROVIDER",
        model_name="test-model",
        latency_ms=25,
        error_code=None,
        fallback_recommended=False,
        advisory_only=True,
        execution_enabled=False,
    )
def _failure_response(
    error_code="RATE_LIMITED",
):
    return AIProviderResponse(
        status="UNAVAILABLE",
        content=None,
        provider="TEST_PROVIDER",
        model_name="test-model",
        latency_ms=40,
        error_code=error_code,
        fallback_recommended=True,
        advisory_only=True,
        execution_enabled=False,
    )
def _service(
    provider_response,
    *,
    deterministic_result=None,
):
    deterministic = (
        FakeDeterministicService(
            deterministic_result
        )
    )
    provider = FakeProvider(
        provider_response
    )
    service = (
        AIExternalOrchestrationService(
            deterministic_service=(
                deterministic
            ),
            provider=provider,
        )
    )
    return (
        service,
        deterministic,
        provider,
    )
@pytest.mark.asyncio
async def test_external_provider_requires_request_opt_in():
    service, deterministic, provider = (
        _service(
            _success_response()
        )
    )
    result = await service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question=(
                "Review my account."
            ),
        ),
    )
    assert result.answer == (
        "Deterministic account "
        "analysis completed."
    )
    assert len(
        deterministic.calls
    ) == 1
    assert provider.calls == []
    assert (
        result.metadata.provider
        == "DETERMINISTIC"
    )
@pytest.mark.asyncio
async def test_successful_provider_enriches_safe_result():
    service, _, provider = _service(
        _success_response()
    )
    result = await service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question=(
                "Review my account."
            ),
            use_external_provider=True,
        ),
    )
    assert len(provider.calls) == 1
    assert (
        result.metadata.provider
        == "TEST_PROVIDER"
    )
    assert (
        result.metadata.model_name
        == "test-model"
    )
    assert (
        "EXTERNAL_AI"
        in result.metadata.data_sources
    )
    assert (
        result.sections[0].title
        == "External AI Provider"
    )
    assert (
        result.sections[0]
        .metrics["latency_ms"]
        == 25
    )
    assert result.execution_allowed is False
    assert (
        result.metadata.execution_enabled
        is False
    )
@pytest.mark.asyncio
async def test_provider_failure_uses_deterministic_fallback():
    service, _, _ = _service(
        _failure_response()
    )
    result = await service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question=(
                "Review my account."
            ),
            use_external_provider=True,
        ),
    )
    assert result.answer == (
        "Deterministic account "
        "analysis completed."
    )
    assert (
        result.metadata.provider
        == "DETERMINISTIC"
    )
    assert (
        result.sections[0]
        .metrics["error_code"]
        == "RATE_LIMITED"
    )
    assert (
        result.sections[0]
        .metrics["fallback_used"]
        is True
    )
    assert any(
        warning.code
        == "EXTERNAL_AI_FALLBACK"
        for warning in result.warnings
    )
@pytest.mark.asyncio
async def test_unexpected_provider_exception_is_sanitized():
    service, _, _ = _service(
        RuntimeError(
            "secret API key leaked"
        )
    )
    result = await service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Continue.",
            use_external_provider=True,
        ),
    )
    result_text = (
        result.model_dump_json()
    ).lower()
    assert (
        result.sections[0]
        .metrics["error_code"]
        == "PROVIDER_ERROR"
    )
    assert "secret api key leaked" not in (
        result_text
    )
    assert result.execution_allowed is False
@pytest.mark.asyncio
async def test_provider_prompt_redacts_credentials():
    service, _, provider = _service(
        _success_response()
    )
    await service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question=(
                "Review api_key=abc123 "
                "and Authorization: "
                "Bearer token-value."
            ),
            use_external_provider=True,
        ),
    )
    prompt = (
        provider.calls[0].user_prompt
    )
    assert "abc123" not in prompt
    assert "token-value" not in prompt
    assert "[REDACTED]" in prompt
@pytest.mark.asyncio
async def test_external_provider_does_not_upgrade_status():
    service, _, _ = _service(
        _success_response(),
        deterministic_result=(
            _deterministic_response(
                status="PARTIAL"
            )
        ),
    )
    result = await service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review this.",
            use_external_provider=True,
        ),
    )
    assert result.status == "PARTIAL"
@pytest.mark.asyncio
async def test_external_answer_has_mandatory_safety_notice():
    service, _, _ = _service(
        AIProviderResponse(
            status="SUCCESS",
            content=(
                "A market explanation."
            ),
            provider="TEST_PROVIDER",
            model_name="test-model",
            latency_ms=5,
            fallback_recommended=False,
            advisory_only=True,
            execution_enabled=False,
        )
    )
    result = await service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review BTC.",
            use_external_provider=True,
        ),
    )
    assert (
        "no trade, order, account "
        "change, or automation job"
        in result.answer
    )
    assert result.execution_allowed is False
@pytest.mark.asyncio
async def test_external_data_source_is_not_duplicated():
    service, _, _ = _service(
        _success_response(),
        deterministic_result=(
            _deterministic_response(
                data_sources=[
                    "USER_QUERY",
                    "EXTERNAL_AI",
                ]
            )
        ),
    )
    result = await service.analyze(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIAssistantRequest(
            question="Review BTC.",
            use_external_provider=True,
        ),
    )
    assert (
        result.metadata.data_sources.count(
            "EXTERNAL_AI"
        )
        == 1
    )
