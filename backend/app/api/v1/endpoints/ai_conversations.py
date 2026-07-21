from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
)
from sqlalchemy.orm import Session
from app.api.dependencies import (
    get_current_user,
)
from app.database.session import (
    get_db,
)
from app.models.user import User
from app.schemas.ai_conversation import (
    AIConversationCreateRequest,
    AIConversationUpdateRequest,
)
from app.services.ai_conversation_service import (
    AIConversationService,
)
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix="/ai-assistant/conversations",
    tags=["AI Assistant"],
)
def get_ai_conversation_service(
    db: Session = Depends(get_db),
) -> AIConversationService:
    return AIConversationService(db)
@router.post("")
async def create_ai_conversation(
    data: AIConversationCreateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    service: AIConversationService = Depends(
        get_ai_conversation_service
    ),
):
    result = service.create_conversation(
        current_user=current_user,
        data=data,
    )
    return success_response(
        message=(
            "AI conversation created "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.get("")
async def list_ai_conversations(
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    current_user: User = Depends(
        get_current_user
    ),
    service: AIConversationService = Depends(
        get_ai_conversation_service
    ),
):
    results = service.list_conversations(
        current_user=current_user,
        limit=limit,
        offset=offset,
    )
    return success_response(
        message=(
            "AI conversations retrieved "
            "successfully"
        ),
        data=[
            item.model_dump(mode="json")
            for item in results
        ],
    )
@router.get("/{conversation_id}")
async def get_ai_conversation_history(
    conversation_id: Annotated[
        int,
        Path(gt=0),
    ],
    limit: Annotated[
        int,
        Query(ge=1, le=500),
    ] = 200,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    current_user: User = Depends(
        get_current_user
    ),
    service: AIConversationService = Depends(
        get_ai_conversation_service
    ),
):
    result = service.get_history(
        current_user=current_user,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )
    return success_response(
        message=(
            "AI conversation history "
            "retrieved successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.patch("/{conversation_id}")
async def update_ai_conversation(
    conversation_id: Annotated[
        int,
        Path(gt=0),
    ],
    data: AIConversationUpdateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    service: AIConversationService = Depends(
        get_ai_conversation_service
    ),
):
    result = service.update_conversation(
        current_user=current_user,
        conversation_id=conversation_id,
        data=data,
    )
    return success_response(
        message=(
            "AI conversation updated "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.delete("/{conversation_id}")
async def delete_ai_conversation(
    conversation_id: Annotated[
        int,
        Path(gt=0),
    ],
    current_user: User = Depends(
        get_current_user
    ),
    service: AIConversationService = Depends(
        get_ai_conversation_service
    ),
):
    service.delete_conversation(
        current_user=current_user,
        conversation_id=conversation_id,
    )
    return success_response(
        message=(
            "AI conversation deleted "
            "successfully"
        ),
        data=None,
    )
