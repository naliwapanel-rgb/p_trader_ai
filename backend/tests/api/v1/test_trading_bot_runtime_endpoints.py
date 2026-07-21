from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
)
from fastapi import (
    FastAPI,
    HTTPException,
)
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.testclient import (
    TestClient,
)
from app.api.automation_dependencies import (
    get_automation_runtime,
)
from app.api.dependencies import (
    get_current_user,
)
from app.api.v1.endpoints import (
    trading_bots as endpoint_module,
)
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
)
from app.database.session import (
    get_db,
)
from app.schemas.trading_bot import (
    TradingBotLifecycleActionResult,
    TradingBotResponse,
)
def build_result(
    *,
    action: str,
    previous_status: str,
    status: str,
):
    timestamp = datetime(
        2026,
        7,
        21,
        14,
        0,
        tzinfo=UTC,
    )
    bot = TradingBotResponse(
        id=10,
        user_id=7,
        exchange_account_id=3,
        name="Runtime Bot",
        description=None,
        strategy_type="MOMENTUM",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        status=status,
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1,
        max_position_value_usd=25,
        max_daily_loss_percent=3,
        max_drawdown_percent=10,
        stop_loss_percent=2,
        take_profit_percent=4,
        strategy_config={},
        created_at=timestamp,
        updated_at=timestamp,
    )
    return TradingBotLifecycleActionResult(
        action=action,
        previous_status=previous_status,
        status=status,
        changed=True,
        bot=bot,
    )
def build_app(
    *,
    lifecycle_service,
    runtime_service,
):
    app = FastAPI()
    app.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.include_router(
        endpoint_module.router,
        prefix="/api/v1",
    )
    app.dependency_overrides[get_db] = (
        lambda: MagicMock()
    )
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=7,
        is_active=True,
    )
    app.dependency_overrides[
        get_automation_runtime
    ] = lambda: SimpleNamespace(
        bot_runtime_service=(
            runtime_service
        )
    )
    endpoint_module.TradingBotLifecycleService = (
        lambda db: lifecycle_service
    )
    return app
def test_start_endpoint_starts_runtime():
    lifecycle_service = SimpleNamespace(
        start_bot=MagicMock(
            return_value=build_result(
                action="START",
                previous_status="STOPPED",
                status="RUNNING",
            )
        )
    )
    runtime_service = SimpleNamespace(
        start_for_bot=AsyncMock(),
        stop_for_bot=AsyncMock(),
        mark_runtime_error=MagicMock(),
    )
    response = TestClient(
        build_app(
            lifecycle_service=(
                lifecycle_service
            ),
            runtime_service=runtime_service,
        )
    ).post(
        "/api/v1/trading-bots/10/start"
    )
    assert response.status_code == 200
    runtime_service.start_for_bot.assert_awaited_once()
def test_pause_endpoint_stops_runtime():
    lifecycle_service = SimpleNamespace(
        pause_bot=MagicMock(
            return_value=build_result(
                action="PAUSE",
                previous_status="RUNNING",
                status="PAUSED",
            )
        )
    )
    runtime_service = SimpleNamespace(
        start_for_bot=AsyncMock(),
        stop_for_bot=AsyncMock(),
        mark_runtime_error=MagicMock(),
    )
    response = TestClient(
        build_app(
            lifecycle_service=(
                lifecycle_service
            ),
            runtime_service=runtime_service,
        )
    ).post(
        "/api/v1/trading-bots/10/pause"
    )
    assert response.status_code == 200
    runtime_service.stop_for_bot.assert_awaited_once()
def test_runtime_start_failure_marks_error():
    lifecycle_service = SimpleNamespace(
        start_bot=MagicMock(
            return_value=build_result(
                action="START",
                previous_status="STOPPED",
                status="RUNNING",
            )
        )
    )
    runtime_service = SimpleNamespace(
        start_for_bot=AsyncMock(
            side_effect=RuntimeError(
                "scheduler unavailable"
            )
        ),
        stop_for_bot=AsyncMock(),
        mark_runtime_error=MagicMock(
            return_value=True
        ),
    )
    response = TestClient(
        build_app(
            lifecycle_service=(
                lifecycle_service
            ),
            runtime_service=runtime_service,
        )
    ).post(
        "/api/v1/trading-bots/10/start"
    )
    assert response.status_code == 503
    assert response.json()["success"] is False
    runtime_service.mark_runtime_error.assert_called_once()
