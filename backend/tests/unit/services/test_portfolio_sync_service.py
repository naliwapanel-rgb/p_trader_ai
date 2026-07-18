from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException
from app.models.portfolio_sync_snapshot import (
    PortfolioSyncSnapshot,
)
from app.services.portfolio_sync_service import (
    PortfolioSyncService,
)
def build_balance():
    return {
        "exchange": "BYBIT",
        "account_type": "UNIFIED",
        "total_equity_usd": 1250.0,
        "total_wallet_balance_usd": 1200.0,
        "total_available_balance_usd": 900.0,
        "total_unrealized_pnl_usd": 50.0,
        "coins": [
            {
                "coin": "USDT",
                "usd_value": 1000.0,
            },
            {
                "coin": "BTC",
                "usd_value": 250.0,
            },
        ],
    }
def build_positions():
    return {
        "exchange": "BYBIT",
        "category": "linear",
        "settle_coin": "USDT",
        "count": 2,
        "positions": [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "position_value": 500.0,
                "unrealized_pnl": 30.0,
                "realized_pnl": 5.0,
            },
            {
                "symbol": "ETHUSDT",
                "side": "SHORT",
                "position_value": 250.0,
                "unrealized_pnl": 20.0,
                "realized_pnl": 7.0,
            },
        ],
    }
def build_orders():
    return {
        "exchange": "BYBIT",
        "category": "linear",
        "settle_coin": "USDT",
        "count": 1,
        "orders": [
            {
                "order_id": "order-1",
                "symbol": "BTCUSDT",
                "side": "BUY",
            }
        ],
    }
def build_snapshot(data):
    snapshot = PortfolioSyncSnapshot(
        **data.model_dump()
    )
    snapshot.id = 10
    timestamp = datetime(
        2026,
        7,
        18,
        21,
        30,
        tzinfo=timezone.utc,
    )
    snapshot.synced_at = timestamp
    snapshot.created_at = timestamp
    return snapshot
def build_service(
    *,
    balance_result=None,
    positions_result=None,
    orders_result=None,
    account_active=True,
    created=True,
):
    client = SimpleNamespace(
        get_account_balance=AsyncMock(
            return_value=(
                build_balance()
                if balance_result is None
                else balance_result
            )
        ),
        get_positions=AsyncMock(
            return_value=(
                build_positions()
                if positions_result is None
                else positions_result
            )
        ),
        get_open_orders=AsyncMock(
            return_value=(
                build_orders()
                if orders_result is None
                else orders_result
            )
        ),
    )
    client_factory = MagicMock(
        return_value=client
    )
    service = PortfolioSyncService(
        db=MagicMock(),
        client_factory=client_factory,
    )
    portfolio = SimpleNamespace(
        id=2,
        user_id=1,
        total_value=100.0,
        profit_loss=10.0,
    )
    account = SimpleNamespace(
        id=3,
        user_id=1,
        exchange_name="BYBIT",
        is_active=account_active,
    )
    service.portfolio_service.get_portfolio = (
        MagicMock(
            return_value=portfolio
        )
    )
    service.exchange_account_service.get_account = (
        MagicMock(
            return_value=account
        )
    )
    def update_portfolio(
        *,
        portfolio,
        total_value,
        profit_loss,
        **kwargs,
    ):
        portfolio.total_value = total_value
        portfolio.profit_loss = profit_loss
        return portfolio
    service.portfolio_repository.update = (
        MagicMock(
            side_effect=update_portfolio
        )
    )
    def create_or_get(data):
        return build_snapshot(data), created
    service.sync_repository.create_or_get = (
        MagicMock(
            side_effect=create_or_get
        )
    )
    return (
        service,
        client,
        client_factory,
        portfolio,
        account,
    )
@pytest.mark.asyncio
async def test_successful_sync_calculates_totals():
    (
        service,
        client,
        client_factory,
        portfolio,
        account,
    ) = build_service()
    result = await service.synchronize(
        current_user=SimpleNamespace(id=1),
        portfolio_id=2,
        exchange_account_id=3,
        category="linear",
        settle_coin="usdt",
    )
    assert result.snapshot.status == "SUCCESS"
    assert result.created is True
    assert (
        result.snapshot.total_equity_usd
        == 1250.0
    )
    assert (
        result.snapshot
        .total_position_value_usd
        == 750.0
    )
    assert (
        result.snapshot
        .total_unrealized_pnl_usd
        == 50.0
    )
    assert (
        result.snapshot
        .total_realized_pnl_usd
        == 12.0
    )
    assert result.snapshot.coin_count == 2
    assert (
        result.snapshot
        .open_position_count
        == 2
    )
    assert (
        result.snapshot.open_order_count
        == 1
    )
    assert result.portfolio_total_value == 1250.0
    assert result.portfolio_profit_loss == 62.0
    assert result.source_errors == {}
    client_factory.assert_called_once_with(
        account
    )
    client.get_positions.assert_awaited_once_with(
        category="linear",
        settle_coin="USDT",
    )
    client.get_open_orders.assert_awaited_once_with(
        category="linear",
        settle_coin="USDT",
    )
    service.portfolio_repository.update.assert_called_once()
@pytest.mark.asyncio
async def test_duplicate_sync_returns_created_false():
    service, _, _, _, _ = build_service(
        created=False
    )
    result = await service.synchronize(
        current_user=SimpleNamespace(id=1),
        portfolio_id=2,
        exchange_account_id=3,
    )
    assert result.created is False
    assert result.snapshot.status == "SUCCESS"
@pytest.mark.asyncio
async def test_partial_sync_records_source_failure():
    service, _, _, _, _ = build_service()
    service.client_factory.return_value.get_positions = (
        AsyncMock(
            side_effect=RuntimeError(
                "Position service unavailable"
            )
        )
    )
    result = await service.synchronize(
        current_user=SimpleNamespace(id=1),
        portfolio_id=2,
        exchange_account_id=3,
    )
    assert result.snapshot.status == "PARTIAL"
    assert (
        result.snapshot.open_position_count
        == 0
    )
    assert (
        result.snapshot.open_order_count
        == 1
    )
    assert result.portfolio_total_value == 1250.0
    assert result.portfolio_profit_loss == 50.0
    assert (
        result.source_errors["positions"]
        == "Position service unavailable"
    )
    assert (
        "positions: Position service unavailable"
        in result.snapshot.error_message
    )
    service.portfolio_repository.update.assert_called_once()
@pytest.mark.asyncio
async def test_failed_sync_does_not_zero_portfolio():
    service, client, _, portfolio, _ = (
        build_service()
    )
    client.get_account_balance = AsyncMock(
        side_effect=RuntimeError(
            "Balance unavailable"
        )
    )
    client.get_positions = AsyncMock(
        side_effect=RuntimeError(
            "Positions unavailable"
        )
    )
    client.get_open_orders = AsyncMock(
        side_effect=RuntimeError(
            "Orders unavailable"
        )
    )
    result = await service.synchronize(
        current_user=SimpleNamespace(id=1),
        portfolio_id=2,
        exchange_account_id=3,
    )
    assert result.snapshot.status == "FAILED"
    assert len(result.source_errors) == 3
    assert result.portfolio_total_value == 100.0
    assert result.portfolio_profit_loss == 10.0
    assert portfolio.total_value == 100.0
    assert portfolio.profit_loss == 10.0
    service.portfolio_repository.update.assert_not_called()
@pytest.mark.asyncio
async def test_inactive_account_is_rejected():
    (
        service,
        client,
        client_factory,
        _,
        _,
    ) = build_service(
        account_active=False
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.synchronize(
            current_user=SimpleNamespace(id=1),
            portfolio_id=2,
            exchange_account_id=3,
        )
    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "Exchange account is inactive"
    )
    client_factory.assert_not_called()
    client.get_account_balance.assert_not_awaited()
def test_fingerprint_is_order_independent():
    first = {
        "balance": {
            "coins": [
                {"coin": "BTC"},
                {"coin": "USDT"},
            ],
            "value": 10,
        },
        "positions": [
            {"symbol": "ETHUSDT"},
            {"symbol": "BTCUSDT"},
        ],
    }
    second = {
        "positions": [
            {"symbol": "BTCUSDT"},
            {"symbol": "ETHUSDT"},
        ],
        "balance": {
            "value": 10,
            "coins": [
                {"coin": "USDT"},
                {"coin": "BTC"},
            ],
        },
    }
    first_fingerprint = (
        PortfolioSyncService.build_fingerprint(
            first
        )
    )
    second_fingerprint = (
        PortfolioSyncService.build_fingerprint(
            second
        )
    )
    assert (
        first_fingerprint
        == second_fingerprint
    )
    assert len(first_fingerprint) == 64
