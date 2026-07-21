from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    Mock,
)
import pytest
from fastapi import (
    HTTPException,
)
from app.schemas.ai_context import (
    AIContextRequest,
)
from app.schemas.alert import (
    AlertResponse,
)
from app.schemas.automation import (
    AutomationRuntimeHealth,
    AutomationSchedulerSnapshot,
    AutomationWorkerSnapshot,
)
from app.schemas.exchange_account import (
    ExchangeAccountResponse,
)
from app.schemas.notification_preference import (
    NotificationPreferenceResponse,
)
from app.schemas.portfolio import (
    PortfolioResponse,
)
from app.schemas.portfolio_sync import (
    PortfolioSyncSnapshotResponse,
)
from app.schemas.risk_management import (
    RiskConfiguration,
)
from app.schemas.watchlist import (
    WatchlistResponse,
)
from app.services.ai_context_service import (
    AIContextBuilderService,
)
def _now():
    return datetime.now(UTC)
def _portfolio():
    return PortfolioResponse(
        id=10,
        user_id=7,
        name="Main Portfolio",
        base_currency="USDT",
        total_value=1000,
        profit_loss=50,
        created_at=_now(),
    )
def _watchlist_item():
    return WatchlistResponse(
        id=20,
        user_id=7,
        symbol="BTCUSDT",
        exchange="BYBIT",
        created_at=_now(),
    )
def _alert():
    return AlertResponse(
        id=30,
        user_id=7,
        symbol="BTCUSDT",
        exchange="BYBIT",
        alert_type="ABOVE",
        target_value=100000,
        is_enabled=True,
        triggered=False,
        created_at=_now(),
    )
def _account():
    return ExchangeAccountResponse(
        id=40,
        user_id=7,
        exchange_name="BYBIT",
        account_name="Primary",
        is_testnet=True,
        is_active=True,
        created_at=_now(),
    )
def _preferences():
    return NotificationPreferenceResponse(
        id=50,
        user_id=7,
        email_enabled=True,
        push_enabled=True,
        sound_enabled=True,
        price_alerts=True,
        arbitrage_alerts=True,
        ai_alerts=True,
        news_alerts=False,
        updated_at=_now(),
    )
def _snapshot():
    return PortfolioSyncSnapshotResponse(
        id=60,
        user_id=7,
        portfolio_id=10,
        exchange_account_id=40,
        exchange_name="BYBIT",
        account_type="UNIFIED",
        category="linear",
        settle_coin="USDT",
        status="SUCCESS",
        fingerprint="a" * 64,
        sync_version=1,
        total_equity_usd=1000,
        total_wallet_balance_usd=950,
        total_available_balance_usd=400,
        total_unrealized_pnl_usd=25,
        total_realized_pnl_usd=10,
        total_position_value_usd=500,
        coin_count=2,
        open_position_count=1,
        open_order_count=1,
        balance_payload={
            "total": 1000,
            "api_key": "DO-NOT-EXPOSE",
            "nested": {
                "authorization": "Bearer secret",
                "safe_value": 5,
            },
        },
        positions_payload=[
            {
                "symbol": "BTCUSDT",
                "size": 0.01,
                "api_secret": "DO-NOT-EXPOSE",
            },
        ],
        orders_payload=[
            {
                "order_id": "abc",
                "signature": "DO-NOT-EXPOSE",
            },
        ],
        error_message=None,
        synced_at=_now(),
        created_at=_now(),
    )
def _runtime():
    runtime = Mock()
    runtime.health.return_value = (
        AutomationRuntimeHealth(
            healthy=True,
            started=True,
            handlers_registered=True,
            worker=AutomationWorkerSnapshot(
                running=True,
                accepting_jobs=True,
                queue_size=0,
                total_jobs=0,
                queued_count=0,
                running_count=0,
                succeeded_count=0,
                failed_count=0,
                cancelled_count=0,
                total_attempts=0,
                retried_job_count=0,
                registered_job_types=[
                    "TRADE_MARKET_ORDER",
                    "TRADE_LIMIT_ORDER",
                ],
            ),
            scheduler=(
                AutomationSchedulerSnapshot(
                    registered_schedule_count=0,
                    running_schedule_count=0,
                    total_submissions=0,
                    total_created_jobs=0,
                    total_duplicate_submissions=0,
                    total_failures=0,
                    schedules=[],
                )
            ),
        )
    )
    return runtime
def _build_service():
    portfolio_service = Mock()
    portfolio_service.list_portfolios.return_value = [
        _portfolio()
    ]
    portfolio_service.get_portfolio.return_value = (
        _portfolio()
    )
    portfolio_sync_service = Mock()
    portfolio_sync_service.get_latest_snapshot.return_value = (
        _snapshot()
    )
    watchlist_service = Mock()
    watchlist_service.list_items.return_value = [
        _watchlist_item()
    ]
    alert_service = Mock()
    alert_service.list_alerts.return_value = [
        _alert()
    ]
    exchange_account_service = Mock()
    exchange_account_service.list_accounts.return_value = [
        _account()
    ]
    exchange_account_service.get_account.return_value = (
        _account()
    )
    preference_repository = Mock()
    preference_repository.get_by_user_id.return_value = (
        _preferences()
    )
    risk_service = Mock()
    risk_service.get_configuration.return_value = (
        RiskConfiguration()
    )
    service = AIContextBuilderService(
        None,
        runtime=_runtime(),
        portfolio_service=(
            portfolio_service
        ),
        portfolio_sync_service=(
            portfolio_sync_service
        ),
        watchlist_service=(
            watchlist_service
        ),
        alert_service=alert_service,
        exchange_account_service=(
            exchange_account_service
        ),
        preference_repository=(
            preference_repository
        ),
        risk_service_getter=(
            lambda user_id: risk_service
        ),
        clock_ms=lambda: 123456789,
    )
    dependencies = {
        "portfolio": portfolio_service,
        "portfolio_sync": (
            portfolio_sync_service
        ),
        "watchlist": watchlist_service,
        "alerts": alert_service,
        "accounts": (
            exchange_account_service
        ),
        "preferences": (
            preference_repository
        ),
        "risk": risk_service,
    }
    return service, dependencies
def test_context_uses_authenticated_user():
    service, dependencies = (
        _build_service()
    )
    user = SimpleNamespace(id=7)
    service.build(
        current_user=user,
        request=AIContextRequest(),
    )
    dependencies[
        "portfolio"
    ].list_portfolios.assert_called_once_with(
        current_user=user
    )
    dependencies[
        "watchlist"
    ].list_items.assert_called_once_with(
        current_user=user
    )
    dependencies[
        "alerts"
    ].list_alerts.assert_called_once_with(
        current_user=user
    )
    dependencies[
        "accounts"
    ].list_accounts.assert_called_once_with(
        current_user=user
    )
    dependencies[
        "preferences"
    ].get_by_user_id.assert_called_once_with(
        7
    )
def test_selected_resources_are_user_scoped():
    service, dependencies = (
        _build_service()
    )
    user = SimpleNamespace(id=7)
    response = service.build(
        current_user=user,
        request=AIContextRequest(
            portfolio_id=10,
            exchange_account_id=40,
        ),
    )
    dependencies[
        "portfolio"
    ].get_portfolio.assert_called_once_with(
        current_user=user,
        portfolio_id=10,
    )
    dependencies[
        "accounts"
    ].get_account.assert_called_once_with(
        current_user=user,
        account_id=40,
    )
    dependencies[
        "portfolio_sync"
    ].get_latest_snapshot.assert_called_once_with(
        current_user=user,
        portfolio_id=10,
        exchange_account_id=40,
    )
    assert (
        response.selected_portfolio.id
        == 10
    )
    assert (
        response
        .selected_exchange_account
        .id
        == 40
    )
def test_sensitive_snapshot_values_are_removed():
    service, _ = _build_service()
    response = service.build(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIContextRequest(
            portfolio_id=10,
            exchange_account_id=40,
        ),
    )
    snapshot = (
        response
        .latest_portfolio_snapshot
    )
    serialized = str(
        snapshot.model_dump()
    )
    assert "DO-NOT-EXPOSE" not in serialized
    assert (
        "api_key"
        not in snapshot.balance_payload
    )
    assert (
        "authorization"
        not in snapshot
        .balance_payload["nested"]
    )
    assert (
        "safe_value"
        in snapshot
        .balance_payload["nested"]
    )
def test_exchange_credentials_are_not_exposed():
    service, _ = _build_service()
    response = service.build(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIContextRequest(),
    )
    account_data = (
        response.exchange_accounts[0]
        .model_dump()
    )
    assert "encrypted_api_key" not in account_data
    assert "encrypted_api_secret" not in account_data
    assert "api_key" not in account_data
    assert "api_secret" not in account_data
def test_missing_snapshot_is_optional():
    service, dependencies = (
        _build_service()
    )
    dependencies[
        "portfolio_sync"
    ].get_latest_snapshot.side_effect = (
        HTTPException(
            status_code=404,
            detail=(
                "Portfolio synchronization "
                "snapshot not found"
            ),
        )
    )
    response = service.build(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIContextRequest(
            portfolio_id=10
        ),
    )
    assert (
        response
        .latest_portfolio_snapshot
        is None
    )
def test_unexpected_snapshot_error_is_raised():
    service, dependencies = (
        _build_service()
    )
    dependencies[
        "portfolio_sync"
    ].get_latest_snapshot.side_effect = (
        HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )
    )
    with pytest.raises(
        HTTPException,
        match="Portfolio not found",
    ):
        service.build(
            current_user=(
                SimpleNamespace(id=7)
            ),
            request=AIContextRequest(
                portfolio_id=10
            ),
        )
def test_preferences_are_read_only():
    service, dependencies = (
        _build_service()
    )
    service.build(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIContextRequest(),
    )
    dependencies[
        "preferences"
    ].create_default.assert_not_called()
def test_context_metadata_and_safety_flags():
    service, _ = _build_service()
    response = service.build(
        current_user=(
            SimpleNamespace(id=7)
        ),
        request=AIContextRequest(),
    )
    assert response.generated_at_ms == 123456789
    assert response.user_id == 7
    assert response.portfolio_count == 1
    assert response.watchlist_count == 1
    assert response.alert_count == 1
    assert response.exchange_account_count == 1
    assert response.advisory_only is True
    assert response.execution_enabled is False
    assert response.automation.healthy is True
