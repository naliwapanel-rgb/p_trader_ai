from types import (
    SimpleNamespace,
)
from unittest.mock import (
    MagicMock,
)
import pytest
from fastapi import (
    HTTPException,
)
from app.schemas.copy_trading_subscription import (
    CopyTradingSubscriptionCreateRequest,
)
from app.services.copy_trading_subscription_service import (
    CopyTradingSubscriptionService,
)
def build_user():
    return SimpleNamespace(
        id=7,
    )
def build_template():
    return SimpleNamespace(
        id=20,
        user_id=4,
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        strategy_config={
            "buy_change_percent_24h": 1.0,
        },
        status="PUBLISHED",
        visibility="PUBLIC",
        version=3,
    )
def build_bot(
    *,
    status="DRAFT",
    paper_trading=True,
    dry_run=True,
):
    return SimpleNamespace(
        id=30,
        user_id=7,
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
def build_subscription(
    *,
    status="ACTIVE",
):
    return SimpleNamespace(
        id=40,
        follower_user_id=7,
        source_template_id=20,
        follower_bot_id=30,
        status=status,
        execution_mode="PAPER_ONLY",
        subscribed_template_version=3,
        last_error=None,
        last_mirrored_at=None,
    )
def build_service(
    *,
    template=None,
    bot=None,
    subscription=None,
):
    db = MagicMock()
    service = (
        CopyTradingSubscriptionService(
            db
        )
    )
    repository = MagicMock()
    template_repository = MagicMock()
    bot_repository = MagicMock()
    service.repository = repository
    service.template_repository = (
        template_repository
    )
    service.bot_repository = (
        bot_repository
    )
    template_repository.get_published_by_id.return_value = (
        template
    )
    bot_repository.get_by_id_and_user.return_value = (
        bot
    )
    repository.get_by_id_and_user.return_value = (
        subscription
    )
    repository.get_by_follower_bot_and_user.return_value = (
        None
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
    repository.update_state.side_effect = (
        update_state
    )
    return SimpleNamespace(
        service=service,
        repository=repository,
        template_repository=(
            template_repository
        ),
        bot_repository=bot_repository,
        db=db,
    )
def request():
    return (
        CopyTradingSubscriptionCreateRequest(
            source_template_id=20,
            follower_bot_id=30,
        )
    )
def test_list_is_follower_scoped():
    context = build_service()
    context.repository.list_by_user.return_value = [
        build_subscription()
    ]
    result = (
        context.service.list_subscriptions(
            current_user=build_user(),
            subscription_status="ACTIVE",
            limit=20,
            offset=5,
        )
    )
    assert len(result) == 1
    context.repository.list_by_user.assert_called_once_with(
        follower_user_id=7,
        status="ACTIVE",
        limit=20,
        offset=5,
    )
def test_missing_subscription_is_hidden():
    context = build_service(
        subscription=None
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.get_subscription(
            current_user=build_user(),
            subscription_id=40,
        )
    assert error.value.status_code == 404
def test_source_template_must_be_public():
    context = build_service(
        template=None,
        bot=build_bot(),
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.create_subscription(
            current_user=build_user(),
            data=request(),
        )
    assert error.value.status_code == 404
def test_follower_bot_must_be_owned():
    context = build_service(
        template=build_template(),
        bot=None,
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.create_subscription(
            current_user=build_user(),
            data=request(),
        )
    assert error.value.status_code == 404
def test_active_follower_bot_is_rejected():
    context = build_service(
        template=build_template(),
        bot=build_bot(
            status="RUNNING"
        ),
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.create_subscription(
            current_user=build_user(),
            data=request(),
        )
    assert error.value.status_code == 409
def test_follower_bot_must_be_fully_safe():
    context = build_service(
        template=build_template(),
        bot=build_bot(
            paper_trading=True,
            dry_run=False,
        ),
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.create_subscription(
            current_user=build_user(),
            data=request(),
        )
    assert error.value.status_code == 409
def test_follower_bot_must_match_template():
    template = build_template()
    bot = build_bot()
    bot.symbol = "ETHUSDT"
    context = build_service(
        template=template,
        bot=bot,
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.create_subscription(
            current_user=build_user(),
            data=request(),
        )
    assert error.value.status_code == 409
    assert "symbol" in error.value.detail
def test_create_subscription():
    template = build_template()
    bot = build_bot()
    context = build_service(
        template=template,
        bot=bot,
    )
    created = build_subscription()
    context.repository.create.return_value = (
        created
    )
    result = (
        context.service.create_subscription(
            current_user=build_user(),
            data=request(),
        )
    )
    assert result is created
    context.repository.create.assert_called_once_with(
        follower_user_id=7,
        source_template_id=20,
        follower_bot_id=30,
        subscribed_template_version=3,
    )
def test_duplicate_follower_subscription_is_rejected():
    context = build_service(
        template=build_template(),
        bot=build_bot(),
    )
    context.repository.get_by_follower_bot_and_user.return_value = (
        build_subscription()
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.create_subscription(
            current_user=build_user(),
            data=request(),
        )
    assert error.value.status_code == 409
    context.repository.create.assert_not_called()
def test_pause_and_resume_subscription():
    subscription = (
        build_subscription(
            status="ACTIVE"
        )
    )
    context = build_service(
        subscription=subscription
    )
    paused = (
        context.service.pause_subscription(
            current_user=build_user(),
            subscription_id=40,
        )
    )
    assert paused.status == "PAUSED"
    resumed = (
        context.service.resume_subscription(
            current_user=build_user(),
            subscription_id=40,
        )
    )
    assert resumed.status == "ACTIVE"
def test_stop_is_idempotent():
    subscription = (
        build_subscription(
            status="STOPPED"
        )
    )
    context = build_service(
        subscription=subscription
    )
    result = (
        context.service.stop_subscription(
            current_user=build_user(),
            subscription_id=40,
        )
    )
    assert result is subscription
    context.repository.update_state.assert_not_called()
def test_delete_requires_stopped_subscription():
    subscription = build_subscription(
        status="ACTIVE"
    )
    context = build_service(
        subscription=subscription
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        context.service.delete_subscription(
            current_user=build_user(),
            subscription_id=40,
        )
    assert error.value.status_code == 409
    context.repository.delete.assert_not_called()
def test_stopped_subscription_can_be_deleted():
    subscription = build_subscription(
        status="STOPPED"
    )
    context = build_service(
        subscription=subscription
    )
    context.service.delete_subscription(
        current_user=build_user(),
        subscription_id=40,
    )
    context.repository.delete.assert_called_once_with(
        subscription
    )
