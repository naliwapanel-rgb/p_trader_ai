from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.exchange_trade import (
    AmendOrderRequest,
    CancelOrderRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    PositionTpSlRequest,
    StopLimitOrderRequest,
    StopMarketOrderRequest,
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
@router.post("/{account_id}/orders/stop-market")
async def place_stop_market_order(
    account_id: int,
    data: StopMarketOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await ExchangeTradingService(
        db
    ).place_stop_market_order(
        current_user=current_user,
        account_id=account_id,
        data=data,
    )

    return success_response(
        message="Stop-market order processed successfully",
        data=result,
    )
@router.post("/{account_id}/positions/tpsl")
async def set_position_tpsl(
    account_id: int,
    data: PositionTpSlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await ExchangeTradingService(
        db
    ).set_position_tpsl(
        current_user=current_user,
        account_id=account_id,
        data=data,
    )

    return success_response(
        message="Position TP/SL processed successfully",
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
@router.post("/{account_id}/orders/cancel")
async def cancel_order(
    account_id: int,
    data: CancelOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await ExchangeTradingService(db).cancel_order(
        current_user=current_user,
        account_id=account_id,
        data=data,
    )

    return success_response(
        message="Order cancellation processed successfully",
        data=result,
    )


@router.post("/{account_id}/orders/amend")
async def amend_order(
    account_id: int,
    data: AmendOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await ExchangeTradingService(db).amend_order(
        current_user=current_user,
        account_id=account_id,
        data=data,
    )

    return success_response(
        message="Order amendment processed successfully",
        data=result,
    )