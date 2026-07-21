from inspect import (
    isawaitable,
)
from fastapi import (
    APIRouter,
    Depends,
)
from app.ai.providers.base import (
    BaseAIProvider,
)
from app.ai.providers.factory import (
    AIProviderFactory,
)
from app.api.dependencies import (
    get_current_user,
)
from app.api.v1.endpoints.ai_context import (
    get_ai_context_builder_service,
)
from app.api.v1.endpoints.ai_conversations import (
    get_ai_conversation_service,
)
from app.models.user import User
from app.schemas.ai_assistant import (
    AIAssistantRequest,
)
from app.schemas.ai_conversation import (
    AIConversationCreateRequest,
    AIConversationExchangeCreate,
)
from app.services.ai_analysis_service import (
    DeterministicAIAnalysisService,
)
from app.services.ai_context_service import (
    AIContextBuilderService,
)
from app.services.ai_contextual_analysis_service import (
    AIContextAwareAnalysisService,
)
from app.services.ai_conversation_aware_analysis_service import (
    AIConversationAwareAnalysisService,
)
from app.services.ai_conversation_service import (
    AIConversationService,
)
from app.services.ai_external_orchestration_service import (
    AIExternalOrchestrationService,
)
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix="/ai-assistant",
    tags=["AI Assistant"],
)
def get_ai_provider() -> BaseAIProvider:
    return AIProviderFactory.create()
def get_context_aware_analysis_service(
    context_builder: (
        AIContextBuilderService
    ) = Depends(
        get_ai_context_builder_service
    ),
    conversation_service: (
        AIConversationService
    ) = Depends(
        get_ai_conversation_service
    ),
    provider: BaseAIProvider = Depends(
        get_ai_provider
    ),
) -> AIExternalOrchestrationService:
    contextual_service = (
        AIContextAwareAnalysisService(
            context_builder=(
                context_builder
            ),
            analysis_service=(
                DeterministicAIAnalysisService()
            ),
        )
    )
    conversation_aware_service = (
        AIConversationAwareAnalysisService(
            contextual_service=(
                contextual_service
            ),
            conversation_service=(
                conversation_service
            ),
        )
    )
    return AIExternalOrchestrationService(
        deterministic_service=(
            conversation_aware_service
        ),
        provider=provider,
    )
def _provider_audit_metadata(
    result,
) -> dict:
    for section in result.sections:
        if (
            section.title
            == "External AI Provider"
        ):
            return dict(
                section.metrics
            )
    return {}
def _assistant_metadata(
    result,
) -> dict:
    provider_audit = (
        _provider_audit_metadata(
            result
        )
    )
    return {
        "status": result.status,
        "execution_allowed": False,
        "advisory_only": (
            result.metadata.advisory_only
        ),
        "execution_enabled": False,
        "provider": (
            result.metadata.provider
        ),
        "model_name": (
            result.metadata.model_name
        ),
        "provider_latency_ms": (
            provider_audit.get(
                "latency_ms"
            )
        ),
        "provider_error_code": (
            provider_audit.get(
                "error_code"
            )
        ),
        "confidence_score": (
            result.metadata.confidence_score
        ),
        "data_sources": list(
            result.metadata.data_sources
        ),
        "warning_codes": [
            warning.code
            for warning in result.warnings
        ],
    }
def _user_metadata(
    data: AIAssistantRequest,
) -> dict:
    return {
        "symbols": list(data.symbols),
        "portfolio_id": (
            data.portfolio_id
        ),
        "exchange_account_id": (
            data.exchange_account_id
        ),
        "include_user_context": (
            data.include_user_context
        ),
        (
            "include_conversation_"
            "history"
        ): (
            data
            .include_conversation_history
        ),
        (
            "conversation_history_"
            "limit"
        ): (
            data
            .conversation_history_limit
        ),
        "use_external_provider": (
            data.use_external_provider
        ),
    }
@router.post("/contextual-query")
async def answer_contextual_query(
    data: AIAssistantRequest,
    current_user: User = Depends(
        get_current_user
    ),
    service: (
        AIExternalOrchestrationService
    ) = Depends(
        get_context_aware_analysis_service
    ),
    conversation_service: (
        AIConversationService
    ) = Depends(
        get_ai_conversation_service
    ),
):
    analysis_candidate = (
        service.analyze(
            current_user=current_user,
            request=data,
        )
    )
    if isawaitable(
        analysis_candidate
    ):
        result = await analysis_candidate
    else:
        result = analysis_candidate
    response_data = result.model_dump(
        mode="json"
    )
    persistence = {
        "persisted": False,
        "conversation_id": None,
        "user_message_id": None,
        "assistant_message_id": None,
    }
    if data.persist_conversation:
        conversation_id = (
            data.conversation_id
        )
        if conversation_id is None:
            conversation = (
                conversation_service
                .create_conversation(
                    current_user=current_user,
                    data=(
                        AIConversationCreateRequest()
                    ),
                )
            )
            conversation_id = (
                conversation.id
            )
        exchange = (
            conversation_service
            .append_exchange(
                current_user=current_user,
                conversation_id=(
                    conversation_id
                ),
                data=(
                    AIConversationExchangeCreate(
                        user_content=(
                            data.question
                        ),
                        assistant_content=(
                            result.answer
                        ),
                        analysis_type=(
                            data.analysis_type
                        ),
                        user_metadata=(
                            _user_metadata(data)
                        ),
                        assistant_metadata=(
                            _assistant_metadata(
                                result
                            )
                        ),
                    )
                ),
            )
        )
        persistence = {
            "persisted": True,
            "conversation_id": (
                exchange.conversation.id
            ),
            "user_message_id": (
                exchange.user_message.id
            ),
            "assistant_message_id": (
                exchange
                .assistant_message.id
            ),
        }
    response_data["conversation"] = (
        persistence
    )
    return success_response(
        message=(
            "Context-aware AI query "
            "analyzed successfully"
        ),
        data=response_data,
    )
