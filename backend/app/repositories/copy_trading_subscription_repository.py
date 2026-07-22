from datetime import (
    UTC,
    datetime,
)
from typing import (
    Any,
)
from sqlalchemy.orm import (
    Session,
)
from app.models.copy_trading_subscription import (
    CopyTradingSubscription,
)
class CopyTradingSubscriptionRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db
    def create(
        self,
        *,
        follower_user_id: int,
        source_template_id: int,
        follower_bot_id: int,
        subscribed_template_version: int,
    ) -> CopyTradingSubscription:
        subscription = (
            CopyTradingSubscription(
                follower_user_id=(
                    follower_user_id
                ),
                source_template_id=(
                    source_template_id
                ),
                follower_bot_id=(
                    follower_bot_id
                ),
                status="ACTIVE",
                execution_mode="PAPER_ONLY",
                subscribed_template_version=(
                    subscribed_template_version
                ),
            )
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    def get_by_id_and_user(
        self,
        *,
        subscription_id: int,
        follower_user_id: int,
    ) -> CopyTradingSubscription | None:
        return (
            self.db.query(
                CopyTradingSubscription
            )
            .filter(
                CopyTradingSubscription.id
                == subscription_id,
                (
                    CopyTradingSubscription
                    .follower_user_id
                    == follower_user_id
                ),
            )
            .first()
        )
    def get_by_follower_bot_and_user(
        self,
        *,
        follower_bot_id: int,
        follower_user_id: int,
    ) -> CopyTradingSubscription | None:
        return (
            self.db.query(
                CopyTradingSubscription
            )
            .filter(
                (
                    CopyTradingSubscription
                    .follower_bot_id
                    == follower_bot_id
                ),
                (
                    CopyTradingSubscription
                    .follower_user_id
                    == follower_user_id
                ),
            )
            .first()
        )
    def list_by_user(
        self,
        *,
        follower_user_id: int,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CopyTradingSubscription]:
        query = (
            self.db.query(
                CopyTradingSubscription
            )
            .filter(
                (
                    CopyTradingSubscription
                    .follower_user_id
                    == follower_user_id
                )
            )
        )
        if status is not None:
            query = query.filter(
                CopyTradingSubscription.status
                == status
            )
        return (
            query.order_by(
                (
                    CopyTradingSubscription
                    .updated_at
                    .desc()
                ),
                (
                    CopyTradingSubscription
                    .id
                    .desc()
                ),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
    def list_active_by_template(
        self,
        *,
        source_template_id: int,
    ) -> list[CopyTradingSubscription]:
        return (
            self.db.query(
                CopyTradingSubscription
            )
            .filter(
                (
                    CopyTradingSubscription
                    .source_template_id
                    == source_template_id
                ),
                CopyTradingSubscription.status
                == "ACTIVE",
            )
            .order_by(
                CopyTradingSubscription.id.asc(),
            )
            .all()
        )
    def update_state(
        self,
        *,
        subscription: (
            CopyTradingSubscription
        ),
        fields: dict[str, Any],
    ) -> CopyTradingSubscription:
        protected = {
            "id",
            "follower_user_id",
            "source_template_id",
            "follower_bot_id",
            "execution_mode",
            "subscribed_template_version",
            "created_at",
        }
        prohibited = protected.intersection(
            fields
        )
        if prohibited:
            names = ", ".join(
                sorted(prohibited)
            )
            raise ValueError(
                "Protected copy-trading "
                "subscription fields cannot "
                f"be updated: {names}"
            )
        for key, value in fields.items():
            setattr(
                subscription,
                key,
                value,
            )
        subscription.updated_at = (
            datetime.now(UTC)
        )
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    def delete(
        self,
        subscription: (
            CopyTradingSubscription
        ),
    ) -> None:
        self.db.delete(subscription)
        self.db.commit()
