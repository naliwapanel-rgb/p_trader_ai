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
from app.models.copy_trading_subscription import (
    CopyTradingSubscription,
)
from app.models.user import (
    User,
)
from app.repositories.copy_trading_subscription_repository import (
    CopyTradingSubscriptionRepository,
)
from app.repositories.strategy_template_repository import (
    StrategyTemplateRepository,
)
from app.repositories.trading_bot_repository import (
    TradingBotRepository,
)
from app.schemas.copy_trading_subscription import (
    CopyTradingSubscriptionCreateRequest,
)
SUBSCRIPTION_ELIGIBLE_BOT_STATUSES = {
    "DRAFT",
    "STOPPED",
}
class CopyTradingSubscriptionService:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.repository = (
            CopyTradingSubscriptionRepository(
                db
            )
        )
        self.template_repository = (
            StrategyTemplateRepository(db)
        )
        self.bot_repository = (
            TradingBotRepository(db)
        )
    def _rollback_safely(self) -> None:
        try:
            self.db.rollback()
        except Exception:
            pass
    def list_subscriptions(
        self,
        *,
        current_user: User,
        subscription_status: (
            str | None
        ) = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CopyTradingSubscription]:
        return self.repository.list_by_user(
            follower_user_id=current_user.id,
            status=subscription_status,
            limit=limit,
            offset=offset,
        )
    def get_subscription(
        self,
        *,
        current_user: User,
        subscription_id: int,
    ) -> CopyTradingSubscription:
        subscription = (
            self.repository
            .get_by_id_and_user(
                subscription_id=(
                    subscription_id
                ),
                follower_user_id=(
                    current_user.id
                ),
            )
        )
        if subscription is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Copy-trading subscription "
                    "not found"
                ),
            )
        return subscription
    @staticmethod
    def _validate_bot_matches_template(
        *,
        bot,
        template,
    ) -> None:
        checks = {
            "strategy_type": (
                bot.strategy_type,
                template.strategy_type,
            ),
            "symbol": (
                bot.symbol,
                template.symbol,
            ),
            "category": (
                bot.category,
                template.category,
            ),
            "timeframe": (
                bot.timeframe,
                template.timeframe,
            ),
            "strategy_config": (
                dict(
                    bot.strategy_config
                    or {}
                ),
                dict(
                    template.strategy_config
                    or {}
                ),
            ),
        }
        mismatched = [
            field
            for field, (
                bot_value,
                template_value,
            )
            in checks.items()
            if bot_value != template_value
        ]
        if mismatched:
            fields = ", ".join(
                mismatched
            )
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Follower bot does not "
                    "match the source strategy "
                    f"template: {fields}"
                ),
            )
    def create_subscription(
        self,
        *,
        current_user: User,
        data: (
            CopyTradingSubscriptionCreateRequest
        ),
    ) -> CopyTradingSubscription:
        template = (
            self.template_repository
            .get_published_by_id(
                template_id=(
                    data.source_template_id
                ),
            )
        )
        if template is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Published source strategy "
                    "template not found"
                ),
            )
        bot = (
            self.bot_repository
            .get_by_id_and_user(
                bot_id=data.follower_bot_id,
                user_id=current_user.id,
            )
        )
        if bot is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Follower trading bot "
                    "not found"
                ),
            )
        if (
            bot.status
            not in (
                SUBSCRIPTION_ELIGIBLE_BOT_STATUSES
            )
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Follower trading bot must "
                    "be in DRAFT or STOPPED "
                    "status before subscribing"
                ),
            )
        if (
            not bot.paper_trading
            or not bot.dry_run
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Follower trading bot must "
                    "enable both paper_trading "
                    "and dry_run"
                ),
            )
        self._validate_bot_matches_template(
            bot=bot,
            template=template,
        )
        existing = (
            self.repository
            .get_by_follower_bot_and_user(
                follower_bot_id=bot.id,
                follower_user_id=(
                    current_user.id
                ),
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Follower trading bot "
                    "already has a copy-trading "
                    "subscription"
                ),
            )
        try:
            return self.repository.create(
                follower_user_id=(
                    current_user.id
                ),
                source_template_id=(
                    template.id
                ),
                follower_bot_id=bot.id,
                subscribed_template_version=(
                    template.version
                ),
            )
        except IntegrityError as error:
            self._rollback_safely()
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Follower trading bot "
                    "already has a copy-trading "
                    "subscription"
                ),
            ) from error
    def pause_subscription(
        self,
        *,
        current_user: User,
        subscription_id: int,
    ) -> CopyTradingSubscription:
        subscription = (
            self.get_subscription(
                current_user=current_user,
                subscription_id=(
                    subscription_id
                ),
            )
        )
        if subscription.status != "ACTIVE":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only active copy-trading "
                    "subscriptions can be paused"
                ),
            )
        return self.repository.update_state(
            subscription=subscription,
            fields={
                "status": "PAUSED",
                "last_error": None,
            },
        )
    def resume_subscription(
        self,
        *,
        current_user: User,
        subscription_id: int,
    ) -> CopyTradingSubscription:
        subscription = (
            self.get_subscription(
                current_user=current_user,
                subscription_id=(
                    subscription_id
                ),
            )
        )
        if subscription.status != "PAUSED":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only paused copy-trading "
                    "subscriptions can be resumed"
                ),
            )
        return self.repository.update_state(
            subscription=subscription,
            fields={
                "status": "ACTIVE",
                "last_error": None,
            },
        )
    def stop_subscription(
        self,
        *,
        current_user: User,
        subscription_id: int,
    ) -> CopyTradingSubscription:
        subscription = (
            self.get_subscription(
                current_user=current_user,
                subscription_id=(
                    subscription_id
                ),
            )
        )
        if subscription.status == "STOPPED":
            return subscription
        return self.repository.update_state(
            subscription=subscription,
            fields={
                "status": "STOPPED",
                "last_error": None,
            },
        )
    def delete_subscription(
        self,
        *,
        current_user: User,
        subscription_id: int,
    ) -> None:
        subscription = (
            self.get_subscription(
                current_user=current_user,
                subscription_id=(
                    subscription_id
                ),
            )
        )
        if subscription.status != "STOPPED":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Copy-trading subscription "
                    "must be stopped before "
                    "deletion"
                ),
            )
        self.repository.delete(
            subscription
        )
