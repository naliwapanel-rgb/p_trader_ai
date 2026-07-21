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
    PaperTradingEngineSettings,
)
from app.schemas.trading_bot_strategy import (
    TradingBotStrategyDecision,
)
from app.services.paper_trading_engine import (
    PaperTradingEngine,
)
NOW = datetime(
    2026,
    7,
    21,
    17,
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
    *,
    paper_trading: bool = True,
    risk_percent: float = 1.0,
    max_position: float = 25.0,
):
    user = User(
        id=7,
        full_name="Paper Engine User",
        email="engine@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    bot = TradingBot(
        id=10,
        user_id=7,
        exchange_account_id=None,
        name="Paper Engine Bot",
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        status="RUNNING",
        paper_trading=paper_trading,
        dry_run=True,
        risk_per_trade_percent=(
            risk_percent
        ),
        max_position_value_usd=(
            max_position
        ),
        max_daily_loss_percent=max(
            risk_percent,
            3.0,
        ),
        max_drawdown_percent=max(
            risk_percent,
            10.0,
        ),
        strategy_config={},
    )
    db.add_all([
        user,
        bot,
    ])
    db.commit()
    db.refresh(bot)
    return bot
def decision(
    action: str,
    *,
    price: float,
):
    return TradingBotStrategyDecision(
        action=action,
        confidence=0.8,
        reason=(
            f"Test {action} decision"
        ),
        reference_price=price,
        evaluated_at=NOW,
    )
def build_engine(
    db,
    *,
    settings=None,
    repository=None,
):
    return PaperTradingEngine(
        db,
        settings=settings,
        repository=repository,
        clock=lambda: NOW,
    )
def test_hold_creates_account_without_order(
    db_session,
):
    bot = create_user_and_bot(
        db_session
    )
    result = build_engine(
        db_session
    ).execute(
        bot=bot,
        decision=decision(
            "HOLD",
            price=100,
        ),
    )
    assert result.outcome == "NO_ACTION"
    assert result.account_created is True
    assert result.position is None
    assert result.order is None
    assert (
        db_session
        .query(PaperTradingAccount)
        .count()
        == 1
    )
    assert (
        db_session
        .query(PaperTradingOrder)
        .count()
        == 0
    )
def test_buy_opens_long_position(
    db_session,
):
    bot = create_user_and_bot(
        db_session
    )
    result = build_engine(
        db_session
    ).execute(
        bot=bot,
        decision=decision(
            "BUY",
            price=100,
        ),
    )
    assert result.outcome == "OPENED"
    assert result.position.side == "LONG"
    assert result.position.status == "OPEN"
    assert result.order.side == "BUY"
    assert (
        result.order.position_effect
        == "OPEN"
    )
    assert result.order.fill_price > 100
    assert result.order.fee_usd > 0
    assert result.order.slippage_usd > 0
    assert (
        result.account.cash_balance_usd
        < 10000
    )
    assert (
        result.account
        .reserved_balance_usd
        > 0
    )
def test_same_direction_signal_increases_position(
    db_session,
):
    bot = create_user_and_bot(
        db_session,
        risk_percent=0.25,
        max_position=60,
    )
    engine = build_engine(
        db_session
    )
    first = engine.execute(
        bot=bot,
        decision=decision(
            "BUY",
            price=100,
        ),
    )
    second = engine.execute(
        bot=bot,
        decision=decision(
            "BUY",
            price=105,
        ),
    )
    assert first.outcome == "OPENED"
    assert second.outcome == "INCREASED"
    assert (
        second.position.quantity
        > first.position.quantity
    )
    assert (
        second.position
        .average_entry_price
        > first.position
        .average_entry_price
    )
    assert (
        db_session
        .query(PaperTradingOrder)
        .count()
        == 2
    )
def test_sell_closes_long_with_realized_profit(
    db_session,
):
    bot = create_user_and_bot(
        db_session
    )
    engine = build_engine(
        db_session
    )
    opened = engine.execute(
        bot=bot,
        decision=decision(
            "BUY",
            price=100,
        ),
    )
    closed = engine.execute(
        bot=bot,
        decision=decision(
            "SELL",
            price=110,
        ),
    )
    assert opened.outcome == "OPENED"
    assert closed.outcome == "CLOSED"
    assert (
        closed.position.status
        == "CLOSED"
    )
    assert (
        closed.order.position_effect
        == "CLOSE"
    )
    assert (
        closed.order.realized_pnl_usd
        > 0
    )
    assert (
        closed.account.realized_pnl_usd
        > 0
    )
    assert (
        closed.account
        .reserved_balance_usd
        == pytest.approx(0)
    )
def test_sell_opens_short_and_buy_closes(
    db_session,
):
    bot = create_user_and_bot(
        db_session
    )
    engine = build_engine(
        db_session
    )
    opened = engine.execute(
        bot=bot,
        decision=decision(
            "SELL",
            price=100,
        ),
    )
    closed = engine.execute(
        bot=bot,
        decision=decision(
            "BUY",
            price=90,
        ),
    )
    assert opened.position.side == "SHORT"
    assert opened.order.side == "SELL"
    assert closed.outcome == "CLOSED"
    assert closed.order.side == "BUY"
    assert (
        closed.order.realized_pnl_usd
        > 0
    )
def test_hold_marks_open_position_to_market(
    db_session,
):
    bot = create_user_and_bot(
        db_session
    )
    engine = build_engine(
        db_session
    )
    engine.execute(
        bot=bot,
        decision=decision(
            "BUY",
            price=100,
        ),
    )
    result = engine.execute(
        bot=bot,
        decision=decision(
            "HOLD",
            price=110,
        ),
    )
    assert result.outcome == "NO_ACTION"
    assert (
        result.position
        .unrealized_pnl_usd
        > 0
    )
    assert (
        result.account
        .unrealized_pnl_usd
        > 0
    )
    assert (
        db_session
        .query(PaperTradingOrder)
        .count()
        == 1
    )
def test_minimum_notional_rejects_trade(
    db_session,
):
    bot = create_user_and_bot(
        db_session,
        risk_percent=1,
        max_position=25,
    )
    settings = (
        PaperTradingEngineSettings(
            initial_balance_usd=10,
            minimum_order_notional_usd=20,
        )
    )
    result = build_engine(
        db_session,
        settings=settings,
    ).execute(
        bot=bot,
        decision=decision(
            "BUY",
            price=100,
        ),
    )
    assert result.outcome == "REJECTED"
    assert result.position is None
    assert result.order is None
    assert (
        db_session
        .query(PaperTradingPosition)
        .count()
        == 0
    )
def test_transaction_rolls_back_on_order_failure(
    db_session,
    monkeypatch,
):
    bot = create_user_and_bot(
        db_session
    )
    repository = (
        PaperTradingRepository(
            db_session
        )
    )
    def fail_order(
        *args,
        **kwargs,
    ):
        raise RuntimeError(
            "simulated order failure"
        )
    monkeypatch.setattr(
        repository,
        "create_order",
        fail_order,
    )
    engine = build_engine(
        db_session,
        repository=repository,
    )
    with pytest.raises(
        RuntimeError,
        match="simulated order failure",
    ):
        engine.execute(
            bot=bot,
            decision=decision(
                "BUY",
                price=100,
            ),
        )
    assert (
        db_session
        .query(PaperTradingAccount)
        .count()
        == 0
    )
    assert (
        db_session
        .query(PaperTradingPosition)
        .count()
        == 0
    )
    assert (
        db_session
        .query(PaperTradingOrder)
        .count()
        == 0
    )
