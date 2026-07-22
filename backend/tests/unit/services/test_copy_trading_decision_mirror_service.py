from datetime import (
    UTC,
    datetime,
    timedelta,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    MagicMock,
)
import pytest
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyDecision,
)
from app.services.copy_trading_decision_mirror_service import (
    CopyTradingDecisionMirrorService,
)
NOW = datetime(
    2026,
    7,
    22,
    16,
    0,
    tzinfo=UTC,
)
def build_template(
    *,
    version=3,
):
    return SimpleNamespace(
        id=20,
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        strategy_config={
            "buy_change_percent_24h": 1.0,
        },
        version=version,
    )
def build_subscription(
    *,
    subscription_id=40,
    follower_user_id=7,
    follower_bot_id=30,
    template_version=3,
    last_mirrored_at=None,
):
    return SimpleNamespace(
        id=subscription_id,
        follower_user_id=(
            follower_user_id
        ),
        source_template_id=20,
        follower_bot_id=(
            follower_bot_id
        ),
        status="ACTIVE",
        execution_mode="PAPER_ONLY",
        subscribed_template_version=(
            template_version
        ),
        last_error=None,
        last_mirrored_at=(
            last_mirrored_at
        ),
    )
def build_bot(
    *,
    bot_id=30,
    user_id=7,
    status="STOPPED",
    paper_trading=True,
    dry_run=True,
):
    return SimpleNamespace(
        id=bot_id,
        user_id=user_id,
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        strategy_config={
            "buy_change_percent_24h": 1.0,
        },
        status=status,
        paper_trading=paper_trading,
        dry_run=dry_run,
    )
def build_decision(
    *,
    action="BUY",
    evaluated_at=NOW,
):
    return TradingBotStrategyDecision(
        action=action,
        confidence=0.8,
        reason="Leader strategy decision",
        reference_price=60000,
        evaluated_at=evaluated_at,
        metadata={
            "symbol": "BTCUSDT",
        },
    )
def build_service(
    *,
    template=None,
    subscriptions=None,
    bots=None,
):
    db = MagicMock()
    subscription_repository = (
        MagicMock()
    )
    template_repository = MagicMock()
    bot_repository = MagicMock()
    paper_engine = MagicMock()
    template_repository.get_published_by_id.return_value = (
        template
    )
    subscription_repository.list_active_by_template.return_value = (
        list(subscriptions or [])
    )
    bot_map = {
        (
            bot.user_id,
            bot.id,
        ): bot
        for bot in (bots or [])
    }
    def get_bot(
        *,
        bot_id,
        user_id,
    ):
        return bot_map.get(
            (
                user_id,
                bot_id,
            )
        )
    bot_repository.get_by_id_and_user.side_effect = (
        get_bot
    )
    def update_state(
        *,
        subscription,
        fields,
    ):
        for key, value in fields.items():
            setattr(
                subscription,
                key,
                value,
            )
        return subscription
    subscription_repository.update_state.side_effect = (
        update_state
    )
    paper_engine.execute.return_value = {
        "outcome": "OPENED",
        "decision_action": "BUY",
    }
    service = (
        CopyTradingDecisionMirrorService(
            db,
            subscription_repository=(
                subscription_repository
            ),
            template_repository=(
                template_repository
            ),
            bot_repository=bot_repository,
            paper_engine_factory=(
                lambda session: paper_engine
            ),
        )
    )
    return SimpleNamespace(
        service=service,
        db=db,
        subscription_repository=(
            subscription_repository
        ),
        template_repository=(
            template_repository
        ),
        bot_repository=bot_repository,
        paper_engine=paper_engine,
    )
def test_requires_published_template():
    context = build_service(
        template=None
    )
    with pytest.raises(
        ValueError,
        match="Published",
    ):
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
def test_empty_subscription_batch():
    context = build_service(
        template=build_template(),
        subscriptions=[],
    )
    result = (
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
    )
    assert result.scanned_count == 0
    assert result.executed_count == 0
    assert result.skipped_count == 0
    assert result.failed_count == 0
def test_executes_safe_follower():
    subscription = build_subscription()
    bot = build_bot()
    context = build_service(
        template=build_template(),
        subscriptions=[subscription],
        bots=[bot],
    )
    result = (
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
    )
    assert result.executed_count == 1
    assert result.skipped_count == 0
    assert result.failed_count == 0
    context.paper_engine.execute.assert_called_once()
    _, kwargs = (
        context.paper_engine
        .execute
        .call_args
    )
    assert kwargs["bot"] is bot
    mirrored = kwargs["decision"]
    assert mirrored.action == "BUY"
    assert (
        mirrored.metadata[
            "copy_trading"
        ]["subscription_id"]
        == 40
    )
    assert (
        subscription.last_mirrored_at
        == NOW
    )
    assert subscription.last_error is None
def test_duplicate_decision_is_skipped():
    subscription = build_subscription(
        last_mirrored_at=NOW
    )
    context = build_service(
        template=build_template(),
        subscriptions=[subscription],
        bots=[build_bot()],
    )
    result = (
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
    )
    assert result.skipped_count == 1
    context.paper_engine.execute.assert_not_called()
def test_older_decision_is_skipped():
    subscription = build_subscription(
        last_mirrored_at=(
            NOW + timedelta(minutes=1)
        )
    )
    context = build_service(
        template=build_template(),
        subscriptions=[subscription],
        bots=[build_bot()],
    )
    result = (
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
    )
    assert result.skipped_count == 1
    context.paper_engine.execute.assert_not_called()
def test_stale_template_version_is_skipped():
    subscription = build_subscription(
        template_version=2
    )
    context = build_service(
        template=build_template(
            version=3
        ),
        subscriptions=[subscription],
        bots=[build_bot()],
    )
    result = (
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
    )
    assert result.skipped_count == 1
    assert "stale" in (
        result.results[0]
        .message
        .lower()
    )
    context.paper_engine.execute.assert_not_called()
def test_running_follower_is_skipped():
    subscription = build_subscription()
    context = build_service(
        template=build_template(),
        subscriptions=[subscription],
        bots=[
            build_bot(
                status="RUNNING"
            )
        ],
    )
    result = (
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
    )
    assert result.skipped_count == 1
    assert "DRAFT or STOPPED" in (
        result.results[0].message
    )
    context.paper_engine.execute.assert_not_called()
def test_unsafe_follower_is_skipped():
    subscription = build_subscription()
    context = build_service(
        template=build_template(),
        subscriptions=[subscription],
        bots=[
            build_bot(
                dry_run=False
            )
        ],
    )
    result = (
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
    )
    assert result.skipped_count == 1
    context.paper_engine.execute.assert_not_called()
def test_missing_follower_is_failed():
    subscription = build_subscription()
    context = build_service(
        template=build_template(),
        subscriptions=[subscription],
        bots=[],
    )
    result = (
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
    )
    assert result.failed_count == 1
    assert (
        subscription.last_error
        == "Follower trading bot was not found"
    )
def test_failure_does_not_stop_other_followers():
    first_subscription = (
        build_subscription(
            subscription_id=40,
            follower_user_id=7,
            follower_bot_id=30,
        )
    )
    second_subscription = (
        build_subscription(
            subscription_id=41,
            follower_user_id=8,
            follower_bot_id=31,
        )
    )
    first_bot = build_bot(
        bot_id=30,
        user_id=7,
    )
    second_bot = build_bot(
        bot_id=31,
        user_id=8,
    )
    context = build_service(
        template=build_template(),
        subscriptions=[
            first_subscription,
            second_subscription,
        ],
        bots=[
            first_bot,
            second_bot,
        ],
    )
    context.paper_engine.execute.side_effect = [
        RuntimeError(
            "Paper execution failed"
        ),
        {
            "outcome": "OPENED",
            "decision_action": "BUY",
        },
    ]
    result = (
        context.service.mirror_decision(
            source_template_id=20,
            decision=build_decision(),
        )
    )
    assert result.scanned_count == 2
    assert result.failed_count == 1
    assert result.executed_count == 1
    assert (
        first_subscription.last_error
        == "Paper execution failed"
    )
    assert (
        second_subscription
        .last_mirrored_at
        == NOW
    )
