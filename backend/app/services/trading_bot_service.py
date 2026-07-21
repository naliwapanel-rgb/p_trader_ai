from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.orm import (
    Session,
)
from app.models.trading_bot import (
    TradingBot,
)
from app.models.user import (
    User,
)
from app.repositories.exchange_account_repository import (
    ExchangeAccountRepository,
)
from app.repositories.trading_bot_repository import (
    TradingBotRepository,
)
from app.schemas.trading_bot import (
    TradingBotCreateRequest,
    TradingBotUpdateRequest,
)
ACTIVE_BOT_STATUSES = {
    "STARTING",
    "RUNNING",
    "PAUSED",
}
CRUD_EDITABLE_STATUSES = {
    "DRAFT",
    "STOPPED",
    "ARCHIVED",
}
class TradingBotService:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.bot_repository = (
            TradingBotRepository(db)
        )
        self.exchange_account_repository = (
            ExchangeAccountRepository(db)
        )
    def list_bots(
        self,
        *,
        current_user: User,
        bot_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TradingBot]:
        return (
            self.bot_repository
            .list_by_user(
                user_id=current_user.id,
                status=bot_status,
                limit=limit,
                offset=offset,
            )
        )
    def get_bot(
        self,
        *,
        current_user: User,
        bot_id: int,
    ) -> TradingBot:
        bot = (
            self.bot_repository
            .get_by_id_and_user(
                bot_id=bot_id,
                user_id=current_user.id,
            )
        )
        if bot is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Trading bot not found",
            )
        return bot
    def _validate_exchange_account(
        self,
        *,
        current_user: User,
        account_id: int,
    ):
        account = (
            self.exchange_account_repository
            .get_by_id_and_user(
                account_id=account_id,
                user_id=current_user.id,
            )
        )
        if account is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Exchange account not found"
                ),
            )
        if not account.is_active:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Exchange account is inactive"
                ),
            )
        return account
    def _ensure_name_available(
        self,
        *,
        current_user: User,
        name: str,
        exclude_bot_id: int | None = None,
    ) -> None:
        existing = (
            self.bot_repository
            .get_by_name_and_user(
                name=name,
                user_id=current_user.id,
            )
        )
        if existing is None:
            return
        if (
            exclude_bot_id is not None
            and existing.id
            == exclude_bot_id
        ):
            return
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A trading bot with this name "
                "already exists"
            ),
        )
    def _rollback_safely(self) -> None:
        try:
            self.db.rollback()
        except Exception:
            pass
    def create_bot(
        self,
        *,
        current_user: User,
        data: TradingBotCreateRequest,
    ) -> TradingBot:
        if (
            data.exchange_account_id
            is not None
        ):
            self._validate_exchange_account(
                current_user=current_user,
                account_id=(
                    data.exchange_account_id
                ),
            )
        self._ensure_name_available(
            current_user=current_user,
            name=data.name,
        )
        try:
            return self.bot_repository.create(
                user_id=current_user.id,
                data=data,
            )
        except IntegrityError as error:
            self._rollback_safely()
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "A trading bot with this "
                    "name already exists"
                ),
            ) from error
    def update_bot(
        self,
        *,
        current_user: User,
        bot_id: int,
        data: TradingBotUpdateRequest,
    ) -> TradingBot:
        bot = self.get_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
        if bot.status in ACTIVE_BOT_STATUSES:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Active trading bots cannot "
                    "be modified"
                ),
            )
        fields = data.model_dump(
            exclude_unset=True
        )
        requested_status = fields.get(
            "status"
        )
        if (
            requested_status is not None
            and requested_status
            not in CRUD_EDITABLE_STATUSES
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Use trading bot lifecycle "
                    "controls to enter an active "
                    "status"
                ),
            )
        if (
            "exchange_account_id" in fields
            and fields[
                "exchange_account_id"
            ]
            is not None
        ):
            self._validate_exchange_account(
                current_user=current_user,
                account_id=fields[
                    "exchange_account_id"
                ],
            )
        if "name" in fields:
            self._ensure_name_available(
                current_user=current_user,
                name=fields["name"],
                exclude_bot_id=bot.id,
            )
        try:
            return self.bot_repository.update(
                bot=bot,
                data=data,
            )
        except ValueError as error:
            self._rollback_safely()
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=str(error),
            ) from error
        except IntegrityError as error:
            self._rollback_safely()
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "A trading bot with this "
                    "name already exists"
                ),
            ) from error
    def delete_bot(
        self,
        *,
        current_user: User,
        bot_id: int,
    ) -> None:
        bot = self.get_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
        if bot.status in ACTIVE_BOT_STATUSES:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Active trading bots must be "
                    "stopped before deletion"
                ),
            )
        self.bot_repository.delete(bot)
