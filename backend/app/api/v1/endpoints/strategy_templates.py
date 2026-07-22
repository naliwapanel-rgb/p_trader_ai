from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import (
    Session,
)
from app.api.dependencies import (
    get_current_user,
)
from app.database.session import (
    get_db,
)
from app.models.user import (
    User,
)
from app.schemas.strategy_template import (
    StrategyTemplateActionResult,
    StrategyTemplateBotCreateRequest,
    StrategyTemplateCreateRequest,
    StrategyTemplateResponse,
    StrategyTemplateStatus,
    StrategyTemplateUpdateRequest,
    StrategyTemplateVisibility,
)
from app.schemas.trading_bot import (
    TradingBotResponse,
)
from app.services.strategy_template_service import (
    StrategyTemplateService,
)
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix="/strategy-templates",
    tags=["Strategy Templates"],
)
def _serialize_template(
    template,
) -> dict:
    return (
        StrategyTemplateResponse
        .model_validate(template)
        .model_dump(mode="json")
    )
def _action_result(
    *,
    action: str,
    previous_status: str,
    template,
) -> dict:
    return (
        StrategyTemplateActionResult(
            action=action,
            previous_status=previous_status,
            status=template.status,
            changed=(
                previous_status
                != template.status
            ),
            template=(
                StrategyTemplateResponse
                .model_validate(template)
            ),
        )
        .model_dump(mode="json")
    )
@router.get("")
async def list_my_strategy_templates(
    template_status: (
        StrategyTemplateStatus | None
    ) = Query(
        default=None,
        alias="status",
    ),
    visibility: (
        StrategyTemplateVisibility | None
    ) = Query(
        default=None,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    templates = (
        StrategyTemplateService(db)
        .list_templates(
            current_user=current_user,
            template_status=(
                template_status
            ),
            visibility=visibility,
            limit=limit,
            offset=offset,
        )
    )
    return success_response(
        message=(
            "Strategy templates retrieved "
            "successfully"
        ),
        data=[
            _serialize_template(template)
            for template in templates
        ],
    )
@router.get("/public")
async def list_public_strategy_templates(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    templates = (
        StrategyTemplateService(db)
        .list_public_templates(
            limit=limit,
            offset=offset,
        )
    )
    return success_response(
        message=(
            "Public strategy templates "
            "retrieved successfully"
        ),
        data=[
            _serialize_template(template)
            for template in templates
        ],
    )
@router.post("")
async def create_my_strategy_template(
    data: StrategyTemplateCreateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    template = (
        StrategyTemplateService(db)
        .create_template(
            current_user=current_user,
            data=data,
        )
    )
    return success_response(
        message=(
            "Strategy template created "
            "successfully"
        ),
        data=_serialize_template(
            template
        ),
    )
@router.get("/{template_id}")
async def get_my_strategy_template(
    template_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    template = (
        StrategyTemplateService(db)
        .get_template(
            current_user=current_user,
            template_id=template_id,
        )
    )
    return success_response(
        message=(
            "Strategy template retrieved "
            "successfully"
        ),
        data=_serialize_template(
            template
        ),
    )
@router.put("/{template_id}")
async def update_my_strategy_template(
    template_id: int,
    data: StrategyTemplateUpdateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    template = (
        StrategyTemplateService(db)
        .update_template(
            current_user=current_user,
            template_id=template_id,
            data=data,
        )
    )
    return success_response(
        message=(
            "Strategy template updated "
            "successfully"
        ),
        data=_serialize_template(
            template
        ),
    )
@router.delete("/{template_id}")
async def delete_my_strategy_template(
    template_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    (
        StrategyTemplateService(db)
        .delete_template(
            current_user=current_user,
            template_id=template_id,
        )
    )
    return success_response(
        message=(
            "Strategy template deleted "
            "successfully"
        ),
        data=None,
    )
@router.post("/{template_id}/publish")
async def publish_my_strategy_template(
    template_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = StrategyTemplateService(
        db
    )
    existing = service.get_template(
        current_user=current_user,
        template_id=template_id,
    )
    previous_status = existing.status
    template = service.publish_template(
        current_user=current_user,
        template_id=template_id,
    )
    return success_response(
        message=(
            "Strategy template published "
            "successfully"
        ),
        data=_action_result(
            action="PUBLISH",
            previous_status=previous_status,
            template=template,
        ),
    )
@router.post("/{template_id}/unpublish")
async def unpublish_my_strategy_template(
    template_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = StrategyTemplateService(
        db
    )
    existing = service.get_template(
        current_user=current_user,
        template_id=template_id,
    )
    previous_status = existing.status
    template = service.unpublish_template(
        current_user=current_user,
        template_id=template_id,
    )
    return success_response(
        message=(
            "Strategy template unpublished "
            "successfully"
        ),
        data=_action_result(
            action="UNPUBLISH",
            previous_status=previous_status,
            template=template,
        ),
    )
@router.post("/{template_id}/archive")
async def archive_my_strategy_template(
    template_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = StrategyTemplateService(
        db
    )
    existing = service.get_template(
        current_user=current_user,
        template_id=template_id,
    )
    previous_status = existing.status
    template = service.archive_template(
        current_user=current_user,
        template_id=template_id,
    )
    return success_response(
        message=(
            "Strategy template archived "
            "successfully"
        ),
        data=_action_result(
            action="ARCHIVE",
            previous_status=previous_status,
            template=template,
        ),
    )
@router.post("/{template_id}/restore")
async def restore_my_strategy_template(
    template_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = StrategyTemplateService(
        db
    )
    existing = service.get_template(
        current_user=current_user,
        template_id=template_id,
    )
    previous_status = existing.status
    template = service.restore_template(
        current_user=current_user,
        template_id=template_id,
    )
    return success_response(
        message=(
            "Strategy template restored "
            "successfully"
        ),
        data=_action_result(
            action="RESTORE",
            previous_status=previous_status,
            template=template,
        ),
    )
@router.post("/{template_id}/create-bot")
async def create_bot_from_strategy_template(
    template_id: int,
    data: StrategyTemplateBotCreateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    bot = (
        StrategyTemplateService(db)
        .create_bot_from_template(
            current_user=current_user,
            template_id=template_id,
            data=data,
        )
    )
    return success_response(
        message=(
            "Trading bot created from "
            "strategy template successfully"
        ),
        data=(
            TradingBotResponse
            .model_validate(bot)
            .model_dump(mode="json")
        ),
    )
