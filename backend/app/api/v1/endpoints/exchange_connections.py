from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.exchanges.factory import ExchangeFactory
from app.models.user import User
from app.schemas.exchange_trade import (
    SetPositionTpSlRequest,
    CloseFullPositionRequest,
    ClosePartialPositionRequest,
    ClosePercentagePositionRequest,
)
from app.services.exchange_account_service import ExchangeAccountService
from app.utils.responses import success_response

router = APIRouter(prefix="/exchange-connections", tags=["Exchange Connections"])


@router.post("/{account_id}/test")
async def test_exchange_connection(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).get_account(
        current_user=current_user,
        account_id=account_id,
    )

    client = ExchangeFactory.create_client(account)

    result = await client.test_connection()

    return success_response(
        message="Exchange connection tested successfully",
        data=result,
    )
    
@router.get("/{account_id}/balance")
async def get_exchange_balance(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).get_account(
        current_user=current_user,
        account_id=account_id,
    )

    client = ExchangeFactory.create_client(account)

    result = await client.get_account_balance()
    

    return success_response(
        message="Exchange balance retrieved successfully",
        data=result,
    )


@router.get("/{account_id}/positions")
async def get_exchange_positions(
    account_id: int,
    category: str = "linear",
    settle_coin: str = "USDT",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).get_account(
        current_user=current_user,
        account_id=account_id,
    )

    client = ExchangeFactory.create_client(account)

    result = await client.get_positions(
        category=category,
        settle_coin=settle_coin,
    )

    return success_response(
        message="Exchange positions retrieved successfully",
        data=result,
    )

@router.post("/{account_id}/positions/close-full")
async def close_full_exchange_position(
    account_id: int,
    data: CloseFullPositionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).get_account(
        current_user=current_user,
        account_id=account_id,
    )

    client = ExchangeFactory.create_client(account)

    close_full_method = getattr(
        client,
        "close_full_position",
        None,
    )

    if close_full_method is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Automatic full position close is not "
                "supported for this exchange"
            ),
        )

    result = await close_full_method(
        symbol=data.symbol,
        category=data.category,
        settle_coin=data.settle_coin,
        position_side=data.position_side,
        time_in_force=data.time_in_force,
        client_order_id=data.client_order_id,
        dry_run=data.dry_run,
    )

    return success_response(
        message="Full position close processed successfully",
        data=result,
    )
@router.post("/{account_id}/positions/close-partial")
async def close_partial_exchange_position(
    account_id: int,
    data: ClosePartialPositionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).get_account(
        current_user=current_user,
        account_id=account_id,
    )

    client = ExchangeFactory.create_client(account)

    close_partial_method = getattr(
        client,
        "close_partial_position",
        None,
    )

    if close_partial_method is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Partial position close is not "
                "supported for this exchange"
            ),
        )

    result = await close_partial_method(
        symbol=data.symbol,
        quantity=data.quantity,
        category=data.category,
        settle_coin=data.settle_coin,
        position_side=data.position_side,
        time_in_force=data.time_in_force,
        client_order_id=data.client_order_id,
        dry_run=data.dry_run,
    )

    return success_response(
        message="Partial position close processed successfully",
        data=result,
    )

@router.post(
    "/{account_id}/positions/close-percentage"
)
async def close_percentage_exchange_position(
    account_id: int,
    data: ClosePercentagePositionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).get_account(
        current_user=current_user,
        account_id=account_id,
    )
    client = ExchangeFactory.create_client(account)
    close_percentage_method = getattr(
        client,
        "close_percentage_position",
        None,
    )
    if close_percentage_method is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Percentage position close is not "
                "supported for this exchange"
            ),
        )
    result = await close_percentage_method(
        symbol=data.symbol,
        percentage=data.percentage,
        category=data.category,
        settle_coin=data.settle_coin,
        position_side=data.position_side,
        time_in_force=data.time_in_force,
        client_order_id=data.client_order_id,
        dry_run=data.dry_run,
    )
    return success_response(
        message=(
            "Percentage position close processed "
            "successfully"
        ),
        data=result,
    )


@router.get("/{account_id}/orders/open")
async def get_exchange_open_orders(
    account_id: int,
    category: str = "linear",
    settle_coin: str = "USDT",
    symbol: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).get_account(
        current_user=current_user,
        account_id=account_id,
    )

    client = ExchangeFactory.create_client(account)

    result = await client.get_open_orders(
        category=category,
        settle_coin=settle_coin,
        symbol=symbol,
    )

    return success_response(
        message="Exchange open orders retrieved successfully",
        data=result,
    )
@router.post("/{account_id}/positions/tp-sl")
async def set_exchange_position_tp_sl(
    account_id: int,
    data: SetPositionTpSlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).get_account(
        current_user=current_user,
        account_id=account_id,
    )
    client = ExchangeFactory.create_client(account)
    set_tp_sl_method = getattr(
        client,
        "set_position_tp_sl",
        None,
    )
    if set_tp_sl_method is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Position TP/SL management is not "
                "supported for this exchange"
            ),
        )
    result = await set_tp_sl_method(
        symbol=data.symbol,
        take_profit=data.take_profit,
        stop_loss=data.stop_loss,
        category=data.category,
        settle_coin=data.settle_coin,
        position_side=data.position_side,
        tp_trigger_by=data.tp_trigger_by,
        sl_trigger_by=data.sl_trigger_by,
        dry_run=data.dry_run,
    )
    return success_response(
        message="Position TP/SL processed successfully",
        data=result,
    )

