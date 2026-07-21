from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session
from app.api.automation_dependencies import (
    get_automation_runtime,
)
from app.api.dependencies import (
    get_current_user,
)
from app.database.session import (
    get_db,
)
from app.models.user import User
from app.schemas.ai_context import (
    AIContextRequest,
)
from app.services.ai_context_service import (
    AIContextBuilderService,
)
from app.services.automation_runtime_service import (
    AutomationRuntime,
)
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix="/ai-assistant",
    tags=["AI Assistant"],
)
def get_ai_context_builder_service(
    db: Session = Depends(get_db),
    runtime: AutomationRuntime = Depends(
        get_automation_runtime
    ),
) -> AIContextBuilderService:
    return AIContextBuilderService(
        db,
        runtime=runtime,
    )
@router.get("/context")
async def get_user_ai_context(
    portfolio_id: Annotated[
        int | None,
        Query(gt=0),
    ] = None,
    exchange_account_id: Annotated[
        int | None,
        Query(gt=0),
    ] = None,
    include_automation: bool = True,
    current_user: User = Depends(
        get_current_user
    ),
    service: AIContextBuilderService = Depends(
        get_ai_context_builder_service
    ),
):
    request = AIContextRequest(
        portfolio_id=portfolio_id,
        exchange_account_id=(
            exchange_account_id
        ),
        include_automation=(
            include_automation
        ),
    )
    result = service.build(
        current_user=current_user,
        request=request,
    )
    return success_response(
        message=(
            "User-specific AI context "
            "retrieved successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
