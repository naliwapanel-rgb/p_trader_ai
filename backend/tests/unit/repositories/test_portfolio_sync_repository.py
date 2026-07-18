import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.models import PortfolioSyncSnapshot
from app.repositories.portfolio_sync_repository import (
    PortfolioSyncRepository,
)
from app.schemas.portfolio_sync import (
    PortfolioSyncSnapshotCreate,
)
@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    db = test_session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
def build_snapshot_data(
    *,
    fingerprint: str = "a" * 64,
    exchange_account_id: int = 3,
) -> PortfolioSyncSnapshotCreate:
    return PortfolioSyncSnapshotCreate(
        user_id=1,
        portfolio_id=2,
        exchange_account_id=(
            exchange_account_id
        ),
        exchange_name="BYBIT",
        account_type="UNIFIED",
        category="linear",
        settle_coin="USDT",
        status="SUCCESS",
        fingerprint=fingerprint,
        total_equity_usd=1250.50,
        total_wallet_balance_usd=1200.00,
        total_available_balance_usd=900.00,
        total_unrealized_pnl_usd=50.50,
        total_realized_pnl_usd=25.00,
        total_position_value_usd=500.00,
        coin_count=2,
        open_position_count=1,
        open_order_count=2,
        balance_payload={
            "exchange": "BYBIT",
            "total_equity_usd": 1250.50,
        },
        positions_payload=[
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
            }
        ],
        orders_payload=[
            {
                "order_id": "order-1",
                "symbol": "BTCUSDT",
            },
            {
                "order_id": "order-2",
                "symbol": "ETHUSDT",
            },
        ],
    )
def test_snapshot_model_is_registered():
    assert (
        "portfolio_sync_snapshots"
        in Base.metadata.tables
    )
def test_create_snapshot_persists_payloads(
    db_session,
):
    repository = PortfolioSyncRepository(
        db_session
    )
    snapshot, created = repository.create_or_get(
        build_snapshot_data()
    )
    assert created is True
    assert snapshot.id is not None
    assert snapshot.exchange_name == "BYBIT"
    assert snapshot.total_equity_usd == 1250.50
    assert snapshot.open_position_count == 1
    assert snapshot.open_order_count == 2
    assert snapshot.balance_payload[
        "exchange"
    ] == "BYBIT"
    assert (
        snapshot.positions_payload[0]["symbol"]
        == "BTCUSDT"
    )
def test_duplicate_snapshot_returns_existing_record(
    db_session,
):
    repository = PortfolioSyncRepository(
        db_session
    )
    first, first_created = (
        repository.create_or_get(
            build_snapshot_data()
        )
    )
    second, second_created = (
        repository.create_or_get(
            build_snapshot_data()
        )
    )
    count = (
        db_session.query(
            PortfolioSyncSnapshot
        ).count()
    )
    assert first_created is True
    assert second_created is False
    assert second.id == first.id
    assert count == 1
def test_same_fingerprint_allowed_for_other_account(
    db_session,
):
    repository = PortfolioSyncRepository(
        db_session
    )
    first, first_created = (
        repository.create_or_get(
            build_snapshot_data(
                exchange_account_id=3
            )
        )
    )
    second, second_created = (
        repository.create_or_get(
            build_snapshot_data(
                exchange_account_id=4
            )
        )
    )
    assert first_created is True
    assert second_created is True
    assert first.id != second.id
def test_latest_and_list_are_newest_first(
    db_session,
):
    repository = PortfolioSyncRepository(
        db_session
    )
    first, _ = repository.create_or_get(
        build_snapshot_data(
            fingerprint="a" * 64
        )
    )
    second, _ = repository.create_or_get(
        build_snapshot_data(
            fingerprint="b" * 64
        )
    )
    latest = repository.get_latest(
        user_id=1,
        portfolio_id=2,
    )
    snapshots = repository.list_by_portfolio(
        user_id=1,
        portfolio_id=2,
    )
    assert latest.id == second.id
    assert snapshots[0].id == second.id
    assert snapshots[1].id == first.id
