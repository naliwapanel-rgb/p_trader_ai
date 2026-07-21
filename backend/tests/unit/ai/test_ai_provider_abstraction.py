import json
import httpx
import pytest
from pydantic import (
    SecretStr,
)
from app.ai.providers.disabled import (
    DisabledAIProvider,
)
from app.ai.providers.factory import (
    AIProviderFactory,
)
from app.ai.providers.openai_compatible import (
    OpenAICompatibleAIProvider,
)
from app.core.config import (
    Settings,
)
from app.schemas.ai_provider import (
    AIProviderRequest,
)
def _request():
    return AIProviderRequest(
        system_prompt=(
            "  Provide advisory-only "
            "trading analysis.  "
        ),
        user_prompt=(
            "  Review BTC market risk.  "
        ),
        max_output_tokens=400,
        temperature=0.1,
    )
def test_provider_request_normalizes_prompts():
    request = _request()
    assert request.system_prompt == (
        "Provide advisory-only "
        "trading analysis."
    )
    assert request.user_prompt == (
        "Review BTC market risk."
    )
@pytest.mark.asyncio
async def test_disabled_provider_returns_safe_fallback():
    provider = DisabledAIProvider()
    response = await provider.generate(
        _request()
    )
    assert response.status == "UNAVAILABLE"
    assert response.content is None
    assert response.provider == "DISABLED"
    assert response.error_code == "DISABLED"
    assert response.fallback_recommended is True
    assert response.advisory_only is True
    assert response.execution_enabled is False
@pytest.mark.asyncio
async def test_openai_compatible_provider_success():
    captured = {}
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        captured["authorization"] = (
            request.headers.get(
                "authorization"
            )
        )
        captured["payload"] = json.loads(
            request.content.decode()
        )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "BTC risk remains "
                                "elevated."
                            ),
                        },
                    },
                ],
            },
            request=request,
        )
    times = iter([
        1000,
        1025,
    ])
    provider = (
        OpenAICompatibleAIProvider(
            api_key=SecretStr(
                "super-secret"
            ),
            base_url=(
                "https://provider.test/v1"
            ),
            model_name="test-model",
            timeout_seconds=5,
            transport=httpx.MockTransport(
                handler
            ),
            clock_ms=lambda: next(times),
        )
    )
    response = await provider.generate(
        _request()
    )
    assert response.status == "SUCCESS"
    assert response.content == (
        "BTC risk remains elevated."
    )
    assert response.provider == (
        "OPENAI_COMPATIBLE"
    )
    assert response.model_name == (
        "test-model"
    )
    assert response.latency_ms == 25
    assert response.error_code is None
    assert (
        response.fallback_recommended
        is False
    )
    assert response.execution_enabled is False
    assert captured["authorization"] == (
        "Bearer super-secret"
    )
    assert (
        captured["payload"]["model"]
        == "test-model"
    )
    assert (
        captured["payload"]
        ["max_tokens"]
        == 400
    )
@pytest.mark.asyncio
async def test_authentication_failure_is_sanitized():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            401,
            json={
                "error": {
                    "message": (
                        "Invalid key "
                        "super-secret"
                    ),
                },
            },
            request=request,
        )
    provider = (
        OpenAICompatibleAIProvider(
            api_key="super-secret",
            base_url=(
                "https://provider.test/v1"
            ),
            model_name="test-model",
            transport=httpx.MockTransport(
                handler
            ),
        )
    )
    response = await provider.generate(
        _request()
    )
    response_text = (
        response.model_dump_json()
    )
    assert response.status == "UNAVAILABLE"
    assert response.error_code == (
        "AUTHENTICATION_FAILED"
    )
    assert "super-secret" not in (
        response_text
    )
@pytest.mark.asyncio
async def test_rate_limit_recommends_fallback():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            429,
            json={"error": "rate limited"},
            request=request,
        )
    provider = (
        OpenAICompatibleAIProvider(
            api_key="test-key",
            base_url=(
                "https://provider.test/v1"
            ),
            model_name="test-model",
            transport=httpx.MockTransport(
                handler
            ),
        )
    )
    response = await provider.generate(
        _request()
    )
    assert response.error_code == (
        "RATE_LIMITED"
    )
    assert response.fallback_recommended is True
@pytest.mark.asyncio
async def test_timeout_recommends_fallback():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ReadTimeout(
            "Provider timed out",
            request=request,
        )
    provider = (
        OpenAICompatibleAIProvider(
            api_key="test-key",
            base_url=(
                "https://provider.test/v1"
            ),
            model_name="test-model",
            transport=httpx.MockTransport(
                handler
            ),
        )
    )
    response = await provider.generate(
        _request()
    )
    assert response.status == "UNAVAILABLE"
    assert response.error_code == "TIMEOUT"
    assert response.content is None
@pytest.mark.asyncio
async def test_invalid_response_recommends_fallback():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [],
            },
            request=request,
        )
    provider = (
        OpenAICompatibleAIProvider(
            api_key="test-key",
            base_url=(
                "https://provider.test/v1"
            ),
            model_name="test-model",
            transport=httpx.MockTransport(
                handler
            ),
        )
    )
    response = await provider.generate(
        _request()
    )
    assert response.error_code == (
        "INVALID_RESPONSE"
    )
    assert response.fallback_recommended is True
def test_factory_disables_external_provider_by_default():
    settings = Settings(
        _env_file=None,
    )
    provider = AIProviderFactory.create(
        settings=settings
    )
    assert isinstance(
        provider,
        DisabledAIProvider,
    )
    assert provider.error_code == "DISABLED"
def test_factory_rejects_missing_configuration():
    settings = Settings(
        _env_file=None,
        ai_external_enabled=True,
        ai_provider=(
            "OPENAI_COMPATIBLE"
        ),
    )
    provider = AIProviderFactory.create(
        settings=settings
    )
    assert isinstance(
        provider,
        DisabledAIProvider,
    )
    assert (
        provider.error_code
        == "NOT_CONFIGURED"
    )
def test_factory_rejects_unsupported_provider():
    settings = Settings(
        _env_file=None,
        ai_external_enabled=True,
        ai_provider="UNKNOWN",
        ai_api_key="secret",
        ai_base_url=(
            "https://provider.test/v1"
        ),
        ai_model_name="test-model",
    )
    provider = AIProviderFactory.create(
        settings=settings
    )
    assert isinstance(
        provider,
        DisabledAIProvider,
    )
    assert provider.error_code == (
        "UNSUPPORTED_PROVIDER"
    )
def test_factory_builds_configured_provider_safely():
    settings = Settings(
        _env_file=None,
        ai_external_enabled=True,
        ai_provider=(
            "OPENAI_COMPATIBLE"
        ),
        ai_api_key="super-secret",
        ai_base_url=(
            "https://provider.test/v1"
        ),
        ai_model_name="test-model",
        ai_request_timeout_seconds=15,
    )
    provider = AIProviderFactory.create(
        settings=settings,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": "Safe",
                            },
                        },
                    ],
                },
                request=request,
            )
        ),
    )
    assert isinstance(
        provider,
        OpenAICompatibleAIProvider,
    )
    assert provider.model_name == (
        "test-model"
    )
    assert "super-secret" not in repr(
        settings
    )
