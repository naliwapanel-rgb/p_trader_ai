from sqlalchemy.orm import Session

from app.models.exchange_account import ExchangeAccount


class ExchangeAccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int) -> list[ExchangeAccount]:
        return (
            self.db.query(ExchangeAccount)
            .filter(ExchangeAccount.user_id == user_id)
            .all()
        )

    def get_by_id_and_user(
        self,
        account_id: int,
        user_id: int,
    ) -> ExchangeAccount | None:
        return (
            self.db.query(ExchangeAccount)
            .filter(
                ExchangeAccount.id == account_id,
                ExchangeAccount.user_id == user_id,
            )
            .first()
        )

    def create(
        self,
        user_id: int,
        exchange_name: str,
        account_name: str,
        encrypted_api_key: str,
        encrypted_api_secret: str,
        is_testnet: bool,
    ) -> ExchangeAccount:

        account = ExchangeAccount(
            user_id=user_id,
            exchange_name=exchange_name,
            account_name=account_name,
            encrypted_api_key=encrypted_api_key,
            encrypted_api_secret=encrypted_api_secret,
            is_testnet=is_testnet,
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        return account

    def update(self, account: ExchangeAccount, **fields) -> ExchangeAccount:
        for key, value in fields.items():
            if value is not None:
                setattr(account, key, value)

        self.db.commit()
        self.db.refresh(account)

        return account

    def delete(self, account: ExchangeAccount) -> None:
        self.db.delete(account)
        self.db.commit()