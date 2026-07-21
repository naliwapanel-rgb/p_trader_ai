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
from app.schemas.trading_bot_performance import (
    PaperTradingHistoryPositionStatus,
)
from app.services.paper_trading_history_service import (
    PaperTradingHistoryService,
)
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix=(
        "/trading-bots/{bot_id}/"
        "paper-trading"
    ),
    tags=["Trading Bots"],
)
@router.get("/account")
async def get_my_paper_trading_account(
    bot_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    result = (
        PaperTradingHistoryService(db)
        .get_account_summary(
            current_user=current_user,
            bot_id=bot_id,
        )
    )
    return success_response(
        message=(
            "Paper trading account retrieved "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.get("/orders")
async def list_my_paper_trading_orders(
    bot_id: int,
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
    result = (
        PaperTradingHistoryService(db)
        .list_orders(
            current_user=current_user,
            bot_id=bot_id,
            limit=limit,
            offset=offset,
        )
    )
    return success_response(
        message=(
            "Paper trading orders retrieved "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.get("/positions")
async def list_my_paper_trading_positions(
    bot_id: int,
    position_status: (
        PaperTradingHistoryPositionStatus
        | None
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
    result = (
        PaperTradingHistoryService(db)
        .list_positions(
            current_user=current_user,
            bot_id=bot_id,
            position_status=(
                position_status
            ),
            limit=limit,
            offset=offset,
        )
    )
    return success_response(
        message=(
            "Paper trading positions retrieved "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
@router.get("/performance")
async def get_my_paper_trading_performance(
    bot_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    result = (
        PaperTradingHistoryService(db)
        .get_performance(
            current_user=current_user,
            bot_id=bot_id,
        )
    )
    return success_response(
        message=(
            "Paper trading performance "
            "retrieved successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
