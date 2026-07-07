from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.exchange_account import (
    ExchangeAccountCreateRequest,
    ExchangeAccountResponse,
    ExchangeAccountUpdateRequest,
)
from app.services.exchange_account_service import ExchangeAccountService
from app.utils.responses import success_response

router = APIRouter(prefix="/exchange-accounts", tags=["Exchange Accounts"])


@router.get("")
async def list_my_exchange_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = ExchangeAccountService(db).list_accounts(current_user)

    data = [
        ExchangeAccountResponse.model_validate(account).model_dump()
        for account in accounts
    ]

    return success_response(
        message="Exchange accounts retrieved successfully",
        data=data,
    )


@router.get("/{account_id}")
async def get_my_exchange_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).get_account(
        current_user=current_user,
        account_id=account_id,
    )

    return success_response(
        message="Exchange account retrieved successfully",
        data=ExchangeAccountResponse.model_validate(account).model_dump(),
    )


@router.post("")
async def create_my_exchange_account(
    data: ExchangeAccountCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).create_account(
        current_user=current_user,
        data=data,
    )

    return success_response(
        message="Exchange account created successfully",
        data=ExchangeAccountResponse.model_validate(account).model_dump(),
    )


@router.put("/{account_id}")
async def update_my_exchange_account(
    account_id: int,
    data: ExchangeAccountUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = ExchangeAccountService(db).update_account(
        current_user=current_user,
        account_id=account_id,
        data=data,
    )

    return success_response(
        message="Exchange account updated successfully",
        data=ExchangeAccountResponse.model_validate(account).model_dump(),
    )


@router.delete("/{account_id}")
async def delete_my_exchange_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ExchangeAccountService(db).delete_account(
        current_user=current_user,
        account_id=account_id,
    )

    return success_response(
        message="Exchange account deleted successfully",
    )