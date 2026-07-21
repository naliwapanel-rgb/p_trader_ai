from collections.abc import (
    Callable,
)
from datetime import (
    UTC,
    datetime,
)
from fastapi import (
    HTTPException,
    status,
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
    TradingBotLifecycleActionResult,
    TradingBotResponse,
)
LifecycleClock = Callable[[], datetime]
class TradingBotLifecycleService:
    def __init__(
        self,
        db: Session,
        *,
        clock: LifecycleClock | None = None,
    ):
        self.bot_repository = (
            TradingBotRepository(db)
        )
        self.exchange_account_repository = (
            ExchangeAccountRepository(db)
        )
        self.clock = (
            clock
            or (
                lambda: datetime.now(UTC)
            )
        )
    def _get_bot(
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
    @staticmethod
    def _conflict(
        *,
        action: str,
        bot: TradingBot,
    ) -> None:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                f"Cannot {action} trading bot "
                f"while status is {bot.status}"
            ),
        )
    def _validate_ready(
        self,
        *,
        current_user: User,
        bot: TradingBot,
    ) -> None:
        if bot.exchange_account_id is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Trading bot requires an "
                    "exchange account before "
                    "starting"
                ),
            )
        account = (
            self.exchange_account_repository
            .get_by_id_and_user(
                account_id=(
                    bot.exchange_account_id
                ),
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
        if (
            not bot.paper_trading
            and not bot.dry_run
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Trading bot execution safety "
                    "is not enabled"
                ),
            )
    @staticmethod
    def _result(
        *,
        action: str,
        previous_status: str,
        changed: bool,
        bot: TradingBot,
    ) -> TradingBotLifecycleActionResult:
        return TradingBotLifecycleActionResult(
            action=action,
            previous_status=previous_status,
            status=bot.status,
            changed=changed,
            bot=(
                TradingBotResponse
                .model_validate(bot)
            ),
        )
    def prepare_bot(
        self,
        *,
        current_user: User,
        bot_id: int,
    ) -> TradingBotLifecycleActionResult:
        bot = self._get_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
        previous_status = bot.status
        if bot.status == "STOPPED":
            return self._result(
                action="PREPARE",
                previous_status=(
                    previous_status
                ),
                changed=False,
                bot=bot,
            )
        if bot.status != "DRAFT":
            self._conflict(
                action="prepare",
                bot=bot,
            )
        now = self.clock()
        bot = (
            self.bot_repository
            .save_lifecycle(
                bot=bot,
                status="STOPPED",
                updated_at=now,
                stopped_at=now,
                last_error=None,
            )
        )
        return self._result(
            action="PREPARE",
            previous_status=previous_status,
            changed=True,
            bot=bot,
        )
    def start_bot(
        self,
        *,
        current_user: User,
        bot_id: int,
    ) -> TradingBotLifecycleActionResult:
        bot = self._get_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
        previous_status = bot.status
        if bot.status == "RUNNING":
            return self._result(
                action="START",
                previous_status=(
                    previous_status
                ),
                changed=False,
                bot=bot,
            )
        if bot.status not in {
            "DRAFT",
            "STOPPED",
        }:
            self._conflict(
                action="start",
                bot=bot,
            )
        self._validate_ready(
            current_user=current_user,
            bot=bot,
        )
        now = self.clock()
        if bot.status == "DRAFT":
            bot = (
                self.bot_repository
                .save_lifecycle(
                    bot=bot,
                    status="STOPPED",
                    updated_at=now,
                    stopped_at=now,
                    last_error=None,
                )
            )
        bot = (
            self.bot_repository
            .save_lifecycle(
                bot=bot,
                status="STARTING",
                updated_at=now,
                stopped_at=None,
                last_error=None,
            )
        )
        bot = (
            self.bot_repository
            .save_lifecycle(
                bot=bot,
                status="RUNNING",
                updated_at=now,
                started_at=now,
                stopped_at=None,
                last_error=None,
            )
        )
        return self._result(
            action="START",
            previous_status=previous_status,
            changed=True,
            bot=bot,
        )
    def pause_bot(
        self,
        *,
        current_user: User,
        bot_id: int,
    ) -> TradingBotLifecycleActionResult:
        bot = self._get_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
        previous_status = bot.status
        if bot.status == "PAUSED":
            return self._result(
                action="PAUSE",
                previous_status=(
                    previous_status
                ),
                changed=False,
                bot=bot,
            )
        if bot.status != "RUNNING":
            self._conflict(
                action="pause",
                bot=bot,
            )
        bot = (
            self.bot_repository
            .save_lifecycle(
                bot=bot,
                status="PAUSED",
                updated_at=self.clock(),
            )
        )
        return self._result(
            action="PAUSE",
            previous_status=previous_status,
            changed=True,
            bot=bot,
        )
    def resume_bot(
        self,
        *,
        current_user: User,
        bot_id: int,
    ) -> TradingBotLifecycleActionResult:
        bot = self._get_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
        previous_status = bot.status
        if bot.status == "RUNNING":
            return self._result(
                action="RESUME",
                previous_status=(
                    previous_status
                ),
                changed=False,
                bot=bot,
            )
        if bot.status != "PAUSED":
            self._conflict(
                action="resume",
                bot=bot,
            )
        self._validate_ready(
            current_user=current_user,
            bot=bot,
        )
        bot = (
            self.bot_repository
            .save_lifecycle(
                bot=bot,
                status="RUNNING",
                updated_at=self.clock(),
                stopped_at=None,
                last_error=None,
            )
        )
        return self._result(
            action="RESUME",
            previous_status=previous_status,
            changed=True,
            bot=bot,
        )
    def stop_bot(
        self,
        *,
        current_user: User,
        bot_id: int,
    ) -> TradingBotLifecycleActionResult:
        bot = self._get_bot(
            current_user=current_user,
            bot_id=bot_id,
        )
        previous_status = bot.status
        if bot.status == "STOPPED":
            return self._result(
                action="STOP",
                previous_status=(
                    previous_status
                ),
                changed=False,
                bot=bot,
            )
        if bot.status not in {
            "DRAFT",
            "STARTING",
            "RUNNING",
            "PAUSED",
            "ERROR",
        }:
            self._conflict(
                action="stop",
                bot=bot,
            )
        now = self.clock()
        bot = (
            self.bot_repository
            .save_lifecycle(
                bot=bot,
                status="STOPPED",
                updated_at=now,
                stopped_at=now,
            )
        )
        return self._result(
            action="STOP",
            previous_status=previous_status,
            changed=True,
            bot=bot,
        )
