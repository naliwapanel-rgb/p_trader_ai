from app.ai.providers.base import (
    BaseAIProvider,
)
from app.schemas.ai_provider import (
    AIProviderErrorCode,
    AIProviderRequest,
    AIProviderResponse,
)
class DisabledAIProvider(
    BaseAIProvider
):
    def __init__(
        self,
        *,
        error_code: AIProviderErrorCode = (
            "DISABLED"
        ),
    ):
        self.error_code = error_code
    @property
    def provider_name(self) -> str:
        return "DISABLED"
    @property
    def model_name(self) -> None:
        return None
    async def generate(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        del request
        return AIProviderResponse(
            status="UNAVAILABLE",
            content=None,
            provider=self.provider_name,
            model_name=None,
            latency_ms=0,
            error_code=self.error_code,
            fallback_recommended=True,
            advisory_only=True,
            execution_enabled=False,
        )
