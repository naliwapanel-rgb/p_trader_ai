from datetime import (
    UTC,
    datetime,
)
import pytest
from sqlalchemy import (
    create_engine,
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
    PaperTradingAccount,
    PaperTradingOrder,
    PaperTradingPosition,
    TradingBot,
    User,
)
from app.repositories.paper_trading_repository import (
    PaperTradingRepository,
)
from app.schemas.paper_trading import (
    PaperTradingAccountCreate,
    PaperTradingOrderCreate,
    PaperTradingPositionCreate,
)
NOW = datetime(
    2026,
    7,
    21,
    16,
    0,
    tzinfo=UTC,
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
def create_user_and_bot(
    db,
):
    user = User(
        id=7,
        full_name="Paper User",
        email="paper@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    bot = TradingBot(
        id=10,
        user_id=7,
        exchange_account_id=None,
        name="Paper BTC Bot",
        description=(
            "Paper trading repository test"
        ),
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        status="RUNNING",
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1.0,
        max_position_value_usd=25.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        stop_loss_percent=2.0,
        take_profit_percent=4.0,
        strategy_config={},
    )
    db.add_all([
        user,
        bot,
    ])
    db.commit()
    return user, bot
def account_data():
    return PaperTradingAccountCreate(
        user_id=7,
        trading_bot_id=10,
        currency="usdt",
        initial_balance_usd=10000,
    )
def position_data(
    *,
    account_id: int,
):
    return PaperTradingPositionCreate(
        user_id=7,
        trading_bot_id=10,
        paper_account_id=account_id,
        symbol="btcusdt",
        category="linear",
        side="LONG",
        quantity=0.0004,
        average_entry_price=60000,
        current_price=60000,
        position_value_usd=24,
        reserved_margin_usd=24,
        unrealized_pnl_usd=0,
        realized_pnl_usd=0,
        total_fees_usd=0.0144,
        opened_at=NOW,
    )
def test_paper_models_are_registered():
    assert (
        "paper_trading_accounts"
        in Base.metadata.tables
    )
    assert (
        "paper_trading_positions"
        in Base.metadata.tables
    )
    assert (
        "paper_trading_orders"
        in Base.metadata.tables
    )
def test_account_get_or_create(
    db_session,
):
    create_user_and_bot(
        db_session
    )
    repository = PaperTradingRepository(
        db_session
    )
    first, first_created = (
        repository.get_or_create_account(
            account_data()
        )
    )
    second, second_created = (
        repository.get_or_create_account(
            account_data()
        )
    )
    assert first_created is True
    assert second_created is False
    assert first.id == second.id
    assert first.currency == "USDT"
    assert first.cash_balance_usd == 10000
    assert first.equity_usd == 10000
    assert (
        db_session
        .query(PaperTradingAccount)
        .count()
        == 1
    )
def test_account_is_user_scoped(
    db_session,
):
    create_user_and_bot(
        db_session
    )
    repository = PaperTradingRepository(
        db_session
    )
    account, _ = (
        repository.get_or_create_account(
            account_data()
        )
    )
    assert (
        repository.get_account_by_bot(
            user_id=7,
            trading_bot_id=10,
        ).id
        == account.id
    )
    assert (
        repository.get_account_by_bot(
            user_id=8,
            trading_bot_id=10,
        )
        is None
    )
def test_position_persistence(
    db_session,
):
    create_user_and_bot(
        db_session
    )
    repository = PaperTradingRepository(
        db_session
    )
    account, _ = (
        repository.get_or_create_account(
            account_data()
        )
    )
    position = repository.create_position(
        position_data(
            account_id=account.id
        )
    )
    loaded = repository.get_open_position(
        paper_account_id=account.id,
        symbol="btcusdt",
    )
    assert loaded is not None
    assert loaded.id == position.id
    assert loaded.symbol == "BTCUSDT"
    assert loaded.side == "LONG"
    assert loaded.status == "OPEN"
    repository.save_position(
        position=position,
        current_price=61000,
        position_value_usd=24.4,
        unrealized_pnl_usd=0.4,
    )
    assert position.current_price == 61000
    assert position.unrealized_pnl_usd == 0.4
def test_order_and_account_updates(
    db_session,
):
    create_user_and_bot(
        db_session
    )
    repository = PaperTradingRepository(
        db_session
    )
    account, _ = (
        repository.get_or_create_account(
            account_data()
        )
    )
    position = repository.create_position(
        position_data(
            account_id=account.id
        )
    )
    order = repository.create_order(
        PaperTradingOrderCreate(
            user_id=7,
            trading_bot_id=10,
            paper_account_id=account.id,
            paper_position_id=position.id,
            symbol="BTCUSDT",
            category="linear",
            side="BUY",
            position_effect="OPEN",
            quantity=0.0004,
            reference_price=60000,
            fill_price=60006,
            gross_value_usd=24.0024,
            fee_rate=0.0006,
            fee_usd=0.01440144,
            slippage_rate=0.0001,
            slippage_usd=0.0024,
            realized_pnl_usd=0,
            decision_reason=(
                "Buy threshold reached"
            ),
            filled_at=NOW,
        )
    )
    repository.save_account(
        account=account,
        cash_balance_usd=(
            9975.98319856
        ),
        reserved_balance_usd=24.0024,
        equity_usd=9999.98559856,
        total_fees_usd=0.01440144,
    )
    orders = repository.list_orders(
        paper_account_id=account.id
    )
    positions = repository.list_positions(
        paper_account_id=account.id,
        status="OPEN",
    )
    assert order.status == "FILLED"
    assert len(orders) == 1
    assert orders[0].id == order.id
    assert len(positions) == 1
    assert account.reserved_balance_usd == 24.0024
    assert account.total_fees_usd == 0.01440144
def test_closed_position_is_not_open(
    db_session,
):
    create_user_and_bot(
        db_session
    )
    repository = PaperTradingRepository(
        db_session
    )
    account, _ = (
        repository.get_or_create_account(
            account_data()
        )
    )
    position = repository.create_position(
        position_data(
            account_id=account.id
        )
    )
    repository.save_position(
        position=position,
        status="CLOSED",
        closed_at=NOW,
        unrealized_pnl_usd=0.0,
    )
    assert (
        repository.get_open_position(
            paper_account_id=account.id,
            symbol="BTCUSDT",
        )
        is None
    )
    closed = repository.list_positions(
        paper_account_id=account.id,
        status="CLOSED",
    )
    assert len(closed) == 1
    assert closed[0].id == position.id
