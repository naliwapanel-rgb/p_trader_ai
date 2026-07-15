from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.exchanges.factory import ExchangeFactory
from app.models.user import User
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