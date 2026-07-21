from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
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
from app.main import app as main_app
from app.schemas.trading_bot import (
    TradingBotLifecycleActionResult,
    TradingBotResponse,
)
def build_bot(
    *,
    status: str,
):
    timestamp = datetime(
        2026,
        7,
        21,
        13,
        0,
        tzinfo=UTC,
    )
    return TradingBotResponse(
        id=10,
        user_id=7,
        exchange_account_id=3,
        name="Lifecycle Bot",
        description="Lifecycle API bot",
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
        strategy_config={
            "period": 14,
        },
        created_at=timestamp,
        updated_at=timestamp,
    )
def build_result(
    *,
    action: str,
    previous_status: str,
    status: str,
    changed: bool = True,
):
    return TradingBotLifecycleActionResult(
        action=action,
        previous_status=previous_status,
        status=status,
        changed=changed,
        bot=build_bot(
            status=status
        ),
    )
def build_app(
    *,
    authenticated: bool = True,
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
    if authenticated:
        app.dependency_overrides[
            get_current_user
        ] = lambda: SimpleNamespace(
            id=7,
            is_active=True,
        )
    return app
def install_service(
    monkeypatch,
    service,
):
    monkeypatch.setattr(
        endpoint_module,
        "TradingBotLifecycleService",
        lambda db: service,
    )
def test_lifecycle_routes_require_authentication():
    client = TestClient(
        build_app(
            authenticated=False
        )
    )
    for action in (
        "prepare",
        "start",
        "pause",
        "resume",
        "stop",
    ):
        response = client.post(
            (
                "/api/v1/trading-bots/"
                f"10/{action}"
            )
        )
        assert response.status_code == 401
def test_prepare_endpoint(
    monkeypatch,
):
    service = SimpleNamespace(
        prepare_bot=MagicMock(
            return_value=build_result(
                action="PREPARE",
                previous_status="DRAFT",
                status="STOPPED",
            )
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    response = TestClient(
        build_app()
    ).post(
        "/api/v1/trading-bots/10/prepare"
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["status"]
        == "STOPPED"
    )
def test_start_endpoint(
    monkeypatch,
):
    service = SimpleNamespace(
        start_bot=MagicMock(
            return_value=build_result(
                action="START",
                previous_status="STOPPED",
                status="RUNNING",
            )
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    response = TestClient(
        build_app()
    ).post(
        "/api/v1/trading-bots/10/start"
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["status"]
        == "RUNNING"
    )
def test_pause_endpoint(
    monkeypatch,
):
    service = SimpleNamespace(
        pause_bot=MagicMock(
            return_value=build_result(
                action="PAUSE",
                previous_status="RUNNING",
                status="PAUSED",
            )
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    response = TestClient(
        build_app()
    ).post(
        "/api/v1/trading-bots/10/pause"
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["status"]
        == "PAUSED"
    )
def test_resume_endpoint(
    monkeypatch,
):
    service = SimpleNamespace(
        resume_bot=MagicMock(
            return_value=build_result(
                action="RESUME",
                previous_status="PAUSED",
                status="RUNNING",
            )
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    response = TestClient(
        build_app()
    ).post(
        "/api/v1/trading-bots/10/resume"
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["status"]
        == "RUNNING"
    )
def test_stop_endpoint(
    monkeypatch,
):
    service = SimpleNamespace(
        stop_bot=MagicMock(
            return_value=build_result(
                action="STOP",
                previous_status="RUNNING",
                status="STOPPED",
            )
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    response = TestClient(
        build_app()
    ).post(
        "/api/v1/trading-bots/10/stop"
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["status"]
        == "STOPPED"
    )
def test_lifecycle_error_is_preserved(
    monkeypatch,
):
    service = SimpleNamespace(
        start_bot=MagicMock(
            side_effect=HTTPException(
                status_code=409,
                detail=(
                    "Cannot start trading bot "
                    "while status is PAUSED"
                ),
            )
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    response = TestClient(
        build_app()
    ).post(
        "/api/v1/trading-bots/10/start"
    )
    assert response.status_code == 409
    assert response.json()["success"] is False
def test_main_openapi_registers_lifecycle():
    paths = main_app.openapi()["paths"]
    for action in (
        "prepare",
        "start",
        "pause",
        "resume",
        "stop",
    ):
        route = (
            "/api/v1/trading-bots/"
            f"{{bot_id}}/{action}"
        )
        assert route in paths
        assert "post" in paths[route]
