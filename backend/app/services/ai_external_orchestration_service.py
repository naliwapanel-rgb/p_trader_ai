import json
import re
from app.ai.providers.base import (
    BaseAIProvider,
)
from app.models.user import (
    User,
)
from app.schemas.ai_assistant import (
    AIAnalysisResponse,
    AIAnalysisSection,
    AIAnalysisWarning,
    AIAssistantRequest,
)
from app.schemas.ai_provider import (
    AIProviderRequest,
    AIProviderResponse,
)
from app.services.ai_conversation_aware_analysis_service import (
    AIConversationAwareAnalysisService,
)
class AIExternalOrchestrationService:
    """
    Apply optional external AI wording to a
    completed deterministic analysis.
    Deterministic analysis remains the fallback
    and safety authority. This service cannot
    submit exchange orders or automation jobs.
    """
    _SENSITIVE_ASSIGNMENT = re.compile(
        (
            r"(?i)\b("
            r"api[_\s-]?key|"
            r"api[_\s-]?secret|"
            r"secret|password|token|"
            r"authorization|"
            r"encryption[_\s-]?key|"
            r"credential"
            r")\b\s*[:=]\s*"
            r"([^\s,;]+)"
        )
    )
    _BEARER_TOKEN = re.compile(
        (
            r"(?i)\bBearer\s+"
            r"[A-Za-z0-9._~+/=-]+"
        )
    )
    _SECRET_KEY_FORMAT = re.compile(
        r"\bsk-[A-Za-z0-9_-]{8,}\b"
    )
    _SYSTEM_PROMPT = (
        "You are the advisory language layer "
        "for P-TRADER AI. Use only the supplied "
        "deterministic analysis. Never claim "
        "that you executed a trade, submitted "
        "an order, changed an account, or created "
        "an automation job. Never request or "
        "reveal passwords, API keys, secrets, "
        "tokens, credentials, or authorization "
        "headers. Preserve all risk warnings. "
        "Give a clear, concise explanation. "
        "The response is advisory only."
    )
    _ADVISORY_SUFFIX = (
        "\n\nAdvisory only: no trade, order, "
        "account change, or automation job was "
        "created or executed."
    )
    def __init__(
        self,
        *,
        deterministic_service: (
            AIConversationAwareAnalysisService
        ),
        provider: BaseAIProvider,
    ):
        self.deterministic_service = (
            deterministic_service
        )
        self.provider = provider
    @classmethod
    def _sanitize_text(
        cls,
        value: str,
    ) -> str:
        sanitized = (
            cls._BEARER_TOKEN.sub(
                "Bearer [REDACTED]",
                value,
            )
        )
        sanitized = (
            cls._SENSITIVE_ASSIGNMENT.sub(
                (
                    lambda match:
                    f"{match.group(1)}="
                    "[REDACTED]"
                ),
                sanitized,
            )
        )
        sanitized = (
            cls._SECRET_KEY_FORMAT.sub(
                "[REDACTED]",
                sanitized,
            )
        )
        return sanitized
    @staticmethod
    def _truncate(
        value: str,
        limit: int,
    ) -> str:
        if len(value) <= limit:
            return value
        return (
            value[
                : limit - 3
            ].rstrip()
            + "..."
        )
    @classmethod
    def _prompt_request(
        cls,
        *,
        request: AIAssistantRequest,
        result: AIAnalysisResponse,
    ) -> AIProviderRequest:
        sections = []
        for section in result.sections[:20]:
            sections.append({
                "title": cls._sanitize_text(
                    section.title
                ),
                "summary": cls._sanitize_text(
                    cls._truncate(
                        section.summary,
                        1000,
                    )
                ),
                "bullet_points": [
                    cls._sanitize_text(
                        cls._truncate(
                            bullet,
                            500,
                        )
                    )
                    for bullet in (
                        section
                        .bullet_points[:15]
                    )
                ],
            })
        warnings = [
            {
                "code": warning.code,
                "severity": warning.severity,
                "message": cls._sanitize_text(
                    cls._truncate(
                        warning.message,
                        500,
                    )
                ),
            }
            for warning in (
                result.warnings[:30]
            )
        ]
        payload = {
            "question": cls._sanitize_text(
                request.question
            ),
            "analysis_type": (
                request.analysis_type
            ),
            "symbols": list(
                request.symbols
            ),
            "deterministic_status": (
                result.status
            ),
            "deterministic_answer": (
                cls._sanitize_text(
                    result.answer
                )
            ),
            "sections": sections,
            "warnings": warnings,
            "execution_allowed": False,
        }
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        serialized = cls._truncate(
            serialized,
            15000,
        )
        return AIProviderRequest(
            system_prompt=(
                cls._SYSTEM_PROMPT
            ),
            user_prompt=serialized,
            max_output_tokens=1000,
            temperature=0.2,
        )
    @staticmethod
    def _provider_section(
        response: AIProviderResponse,
        *,
        fallback_used: bool,
    ) -> AIAnalysisSection:
        if fallback_used:
            summary = (
                "The external AI provider was "
                "unavailable. The deterministic "
                "analysis was retained."
            )
        else:
            summary = (
                "External AI wording was applied "
                "to the deterministic advisory "
                "analysis."
            )
        return AIAnalysisSection(
            title="External AI Provider",
            summary=summary,
            metrics={
                "provider": response.provider,
                "model_name": (
                    response.model_name
                ),
                "latency_ms": (
                    response.latency_ms
                ),
                "error_code": (
                    response.error_code
                ),
                "fallback_used": (
                    fallback_used
                ),
                "execution_enabled": False,
            },
        )
    @staticmethod
    def _append_warning(
        warnings: list[
            AIAnalysisWarning
        ],
        warning: AIAnalysisWarning,
    ) -> list[AIAnalysisWarning]:
        identities = {
            (
                item.code,
                item.message,
            )
            for item in warnings
        }
        identity = (
            warning.code,
            warning.message,
        )
        if (
            identity not in identities
            and len(warnings) < 50
        ):
            warnings.append(warning)
        return warnings
    @staticmethod
    def _provider_identity(
        provider: BaseAIProvider,
    ) -> tuple[str, str | None]:
        try:
            provider_name = (
                provider.provider_name
            )
        except Exception:
            provider_name = "UNKNOWN"
        try:
            model_name = (
                provider.model_name
            )
        except Exception:
            model_name = None
        return (
            provider_name,
            model_name,
        )
    def _unexpected_failure(
        self,
    ) -> AIProviderResponse:
        provider_name, model_name = (
            self._provider_identity(
                self.provider
            )
        )
        return AIProviderResponse(
            status="UNAVAILABLE",
            content=None,
            provider=provider_name,
            model_name=model_name,
            latency_ms=0,
            error_code="PROVIDER_ERROR",
            fallback_recommended=True,
            advisory_only=True,
            execution_enabled=False,
        )
    @classmethod
    def _external_answer(
        cls,
        content: str,
    ) -> str:
        maximum_content_length = (
            12000
            - len(cls._ADVISORY_SUFFIX)
        )
        normalized = cls._truncate(
            content.strip(),
            maximum_content_length,
        )
        return (
            normalized
            + cls._ADVISORY_SUFFIX
        )
    async def analyze(
        self,
        *,
        current_user: User,
        request: AIAssistantRequest,
    ) -> AIAnalysisResponse:
        deterministic_result = (
            self.deterministic_service
            .analyze(
                current_user=current_user,
                request=request,
            )
        )
        if not request.use_external_provider:
            return deterministic_result
        provider_request = (
            self._prompt_request(
                request=request,
                result=deterministic_result,
            )
        )
        try:
            provider_response = (
                await self.provider.generate(
                    provider_request
                )
            )
        except Exception:
            provider_response = (
                self._unexpected_failure()
            )
        provider_succeeded = (
            provider_response.status
            == "SUCCESS"
            and provider_response.content
            is not None
        )
        if not provider_succeeded:
            warnings = list(
                deterministic_result.warnings
            )
            warnings = self._append_warning(
                warnings,
                AIAnalysisWarning(
                    code=(
                        "EXTERNAL_AI_FALLBACK"
                    ),
                    severity="INFO",
                    message=(
                        "External AI was "
                        "unavailable. Deterministic "
                        "analysis was retained."
                    ),
                ),
            )
            return (
                deterministic_result.model_copy(
                    update={
                        "sections": [
                            self._provider_section(
                                provider_response,
                                fallback_used=True,
                            ),
                            *deterministic_result
                            .sections[:29],
                        ],
                        "warnings": warnings,
                        "execution_allowed": False,
                    }
                )
            )
        data_sources = list(
            deterministic_result
            .metadata.data_sources
        )
        if (
            "EXTERNAL_AI"
            not in data_sources
            and len(data_sources) < 20
        ):
            data_sources.append(
                "EXTERNAL_AI"
            )
        metadata = (
            deterministic_result
            .metadata.model_copy(
                update={
                    "provider": (
                        provider_response
                        .provider
                    ),
                    "model_name": (
                        provider_response
                        .model_name
                    ),
                    "data_sources": (
                        data_sources
                    ),
                    "advisory_only": True,
                    "execution_enabled": False,
                }
            )
        )
        warnings = list(
            deterministic_result.warnings
        )
        warnings = self._append_warning(
            warnings,
            AIAnalysisWarning(
                code=(
                    "EXTERNAL_AI_ADVISORY"
                ),
                severity="INFO",
                message=(
                    "External AI wording is "
                    "advisory only and cannot "
                    "execute a trade or "
                    "automation action."
                ),
            ),
        )
        return (
            deterministic_result.model_copy(
                update={
                    "answer": (
                        self._external_answer(
                            provider_response
                            .content
                        )
                    ),
                    "sections": [
                        self._provider_section(
                            provider_response,
                            fallback_used=False,
                        ),
                        *deterministic_result
                        .sections[:29],
                    ],
                    "warnings": warnings,
                    "metadata": metadata,
                    "execution_allowed": False,
                }
            )
        )
