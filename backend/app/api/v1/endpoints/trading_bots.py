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
from app.schemas.trading_bot import (
    TradingBotCreateRequest,
    TradingBotLifecycleActionResult,
    TradingBotResponse,
    TradingBotStatus,
    TradingBotUpdateRequest,
)
from app.services.trading_bot_lifecycle_service import (
    TradingBotLifecycleService,
)
from app.services.trading_bot_service import (
    TradingBotService,
)
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix="/trading-bots",
    tags=["Trading Bots"],
)
@router.get("")
async def list_my_trading_bots(
    bot_status: (
        TradingBotStatus | None
    ) = Query(
        default=None,
        alias="status",
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
    bots = TradingBotService(
        db
    ).list_bots(
        current_user=current_user,
        bot_status=bot_status,
        limit=limit,
        offset=offset,
    )
    data = [
        TradingBotResponse
        .model_validate(bot)
        .model_dump(mode="json")
        for bot in bots
    ]
    return success_response(
        message=(
            "Trading bots retrieved "
            "successfully"
        ),
        data=data,
    )
@router.post("")
async def create_my_trading_bot(
    data: TradingBotCreateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    bot = TradingBotService(
        db
    ).create_bot(
        current_user=current_user,
        data=data,
    )
    return success_response(
        message=(
            "Trading bot created "
            "successfully"
        ),
        data=(
            TradingBotResponse
            .model_validate(bot)
            .model_dump(mode="json")
        ),
    )
@router.get("/{bot_id}")
async def get_my_trading_bot(
    bot_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    bot = TradingBotService(
        db
    ).get_bot(
        current_user=current_user,
        bot_id=bot_id,
    )
    return success_response(
        message=(
            "Trading bot retrieved "
            "successfully"
        ),
        data=(
            TradingBotResponse
            .model_validate(bot)
            .model_dump(mode="json")
        ),
    )
@router.put("/{bot_id}")
async def update_my_trading_bot(
    bot_id: int,
    data: TradingBotUpdateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    bot = TradingBotService(
        db
    ).update_bot(
        current_user=current_user,
        bot_id=bot_id,
        data=data,
    )
    return success_response(
        message=(
            "Trading bot updated "
            "successfully"
        ),
        data=(
            TradingBotResponse
            .model_validate(bot)
            .model_dump(mode="json")
        ),
    )
@router.delete("/{bot_id}")
async def delete_my_trading_bot(
    bot_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    TradingBotService(
        db
    ).delete_bot(
        current_user=current_user,
        bot_id=bot_id,
    )
    return success_response(
        message=(
            "Trading bot deleted "
            "successfully"
        ),
    )
@router.post("/{bot_id}/prepare")
async def prepare_my_trading_bot(
    bot_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    result = (
        TradingBotLifecycleService(db)
        .prepare_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
    )
    return success_response(
        message=(
            "Trading bot prepared "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/{bot_id}/start")
async def start_my_trading_bot(
    bot_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    result = (
        TradingBotLifecycleService(db)
        .start_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
    )
    return success_response(
        message=(
            "Trading bot started "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/{bot_id}/pause")
async def pause_my_trading_bot(
    bot_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    result = (
        TradingBotLifecycleService(db)
        .pause_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
    )
    return success_response(
        message=(
            "Trading bot paused "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/{bot_id}/resume")
async def resume_my_trading_bot(
    bot_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    result = (
        TradingBotLifecycleService(db)
        .resume_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
    )
    return success_response(
        message=(
            "Trading bot resumed "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.post("/{bot_id}/stop")
async def stop_my_trading_bot(
    bot_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    result = (
        TradingBotLifecycleService(db)
        .stop_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
    )
    return success_response(
        message=(
            "Trading bot stopped "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
