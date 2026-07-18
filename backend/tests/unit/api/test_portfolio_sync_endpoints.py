from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)
import pytest
from fastapi import HTTPException
from app.api.v1.endpoints.portfolios import (
    get_latest_portfolio_sync,
    get_portfolio_sync_snapshot,
    list_portfolio_sync_history,
    synchronize_my_portfolio,
)
from app.main import app
from app.schemas.portfolio_sync import (
    PortfolioSyncExecutionResult,
    PortfolioSyncRequest,
    PortfolioSyncSnapshotResponse,
)
from app.services.portfolio_sync_service import (
    PortfolioSyncService,
)
def build_snapshot(
    *,
    snapshot_id: int = 10,
    portfolio_id: int = 2,
):
    timestamp = datetime(
        2026,
        7,
        18,
        21,
        30,
        tzinfo=timezone.utc,
    )
    return SimpleNamespace(
        id=snapshot_id,
        user_id=1,
        portfolio_id=portfolio_id,
        exchange_account_id=3,
        exchange_name="BYBIT",
        account_type="UNIFIED",
        category="linear",
        settle_coin="USDT",
        status="SUCCESS",
        fingerprint="a" * 64,
        sync_version=1,
        total_equity_usd=1250.0,
        total_wallet_balance_usd=1200.0,
        total_available_balance_usd=900.0,
        total_unrealized_pnl_usd=50.0,
        total_realized_pnl_usd=12.0,
        total_position_value_usd=750.0,
        coin_count=2,
        open_position_count=2,
        open_order_count=1,
        balance_payload={
            "exchange": "BYBIT",
        },
        positions_payload=[
            {
                "symbol": "BTCUSDT",
            }
        ],
        orders_payload=[
            {
                "order_id": "order-1",
            }
        ],
        error_message=None,
        synced_at=timestamp,
        created_at=timestamp,
    )
def build_execution_result():
    snapshot = (
        PortfolioSyncSnapshotResponse
        .model_validate(build_snapshot())
    )
    return PortfolioSyncExecutionResult(
        snapshot=snapshot,
        created=True,
        portfolio_total_value=1250.0,
        portfolio_profit_loss=62.0,
        source_errors={},
    )
def test_portfolio_sync_routes_are_registered():
    paths = app.openapi()["paths"]
    assert (
        "/api/v1/portfolios/"
        "{portfolio_id}/sync"
        in paths
    )
    assert (
        "/api/v1/portfolios/"
        "{portfolio_id}/sync/latest"
        in paths
    )
    assert (
        "/api/v1/portfolios/"
        "{portfolio_id}/sync/history"
        in paths
    )
    assert (
        "/api/v1/portfolios/"
        "{portfolio_id}/sync/{snapshot_id}"
        in paths
    )
    assert (
        "post"
        in paths[
            "/api/v1/portfolios/"
            "{portfolio_id}/sync"
        ]
    )
    assert (
        "get"
        in paths[
            "/api/v1/portfolios/"
            "{portfolio_id}/sync/latest"
        ]
    )
def test_portfolio_sync_routes_require_authentication():
    paths = app.openapi()["paths"]
    operations = [
        paths[
            "/api/v1/portfolios/"
            "{portfolio_id}/sync"
        ]["post"],
        paths[
            "/api/v1/portfolios/"
            "{portfolio_id}/sync/latest"
        ]["get"],
        paths[
            "/api/v1/portfolios/"
            "{portfolio_id}/sync/history"
        ]["get"],
        paths[
            "/api/v1/portfolios/"
            "{portfolio_id}/sync/{snapshot_id}"
        ]["get"],
    ]
    for operation in operations:
        assert operation.get("security")
@pytest.mark.asyncio
async def test_sync_endpoint_delegates_to_service():
    current_user = SimpleNamespace(id=1)
    db = MagicMock()
    request = PortfolioSyncRequest(
        exchange_account_id=3,
        category="linear",
        settle_coin="usdt",
    )
    with patch(
        "app.api.v1.endpoints.portfolios."
        "PortfolioSyncService"
    ) as service_class:
        service = service_class.return_value
        service.synchronize = AsyncMock(
            return_value=build_execution_result()
        )
        response = await synchronize_my_portfolio(
            portfolio_id=2,
            data=request,
            current_user=current_user,
            db=db,
        )
    service_class.assert_called_once_with(db)
    service.synchronize.assert_awaited_once_with(
        current_user=current_user,
        portfolio_id=2,
        exchange_account_id=3,
        category="linear",
        settle_coin="usdt",
    )
    assert response["success"] is True
    assert (
        response["data"]["snapshot"]["status"]
        == "SUCCESS"
    )
    assert (
        response["data"]["portfolio_total_value"]
        == 1250.0
    )
@pytest.mark.asyncio
async def test_latest_endpoint_serializes_snapshot():
    current_user = SimpleNamespace(id=1)
    db = MagicMock()
    with patch(
        "app.api.v1.endpoints.portfolios."
        "PortfolioSyncService"
    ) as service_class:
        service = service_class.return_value
        service.get_latest_snapshot = MagicMock(
            return_value=build_snapshot()
        )
        response = await get_latest_portfolio_sync(
            portfolio_id=2,
            exchange_account_id=3,
            current_user=current_user,
            db=db,
        )
    service.get_latest_snapshot.assert_called_once_with(
        current_user=current_user,
        portfolio_id=2,
        exchange_account_id=3,
    )
    assert response["success"] is True
    assert response["data"]["id"] == 10
    assert (
        response["data"]["total_equity_usd"]
        == 1250.0
    )
@pytest.mark.asyncio
async def test_history_endpoint_serializes_snapshots():
    current_user = SimpleNamespace(id=1)
    db = MagicMock()
    snapshots = [
        build_snapshot(snapshot_id=11),
        build_snapshot(snapshot_id=10),
    ]
    with patch(
        "app.api.v1.endpoints.portfolios."
        "PortfolioSyncService"
    ) as service_class:
        service = service_class.return_value
        service.list_snapshots = MagicMock(
            return_value=snapshots
        )
        response = (
            await list_portfolio_sync_history(
                portfolio_id=2,
                limit=25,
                current_user=current_user,
                db=db,
            )
        )
    service.list_snapshots.assert_called_once_with(
        current_user=current_user,
        portfolio_id=2,
        limit=25,
    )
    assert response["success"] is True
    assert len(response["data"]) == 2
    assert response["data"][0]["id"] == 11
    assert response["data"][1]["id"] == 10
@pytest.mark.asyncio
async def test_snapshot_endpoint_serializes_record():
    current_user = SimpleNamespace(id=1)
    db = MagicMock()
    with patch(
        "app.api.v1.endpoints.portfolios."
        "PortfolioSyncService"
    ) as service_class:
        service = service_class.return_value
        service.get_snapshot = MagicMock(
            return_value=build_snapshot(
                snapshot_id=15
            )
        )
        response = (
            await get_portfolio_sync_snapshot(
                portfolio_id=2,
                snapshot_id=15,
                current_user=current_user,
                db=db,
            )
        )
    service.get_snapshot.assert_called_once_with(
        current_user=current_user,
        portfolio_id=2,
        snapshot_id=15,
    )
    assert response["success"] is True
    assert response["data"]["id"] == 15
def build_read_service():
    service = PortfolioSyncService(
        db=MagicMock(),
        client_factory=MagicMock(),
    )
    service.portfolio_service.get_portfolio = (
        MagicMock(
            return_value=SimpleNamespace(id=2)
        )
    )
    service.exchange_account_service.get_account = (
        MagicMock(
            return_value=SimpleNamespace(id=3)
        )
    )
    return service
def test_latest_service_validates_ownership():
    service = build_read_service()
    current_user = SimpleNamespace(id=1)
    snapshot = build_snapshot()
    service.sync_repository.get_latest = (
        MagicMock(return_value=snapshot)
    )
    result = service.get_latest_snapshot(
        current_user=current_user,
        portfolio_id=2,
        exchange_account_id=3,
    )
    assert result is snapshot
    service.portfolio_service.get_portfolio.assert_called_once_with(
        current_user=current_user,
        portfolio_id=2,
    )
    service.exchange_account_service.get_account.assert_called_once_with(
        current_user=current_user,
        account_id=3,
    )
    service.sync_repository.get_latest.assert_called_once_with(
        user_id=1,
        portfolio_id=2,
        exchange_account_id=3,
    )
def test_latest_service_raises_when_missing():
    service = build_read_service()
    service.sync_repository.get_latest = MagicMock(
        return_value=None
    )
    with pytest.raises(HTTPException) as exc_info:
        service.get_latest_snapshot(
            current_user=SimpleNamespace(id=1),
            portfolio_id=2,
        )
    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == (
            "Portfolio synchronization "
            "snapshot not found"
        )
    )
def test_history_service_validates_portfolio():
    service = build_read_service()
    current_user = SimpleNamespace(id=1)
    snapshots = [
        build_snapshot(snapshot_id=11),
        build_snapshot(snapshot_id=10),
    ]
    service.sync_repository.list_by_portfolio = (
        MagicMock(return_value=snapshots)
    )
    result = service.list_snapshots(
        current_user=current_user,
        portfolio_id=2,
        limit=25,
    )
    assert result == snapshots
    service.portfolio_service.get_portfolio.assert_called_once_with(
        current_user=current_user,
        portfolio_id=2,
    )
    service.sync_repository.list_by_portfolio.assert_called_once_with(
        user_id=1,
        portfolio_id=2,
        limit=25,
    )
def test_snapshot_service_rejects_other_portfolio():
    service = build_read_service()
    service.sync_repository.get_by_id_and_user = (
        MagicMock(
            return_value=build_snapshot(
                snapshot_id=15,
                portfolio_id=99,
            )
        )
    )
    with pytest.raises(HTTPException) as exc_info:
        service.get_snapshot(
            current_user=SimpleNamespace(id=1),
            portfolio_id=2,
            snapshot_id=15,
        )
    assert exc_info.value.status_code == 404
    assert (
        exc_info.value.detail
        == (
            "Portfolio synchronization "
            "snapshot not found"
        )
    )
