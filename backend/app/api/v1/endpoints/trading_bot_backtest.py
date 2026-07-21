from fastapi import (
    APIRouter,
    Depends,
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
from app.schemas.trading_bot_backtest import (
    TradingBotBacktestRequest,
)
from app.services.trading_bot_backtest_service import (
    TradingBotBacktestService,
)
from app.utils.responses import (
    success_response,
)
router = APIRouter(
    prefix="/trading-bots",
    tags=["Trading Bots"],
)
@router.post("/{bot_id}/backtest")
async def run_my_trading_bot_backtest(
    bot_id: int,
    data: TradingBotBacktestRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    result = (
        await TradingBotBacktestService(db)
        .run_backtest(
            current_user=current_user,
            bot_id=bot_id,
            data=data,
        )
    )
    return success_response(
        message=(
            "Trading bot backtest completed "
            "successfully"
        ),
        data=result.model_dump(
            mode="json"
        ),
    )
