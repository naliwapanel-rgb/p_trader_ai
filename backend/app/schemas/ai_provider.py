from typing import (
    Literal,
)
from pydantic import (
    BaseModel,
    Field,
    field_validator,
)
AIProviderStatus = Literal[
    "SUCCESS",
    "UNAVAILABLE",
]
AIProviderErrorCode = Literal[
    "DISABLED",
    "NOT_CONFIGURED",
    "UNSUPPORTED_PROVIDER",
    "AUTHENTICATION_FAILED",
    "RATE_LIMITED",
    "TIMEOUT",
    "NETWORK_ERROR",
    "PROVIDER_ERROR",
    "INVALID_RESPONSE",
]
class AIProviderRequest(BaseModel):
    system_prompt: str = Field(
        min_length=1,
        max_length=8000,
    )
    user_prompt: str = Field(
        min_length=1,
        max_length=16000,
    )
    max_output_tokens: int = Field(
        default=800,
        ge=1,
        le=4096,
    )
    temperature: float = Field(
        default=0.2,
        ge=0,
        le=2,
    )
    @field_validator(
        "system_prompt",
        "user_prompt",
    )
    @classmethod
    def normalize_prompt(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "AI provider prompts "
                "cannot be blank"
            )
        return normalized
class AIProviderResponse(BaseModel):
    status: AIProviderStatus
    content: str | None = Field(
        default=None,
        min_length=1,
        max_length=12000,
    )
    provider: str = Field(
        min_length=2,
        max_length=100,
    )
    model_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    latency_ms: int = Field(
        default=0,
        ge=0,
    )
    error_code: (
        AIProviderErrorCode | None
    ) = None
    fallback_recommended: bool = False
    advisory_only: Literal[True] = True
    execution_enabled: Literal[False] = False
    @field_validator("provider")
    @classmethod
    def normalize_provider(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError(
                "provider cannot be blank"
            )
        return normalized
    @field_validator("content")
    @classmethod
    def normalize_content(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "provider content cannot "
                "be blank"
            )
        return normalized
