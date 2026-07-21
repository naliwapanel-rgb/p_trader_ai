from fastapi import (
    APIRouter,
    Depends,
)
from app.api.dependencies import (
    get_current_user,
)
from app.api.v1.endpoints.ai_context import (
    get_ai_context_builder_service,
)
from app.models.user import User
from app.schemas.ai_assistant import (
    AIAssistantRequest,
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
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix="/ai-assistant",
    tags=["AI Assistant"],
)
def get_context_aware_analysis_service(
    context_builder: (
        AIContextBuilderService
    ) = Depends(
        get_ai_context_builder_service
    ),
) -> AIContextAwareAnalysisService:
    return AIContextAwareAnalysisService(
        context_builder=(
            context_builder
        ),
        analysis_service=(
            DeterministicAIAnalysisService()
        ),
    )
@router.post("/contextual-query")
async def answer_contextual_query(
    data: AIAssistantRequest,
    current_user: User = Depends(
        get_current_user
    ),
    service: (
        AIContextAwareAnalysisService
    ) = Depends(
        get_context_aware_analysis_service
    ),
):
    result = service.analyze(
        current_user=current_user,
        request=data,
    )
    return success_response(
        message=(
            "Context-aware AI query "
            "analyzed successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
