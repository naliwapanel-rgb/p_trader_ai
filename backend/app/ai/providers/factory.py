import httpx
from app.ai.providers.base import (
    BaseAIProvider,
)
from app.ai.providers.disabled import (
    DisabledAIProvider,
)
from app.ai.providers.openai_compatible import (
    OpenAICompatibleAIProvider,
)
from app.core.config import (
    Settings,
    get_settings,
)
class AIProviderFactory:
    @staticmethod
    def create(
        *,
        settings: Settings | None = None,
        transport: (
            httpx.AsyncBaseTransport | None
        ) = None,
    ) -> BaseAIProvider:
        resolved_settings = (
            settings or get_settings()
        )
        if not (
            resolved_settings
            .ai_external_enabled
        ):
            return DisabledAIProvider(
                error_code="DISABLED"
            )
        provider_name = (
            resolved_settings
            .ai_provider
            .strip()
            .upper()
        )
        if (
            provider_name
            != "OPENAI_COMPATIBLE"
        ):
            return DisabledAIProvider(
                error_code=(
                    "UNSUPPORTED_PROVIDER"
                )
            )
        api_key = (
            resolved_settings.ai_api_key
        )
        base_url = (
            resolved_settings.ai_base_url
        )
        model_name = (
            resolved_settings.ai_model_name
        )
        secret_value = (
            api_key.get_secret_value()
            if api_key is not None
            else ""
        )
        if (
            not secret_value.strip()
            or not base_url
            or not base_url.strip()
            or not model_name
            or not model_name.strip()
        ):
            return DisabledAIProvider(
                error_code="NOT_CONFIGURED"
            )
        return OpenAICompatibleAIProvider(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            timeout_seconds=(
                resolved_settings
                .ai_request_timeout_seconds
            ),
            transport=transport,
        )
