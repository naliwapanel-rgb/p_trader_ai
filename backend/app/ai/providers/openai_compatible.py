import time
from collections.abc import (
    Callable,
)
import httpx
from pydantic import (
    SecretStr,
)
from app.ai.providers.base import (
    BaseAIProvider,
)
from app.schemas.ai_provider import (
    AIProviderErrorCode,
    AIProviderRequest,
    AIProviderResponse,
)
class OpenAICompatibleAIProvider(
    BaseAIProvider
):
    def __init__(
        self,
        *,
        api_key: SecretStr | str,
        base_url: str,
        model_name: str,
        timeout_seconds: float = 20.0,
        transport: (
            httpx.AsyncBaseTransport | None
        ) = None,
        clock_ms: (
            Callable[[], int] | None
        ) = None,
    ):
        if isinstance(api_key, SecretStr):
            secret_value = (
                api_key.get_secret_value()
            )
        else:
            secret_value = api_key
        secret_value = secret_value.strip()
        normalized_url = base_url.strip()
        normalized_model = model_name.strip()
        if not secret_value:
            raise ValueError(
                "AI provider API key "
                "cannot be blank"
            )
        if not normalized_url:
            raise ValueError(
                "AI provider base URL "
                "cannot be blank"
            )
        if not normalized_model:
            raise ValueError(
                "AI provider model name "
                "cannot be blank"
            )
        if timeout_seconds <= 0:
            raise ValueError(
                "AI provider timeout "
                "must be positive"
            )
        self._api_key = secret_value
        self._base_url = (
            normalized_url.rstrip("/")
            + "/"
        )
        self._model_name = (
            normalized_model
        )
        self._timeout_seconds = (
            timeout_seconds
        )
        self._transport = transport
        self._clock_ms = (
            clock_ms
            or (
                lambda:
                int(time.time() * 1000)
            )
        )
    @property
    def provider_name(self) -> str:
        return "OPENAI_COMPATIBLE"
    @property
    def model_name(self) -> str:
        return self._model_name
    def _failure(
        self,
        *,
        error_code: AIProviderErrorCode,
        started_at_ms: int,
    ) -> AIProviderResponse:
        latency = max(
            0,
            self._clock_ms()
            - started_at_ms,
        )
        return AIProviderResponse(
            status="UNAVAILABLE",
            content=None,
            provider=self.provider_name,
            model_name=self.model_name,
            latency_ms=latency,
            error_code=error_code,
            fallback_recommended=True,
            advisory_only=True,
            execution_enabled=False,
        )
    @staticmethod
    def _extract_content(
        payload,
    ) -> str | None:
        if not isinstance(payload, dict):
            return None
        choices = payload.get("choices")
        if (
            not isinstance(choices, list)
            or not choices
        ):
            return None
        first_choice = choices[0]
        if not isinstance(
            first_choice,
            dict,
        ):
            return None
        message = first_choice.get(
            "message"
        )
        if not isinstance(message, dict):
            return None
        content = message.get("content")
        if not isinstance(content, str):
            return None
        normalized = content.strip()
        return normalized or None
    async def generate(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        started_at_ms = self._clock_ms()
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        request.system_prompt
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        request.user_prompt
                    ),
                },
            ],
            "max_tokens": (
                request.max_output_tokens
            ),
            "temperature": (
                request.temperature
            ),
        }
        headers = {
            "Authorization": (
                f"Bearer {self._api_key}"
            ),
            "Content-Type": (
                "application/json"
            ),
        }
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    "chat/completions",
                    headers=headers,
                    json=payload,
                )
        except httpx.TimeoutException:
            return self._failure(
                error_code="TIMEOUT",
                started_at_ms=started_at_ms,
            )
        except httpx.RequestError:
            return self._failure(
                error_code="NETWORK_ERROR",
                started_at_ms=started_at_ms,
            )
        if response.status_code in {
            401,
            403,
        }:
            return self._failure(
                error_code=(
                    "AUTHENTICATION_FAILED"
                ),
                started_at_ms=started_at_ms,
            )
        if response.status_code == 429:
            return self._failure(
                error_code="RATE_LIMITED",
                started_at_ms=started_at_ms,
            )
        if response.status_code >= 400:
            return self._failure(
                error_code="PROVIDER_ERROR",
                started_at_ms=started_at_ms,
            )
        try:
            response_payload = (
                response.json()
            )
        except ValueError:
            return self._failure(
                error_code="INVALID_RESPONSE",
                started_at_ms=started_at_ms,
            )
        content = self._extract_content(
            response_payload
        )
        if content is None:
            return self._failure(
                error_code="INVALID_RESPONSE",
                started_at_ms=started_at_ms,
            )
        latency = max(
            0,
            self._clock_ms()
            - started_at_ms,
        )
        return AIProviderResponse(
            status="SUCCESS",
            content=content,
            provider=self.provider_name,
            model_name=self.model_name,
            latency_ms=latency,
            error_code=None,
            fallback_recommended=False,
            advisory_only=True,
            execution_enabled=False,
        )
