from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.encryption import encrypt_value
from app.models.user import User
from app.repositories.exchange_account_repository import ExchangeAccountRepository
from app.schemas.exchange_account import (
    ExchangeAccountCreateRequest,
    ExchangeAccountUpdateRequest,
)


SUPPORTED_EXCHANGES = {"BYBIT", "BINANCE", "MEXC", "GATEIO"}


class ExchangeAccountService:
    def __init__(self, db: Session):
        self.exchange_account_repository = ExchangeAccountRepository(db)

    def list_accounts(self, current_user: User):
        return self.exchange_account_repository.list_by_user(current_user.id)

    def get_account(
        self,
        current_user: User,
        account_id: int,
    ):
        account = self.exchange_account_repository.get_by_id_and_user(
            account_id=account_id,
            user_id=current_user.id,
        )

        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exchange account not found",
            )

        return account

    def create_account(
        self,
        current_user: User,
        data: ExchangeAccountCreateRequest,
    ):
        exchange_name = data.exchange_name.upper()

        if exchange_name not in SUPPORTED_EXCHANGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported exchange",
            )

        return self.exchange_account_repository.create(
            user_id=current_user.id,
            exchange_name=exchange_name,
            account_name=data.account_name,
            encrypted_api_key=encrypt_value(data.api_key),
            encrypted_api_secret=encrypt_value(data.api_secret),
            is_testnet=data.is_testnet,
        )

    def update_account(
        self,
        current_user: User,
        account_id: int,
        data: ExchangeAccountUpdateRequest,
    ):
        account = self.get_account(
            current_user=current_user,
            account_id=account_id,
        )

        update_data = data.model_dump()

        if update_data.get("api_key") is not None:
            update_data["encrypted_api_key"] = encrypt_value(update_data.pop("api_key"))
        else:
            update_data.pop("api_key", None)

        if update_data.get("api_secret") is not None:
            update_data["encrypted_api_secret"] = encrypt_value(update_data.pop("api_secret"))
        else:
            update_data.pop("api_secret", None)

        return self.exchange_account_repository.update(
            account,
            **update_data,
        )

    def delete_account(
        self,
        current_user: User,
        account_id: int,
    ) -> None:
        account = self.get_account(
            current_user=current_user,
            account_id=account_id,
        )

        self.exchange_account_repository.delete(account)