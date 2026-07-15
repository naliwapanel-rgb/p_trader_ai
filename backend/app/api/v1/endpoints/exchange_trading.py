from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.exchange_trade import (
    LimitOrderRequest,
    MarketOrderRequest,
)
from app.services.exchange_trading_service import ExchangeTradingService
from app.utils.responses import success_response


router = APIRouter(
    prefix="/exchange-trading",
    tags=["Exchange Trading"],
)


@router.post("/{account_id}/orders/market")
async def place_market_order(
    account_id: int,
    data: MarketOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await ExchangeTradingService(db).place_market_order(
        current_user=current_user,
        account_id=account_id,
        data=data,
    )

    return success_response(
        message="Market order processed successfully",
        data=result,
    )


@router.post("/{account_id}/orders/limit")
async def place_limit_order(
    account_id: int,
    data: LimitOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await ExchangeTradingService(db).place_limit_order(
        current_user=current_user,
        account_id=account_id,
        data=data,
    )

    return success_response(
        message="Limit order processed successfully",
        data=result,
    )