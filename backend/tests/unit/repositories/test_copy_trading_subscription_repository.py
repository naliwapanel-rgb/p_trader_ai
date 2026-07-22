from __future__ import (
    annotations,
)
from collections.abc import (
    Generator,
)
import pytest
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import (
    StaticPool,
)
from app.database.session import (
    Base,
)
from app.models.copy_trading_subscription import (
    CopyTradingSubscription,
)
from app.models.strategy_template import (
    StrategyTemplate,
)
from app.models.trading_bot import (
    TradingBot,
)
from app.models.user import (
    User,
)
from app.repositories.copy_trading_subscription_repository import (
    CopyTradingSubscriptionRepository,
)
@pytest.fixture
def db() -> Generator[
    Session,
    None,
    None,
]:
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    tables = [
        User.__table__,
        StrategyTemplate.__table__,
        TradingBot.__table__,
        CopyTradingSubscription.__table__,
    ]
    Base.metadata.create_all(
        bind=engine,
        tables=tables,
    )
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
            tables=list(
                reversed(tables)
            ),
        )
        engine.dispose()
def create_user(
    db: Session,
    *,
    email: str,
) -> User:
    user = User(
        full_name="Follower User",
        email=email,
        hashed_password="hashed-password",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
def create_template(
    db: Session,
    *,
    user_id: int,
) -> StrategyTemplate:
    template = StrategyTemplate(
        user_id=user_id,
        name="Published Template",
        description=None,
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        visibility="PUBLIC",
        status="PUBLISHED",
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1.0,
        max_position_value_usd=25.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        stop_loss_percent=None,
        take_profit_percent=None,
        strategy_config={},
        version=2,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template
def create_bot(
    db: Session,
    *,
    user_id: int,
    name: str,
) -> TradingBot:
    bot = TradingBot(
        user_id=user_id,
        exchange_account_id=None,
        name=name,
        description=None,
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        status="DRAFT",
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1.0,
        max_position_value_usd=25.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        stop_loss_percent=None,
        take_profit_percent=None,
        strategy_config={},
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot
def test_create_and_get_subscription(
    db: Session,
):
    publisher = create_user(
        db,
        email="publisher@example.com",
    )
    follower = create_user(
        db,
        email="follower@example.com",
    )
    template = create_template(
        db,
        user_id=publisher.id,
    )
    bot = create_bot(
        db,
        user_id=follower.id,
        name="Follower Bot",
    )
    repository = (
        CopyTradingSubscriptionRepository(
            db
        )
    )
    subscription = repository.create(
        follower_user_id=follower.id,
        source_template_id=template.id,
        follower_bot_id=bot.id,
        subscribed_template_version=2,
    )
    loaded = (
        repository.get_by_id_and_user(
            subscription_id=(
                subscription.id
            ),
            follower_user_id=(
                follower.id
            ),
        )
    )
    assert loaded is subscription
    assert loaded.status == "ACTIVE"
    assert (
        loaded.execution_mode
        == "PAPER_ONLY"
    )
    assert (
        loaded
        .subscribed_template_version
        == 2
    )
def test_subscription_is_owner_scoped(
    db: Session,
):
    publisher = create_user(
        db,
        email="publisher@example.com",
    )
    follower = create_user(
        db,
        email="follower@example.com",
    )
    other_user = create_user(
        db,
        email="other@example.com",
    )
    template = create_template(
        db,
        user_id=publisher.id,
    )
    bot = create_bot(
        db,
        user_id=follower.id,
        name="Follower Bot",
    )
    repository = (
        CopyTradingSubscriptionRepository(
            db
        )
    )
    subscription = repository.create(
        follower_user_id=follower.id,
        source_template_id=template.id,
        follower_bot_id=bot.id,
        subscribed_template_version=2,
    )
    assert (
        repository.get_by_id_and_user(
            subscription_id=(
                subscription.id
            ),
            follower_user_id=(
                other_user.id
            ),
        )
        is None
    )
def test_follower_bot_is_unique(
    db: Session,
):
    publisher = create_user(
        db,
        email="publisher@example.com",
    )
    follower = create_user(
        db,
        email="follower@example.com",
    )
    template = create_template(
        db,
        user_id=publisher.id,
    )
    bot = create_bot(
        db,
        user_id=follower.id,
        name="Follower Bot",
    )
    repository = (
        CopyTradingSubscriptionRepository(
            db
        )
    )
    repository.create(
        follower_user_id=follower.id,
        source_template_id=template.id,
        follower_bot_id=bot.id,
        subscribed_template_version=2,
    )
    with pytest.raises(
        IntegrityError,
    ):
        repository.create(
            follower_user_id=follower.id,
            source_template_id=template.id,
            follower_bot_id=bot.id,
            subscribed_template_version=2,
        )
    db.rollback()
def test_list_and_active_template_filter(
    db: Session,
):
    publisher = create_user(
        db,
        email="publisher@example.com",
    )
    follower = create_user(
        db,
        email="follower@example.com",
    )
    template = create_template(
        db,
        user_id=publisher.id,
    )
    first_bot = create_bot(
        db,
        user_id=follower.id,
        name="First Bot",
    )
    second_bot = create_bot(
        db,
        user_id=follower.id,
        name="Second Bot",
    )
    repository = (
        CopyTradingSubscriptionRepository(
            db
        )
    )
    first = repository.create(
        follower_user_id=follower.id,
        source_template_id=template.id,
        follower_bot_id=first_bot.id,
        subscribed_template_version=2,
    )
    second = repository.create(
        follower_user_id=follower.id,
        source_template_id=template.id,
        follower_bot_id=second_bot.id,
        subscribed_template_version=2,
    )
    repository.update_state(
        subscription=second,
        fields={
            "status": "PAUSED",
        },
    )
    active = (
        repository.list_active_by_template(
            source_template_id=(
                template.id
            ),
        )
    )
    assert [
        item.id
        for item in active
    ] == [first.id]
    paused = repository.list_by_user(
        follower_user_id=follower.id,
        status="PAUSED",
    )
    assert [
        item.id
        for item in paused
    ] == [second.id]
def test_update_state_rejects_protected_fields(
    db: Session,
):
    publisher = create_user(
        db,
        email="publisher@example.com",
    )
    follower = create_user(
        db,
        email="follower@example.com",
    )
    template = create_template(
        db,
        user_id=publisher.id,
    )
    bot = create_bot(
        db,
        user_id=follower.id,
        name="Follower Bot",
    )
    repository = (
        CopyTradingSubscriptionRepository(
            db
        )
    )
    subscription = repository.create(
        follower_user_id=follower.id,
        source_template_id=template.id,
        follower_bot_id=bot.id,
        subscribed_template_version=2,
    )
    with pytest.raises(
        ValueError,
        match="Protected",
    ):
        repository.update_state(
            subscription=subscription,
            fields={
                "follower_bot_id": (
                    bot.id + 1
                ),
            },
        )
def test_paper_only_constraint(
    db: Session,
):
    publisher = create_user(
        db,
        email="publisher@example.com",
    )
    follower = create_user(
        db,
        email="follower@example.com",
    )
    template = create_template(
        db,
        user_id=publisher.id,
    )
    bot = create_bot(
        db,
        user_id=follower.id,
        name="Follower Bot",
    )
    subscription = (
        CopyTradingSubscription(
            follower_user_id=(
                follower.id
            ),
            source_template_id=(
                template.id
            ),
            follower_bot_id=bot.id,
            status="ACTIVE",
            execution_mode="LIVE",
            subscribed_template_version=2,
        )
    )
    db.add(subscription)
    with pytest.raises(
        IntegrityError,
    ):
        db.commit()
    db.rollback()
def test_delete_subscription(
    db: Session,
):
    publisher = create_user(
        db,
        email="publisher@example.com",
    )
    follower = create_user(
        db,
        email="follower@example.com",
    )
    template = create_template(
        db,
        user_id=publisher.id,
    )
    bot = create_bot(
        db,
        user_id=follower.id,
        name="Follower Bot",
    )
    repository = (
        CopyTradingSubscriptionRepository(
            db
        )
    )
    subscription = repository.create(
        follower_user_id=follower.id,
        source_template_id=template.id,
        follower_bot_id=bot.id,
        subscribed_template_version=2,
    )
    subscription_id = subscription.id
    repository.delete(subscription)
    assert (
        repository.get_by_id_and_user(
            subscription_id=(
                subscription_id
            ),
            follower_user_id=(
                follower.id
            ),
        )
        is None
    )
