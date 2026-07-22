from collections.abc import (
    Callable,
)
from copy import (
    deepcopy,
)
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
from app.repositories.copy_trading_subscription_repository import (
    CopyTradingSubscriptionRepository,
)
from app.repositories.strategy_template_repository import (
    StrategyTemplateRepository,
)
from app.repositories.trading_bot_repository import (
    TradingBotRepository,
)
from app.schemas.copy_trading_mirroring import (
    CopyTradingMirrorBatchResult,
    CopyTradingMirrorItemResult,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyDecision,
)
from app.services.paper_trading_engine import (
    PaperTradingEngine,
)
PaperEngineFactory = Callable[
    [Session],
    PaperTradingEngine,
]
class CopyTradingDecisionMirrorService:
    FOLLOWER_BOT_STATUSES = frozenset({
        "DRAFT",
        "STOPPED",
    })
    def __init__(
        self,
        db: Session,
        *,
        subscription_repository: (
            CopyTradingSubscriptionRepository
            | None
        ) = None,
        template_repository: (
            StrategyTemplateRepository
            | None
        ) = None,
        bot_repository: (
            TradingBotRepository | None
        ) = None,
        paper_engine_factory: (
            PaperEngineFactory | None
        ) = None,
    ):
        self.db = db
        self.subscription_repository = (
            subscription_repository
            or (
                CopyTradingSubscriptionRepository(
                    db
                )
            )
        )
        self.template_repository = (
            template_repository
            or StrategyTemplateRepository(db)
        )
        self.bot_repository = (
            bot_repository
            or TradingBotRepository(db)
        )
        self.paper_engine_factory = (
            paper_engine_factory
            or (
                lambda session:
                PaperTradingEngine(session)
            )
        )
    @staticmethod
    def _error_text(
        error: BaseException,
    ) -> str:
        message = str(error).strip()
        return (
            message
            or error.__class__.__name__
        )[:4000]
    def _rollback_safely(self) -> None:
        try:
            self.db.rollback()
        except Exception:
            pass
    @staticmethod
    def _utc_timestamp(
        value: datetime,
    ) -> datetime:
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            return value.replace(
                tzinfo=UTC
            )
        return value.astimezone(UTC)
    @classmethod
    def _already_mirrored(
        cls,
        *,
        subscription,
        evaluated_at: datetime,
    ) -> bool:
        if (
            subscription.last_mirrored_at
            is None
        ):
            return False
        previous = cls._utc_timestamp(
            subscription.last_mirrored_at
        )
        current = cls._utc_timestamp(
            evaluated_at
        )
        return previous >= current
    @staticmethod
    def _matching_fields(
        *,
        bot,
        template,
    ) -> list[str]:
        comparisons = {
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
        return [
            field
            for field, (
                bot_value,
                template_value,
            )
            in comparisons.items()
            if bot_value != template_value
        ]
    @staticmethod
    def _execution_payload(
        execution,
    ) -> dict[str, Any]:
        model_dump = getattr(
            execution,
            "model_dump",
            None,
        )
        if callable(model_dump):
            return model_dump(
                mode="json"
            )
        if isinstance(
            execution,
            dict,
        ):
            return dict(execution)
        return {
            "outcome": getattr(
                execution,
                "outcome",
                "UNKNOWN",
            ),
        }
    def _record_subscription_error(
        self,
        *,
        subscription,
        message: str,
    ) -> None:
        try:
            (
                self.subscription_repository
                .update_state(
                    subscription=subscription,
                    fields={
                        "last_error": message,
                    },
                )
            )
        except Exception:
            self._rollback_safely()
    @staticmethod
    def _item_result(
        *,
        subscription,
        outcome: str,
        message: str,
        paper_execution: (
            dict[str, Any] | None
        ) = None,
    ) -> CopyTradingMirrorItemResult:
        return CopyTradingMirrorItemResult(
            subscription_id=(
                subscription.id
            ),
            follower_user_id=(
                subscription
                .follower_user_id
            ),
            follower_bot_id=(
                subscription.follower_bot_id
            ),
            outcome=outcome,
            message=message,
            paper_execution=paper_execution,
        )
    @staticmethod
    def _mirrored_decision(
        *,
        subscription,
        source_template_id: int,
        decision: TradingBotStrategyDecision,
    ) -> TradingBotStrategyDecision:
        metadata = deepcopy(
            decision.metadata
            or {}
        )
        metadata["copy_trading"] = {
            "subscription_id": (
                subscription.id
            ),
            "source_template_id": (
                source_template_id
            ),
            "execution_mode": "PAPER_ONLY",
        }
        reason = (
            "Copy-trading mirror: "
            + decision.reason
        )[:1000]
        return (
            TradingBotStrategyDecision
            .model_validate({
                "action": decision.action,
                "confidence": (
                    decision.confidence
                ),
                "reason": reason,
                "reference_price": (
                    decision.reference_price
                ),
                "evaluated_at": (
                    decision.evaluated_at
                ),
                "metadata": metadata,
            })
        )
    def mirror_decision(
        self,
        *,
        source_template_id: int,
        decision: (
            TradingBotStrategyDecision
            | dict[str, Any]
        ),
    ) -> CopyTradingMirrorBatchResult:
        validated_decision = (
            TradingBotStrategyDecision
            .model_validate(decision)
        )
        evaluated_at = (
            validated_decision.evaluated_at
        )
        if (
            evaluated_at.tzinfo is None
            or evaluated_at.utcoffset()
            is None
        ):
            raise ValueError(
                "Copy-trading decision "
                "evaluated_at must include "
                "a timezone"
            )
        template = (
            self.template_repository
            .get_published_by_id(
                template_id=(
                    source_template_id
                ),
            )
        )
        if template is None:
            raise ValueError(
                "Published source strategy "
                "template was not found"
            )
        subscriptions = (
            self.subscription_repository
            .list_active_by_template(
                source_template_id=(
                    template.id
                ),
            )
        )
        results = []
        for subscription in subscriptions:
            if (
                subscription
                .subscribed_template_version
                != template.version
            ):
                message = (
                    "Subscription template "
                    "version is stale"
                )
                self._record_subscription_error(
                    subscription=subscription,
                    message=message,
                )
                results.append(
                    self._item_result(
                        subscription=(
                            subscription
                        ),
                        outcome="SKIPPED",
                        message=message,
                    )
                )
                continue
            if self._already_mirrored(
                subscription=subscription,
                evaluated_at=evaluated_at,
            ):
                results.append(
                    self._item_result(
                        subscription=(
                            subscription
                        ),
                        outcome="SKIPPED",
                        message=(
                            "Decision was already "
                            "mirrored"
                        ),
                    )
                )
                continue
            bot = (
                self.bot_repository
                .get_by_id_and_user(
                    bot_id=(
                        subscription
                        .follower_bot_id
                    ),
                    user_id=(
                        subscription
                        .follower_user_id
                    ),
                )
            )
            if bot is None:
                message = (
                    "Follower trading bot "
                    "was not found"
                )
                self._record_subscription_error(
                    subscription=subscription,
                    message=message,
                )
                results.append(
                    self._item_result(
                        subscription=(
                            subscription
                        ),
                        outcome="FAILED",
                        message=message,
                    )
                )
                continue
            if (
                bot.status
                not in (
                    self.FOLLOWER_BOT_STATUSES
                )
            ):
                message = (
                    "Follower trading bot must "
                    "remain DRAFT or STOPPED "
                    "during mirrored execution"
                )
                self._record_subscription_error(
                    subscription=subscription,
                    message=message,
                )
                results.append(
                    self._item_result(
                        subscription=(
                            subscription
                        ),
                        outcome="SKIPPED",
                        message=message,
                    )
                )
                continue
            if (
                not bot.paper_trading
                or not bot.dry_run
            ):
                message = (
                    "Follower trading bot must "
                    "enable both paper_trading "
                    "and dry_run"
                )
                self._record_subscription_error(
                    subscription=subscription,
                    message=message,
                )
                results.append(
                    self._item_result(
                        subscription=(
                            subscription
                        ),
                        outcome="SKIPPED",
                        message=message,
                    )
                )
                continue
            mismatched = (
                self._matching_fields(
                    bot=bot,
                    template=template,
                )
            )
            if mismatched:
                message = (
                    "Follower trading bot no "
                    "longer matches the source "
                    "template: "
                    + ", ".join(mismatched)
                )
                self._record_subscription_error(
                    subscription=subscription,
                    message=message,
                )
                results.append(
                    self._item_result(
                        subscription=(
                            subscription
                        ),
                        outcome="SKIPPED",
                        message=message,
                    )
                )
                continue
            mirrored_decision = (
                self._mirrored_decision(
                    subscription=subscription,
                    source_template_id=(
                        template.id
                    ),
                    decision=(
                        validated_decision
                    ),
                )
            )
            try:
                paper_engine = (
                    self.paper_engine_factory(
                        self.db
                    )
                )
                execution = (
                    paper_engine.execute(
                        bot=bot,
                        decision=(
                            mirrored_decision
                        ),
                    )
                )
                execution_payload = (
                    self._execution_payload(
                        execution
                    )
                )
                (
                    self.subscription_repository
                    .update_state(
                        subscription=(
                            subscription
                        ),
                        fields={
                            "last_mirrored_at": (
                                evaluated_at
                            ),
                            "last_error": None,
                        },
                    )
                )
                results.append(
                    self._item_result(
                        subscription=(
                            subscription
                        ),
                        outcome="EXECUTED",
                        message=(
                            "Decision mirrored "
                            "to paper trading"
                        ),
                        paper_execution=(
                            execution_payload
                        ),
                    )
                )
            except Exception as error:
                self._rollback_safely()
                message = self._error_text(
                    error
                )
                self._record_subscription_error(
                    subscription=subscription,
                    message=message,
                )
                results.append(
                    self._item_result(
                        subscription=(
                            subscription
                        ),
                        outcome="FAILED",
                        message=message,
                    )
                )
        return CopyTradingMirrorBatchResult(
            source_template_id=(
                template.id
            ),
            action=(
                validated_decision.action
            ),
            evaluated_at=evaluated_at,
            scanned_count=len(results),
            executed_count=sum(
                result.outcome == "EXECUTED"
                for result in results
            ),
            skipped_count=sum(
                result.outcome == "SKIPPED"
                for result in results
            ),
            failed_count=sum(
                result.outcome == "FAILED"
                for result in results
            ),
            results=results,
        )
