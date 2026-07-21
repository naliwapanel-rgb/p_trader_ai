import pytest
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.orm import (
    sessionmaker,
)
from sqlalchemy.pool import (
    StaticPool,
)
from app.database.session import (
    Base,
)
from app.models import (
    ExchangeAccount,
    TradingBot,
    User,
)
from app.repositories.trading_bot_repository import (
    TradingBotRepository,
)
from app.schemas.trading_bot import (
    TradingBotCreateRequest,
    TradingBotUpdateRequest,
)
@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine
    )
    TestingSession = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(
            bind=engine
        )
        engine.dispose()
def _create_user_and_account(
    db,
    *,
    user_id: int,
    account_id: int,
):
    user = User(
        id=user_id,
        full_name=(
            f"Bot User {user_id}"
        ),
        email=(
            f"bot{user_id}@example.com"
        ),
        hashed_password="hashed",
        is_active=True,
    )
    account = ExchangeAccount(
        id=account_id,
        user_id=user_id,
        exchange_name="BYBIT",
        account_name=(
            f"Bot Account {account_id}"
        ),
        encrypted_api_key="encrypted-key",
        encrypted_api_secret=(
            "encrypted-secret"
        ),
        is_testnet=True,
        is_active=True,
    )
    db.add_all([
        user,
        account,
    ])
    db.commit()
    return user, account
def _create_data(
    *,
    name="BTC Momentum Bot",
    exchange_account_id=3,
    status_config=None,
):
    config = {
        "period": 14,
    }
    if status_config is not None:
        config.update(status_config)
    return TradingBotCreateRequest(
        exchange_account_id=(
            exchange_account_id
        ),
        name=name,
        description=(
            "Persistence foundation bot"
        ),
        strategy_type="MOMENTUM",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1,
        max_position_value_usd=25,
        max_daily_loss_percent=3,
        max_drawdown_percent=10,
        stop_loss_percent=2,
        take_profit_percent=4,
        strategy_config=config,
    )
def test_trading_bot_model_is_registered():
    assert (
        "trading_bots"
        in Base.metadata.tables
    )
def test_create_persists_configuration(
    db_session,
):
    _create_user_and_account(
        db_session,
        user_id=7,
        account_id=3,
    )
    repository = TradingBotRepository(
        db_session
    )
    bot = repository.create(
        user_id=7,
        data=_create_data(),
    )
    assert bot.id is not None
    assert bot.user_id == 7
    assert bot.exchange_account_id == 3
    assert bot.name == "BTC Momentum Bot"
    assert bot.symbol == "BTCUSDT"
    assert bot.status == "DRAFT"
    assert bot.paper_trading is True
    assert bot.dry_run is True
    assert bot.strategy_config == {
        "period": 14,
    }
    assert bot.created_at is not None
    assert bot.updated_at is not None
def test_repository_is_user_scoped(
    db_session,
):
    _create_user_and_account(
        db_session,
        user_id=7,
        account_id=3,
    )
    _create_user_and_account(
        db_session,
        user_id=8,
        account_id=4,
    )
    repository = TradingBotRepository(
        db_session
    )
    first = repository.create(
        user_id=7,
        data=_create_data(
            name="User Seven Bot",
            exchange_account_id=3,
        ),
    )
    second = repository.create(
        user_id=8,
        data=_create_data(
            name="User Eight Bot",
            exchange_account_id=4,
        ),
    )
    assert repository.list_by_user(
        user_id=7
    ) == [first]
    assert repository.list_by_user(
        user_id=8
    ) == [second]
    assert (
        repository.get_by_id_and_user(
            bot_id=first.id,
            user_id=8,
        )
        is None
    )
    assert (
        repository.get_by_id_and_user(
            bot_id=first.id,
            user_id=7,
        )
        is first
    )
def test_bot_name_is_unique_per_user(
    db_session,
):
    _create_user_and_account(
        db_session,
        user_id=7,
        account_id=3,
    )
    _create_user_and_account(
        db_session,
        user_id=8,
        account_id=4,
    )
    repository = TradingBotRepository(
        db_session
    )
    repository.create(
        user_id=7,
        data=_create_data(
            name="Shared Name",
            exchange_account_id=3,
        ),
    )
    with pytest.raises(
        IntegrityError
    ):
        repository.create(
            user_id=7,
            data=_create_data(
                name="Shared Name",
                exchange_account_id=3,
            ),
        )
    db_session.rollback()
    other_user_bot = repository.create(
        user_id=8,
        data=_create_data(
            name="Shared Name",
            exchange_account_id=4,
        ),
    )
    assert other_user_bot.user_id == 8
def test_update_enforces_effective_safety(
    db_session,
):
    _create_user_and_account(
        db_session,
        user_id=7,
        account_id=3,
    )
    repository = TradingBotRepository(
        db_session
    )
    bot = repository.create(
        user_id=7,
        data=_create_data(),
    )
    updated = repository.update(
        bot=bot,
        data=TradingBotUpdateRequest(
            name="Updated Momentum Bot",
            status="STOPPED",
            paper_trading=False,
            dry_run=True,
            strategy_config={
                "period": 21,
            },
        ),
    )
    assert updated.name == (
        "Updated Momentum Bot"
    )
    assert updated.status == "STOPPED"
    assert updated.paper_trading is False
    assert updated.dry_run is True
    assert updated.strategy_config == {
        "period": 21,
    }
    with pytest.raises(
        ValueError,
        match=(
            "paper_trading or "
            "dry_run"
        ),
    ):
        repository.update(
            bot=updated,
            data=(
                TradingBotUpdateRequest(
                    dry_run=False
                )
            ),
        )
def test_filter_and_delete(
    db_session,
):
    _create_user_and_account(
        db_session,
        user_id=7,
        account_id=3,
    )
    repository = TradingBotRepository(
        db_session
    )
    draft = repository.create(
        user_id=7,
        data=_create_data(
            name="Draft Bot",
        ),
    )
    stopped = repository.create(
        user_id=7,
        data=_create_data(
            name="Stopped Bot",
        ),
    )
    stopped = repository.update(
        bot=stopped,
        data=TradingBotUpdateRequest(
            status="STOPPED"
        ),
    )
    assert repository.list_by_user(
        user_id=7,
        status="DRAFT",
    ) == [draft]
    assert repository.list_by_user(
        user_id=7,
        status="STOPPED",
    ) == [stopped]
    repository.delete(draft)
    assert (
        repository.get_by_id_and_user(
            bot_id=draft.id,
            user_id=7,
        )
        is None
    )
