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
def build_bot(
    *,
    bot_id: int = 10,
    name: str = "BTC Bot",
    status: str = "DRAFT",
):
    timestamp = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )
    return SimpleNamespace(
        id=bot_id,
        user_id=7,
        exchange_account_id=3,
        name=name,
        description="API test bot",
        strategy_type="MOMENTUM",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        status=status,
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1.0,
        max_position_value_usd=25.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        stop_loss_percent=2.0,
        take_profit_percent=4.0,
        strategy_config={
            "period": 14,
        },
        last_error=None,
        started_at=None,
        stopped_at=None,
        last_run_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )
def build_payload():
    return {
        "exchange_account_id": 3,
        "name": "BTC Bot",
        "description": "API test bot",
        "strategy_type": "MOMENTUM",
        "symbol": "BTCUSDT",
        "category": "linear",
        "timeframe": "5m",
        "paper_trading": True,
        "dry_run": True,
        "risk_per_trade_percent": 1,
        "max_position_value_usd": 25,
        "max_daily_loss_percent": 3,
        "max_drawdown_percent": 10,
        "stop_loss_percent": 2,
        "take_profit_percent": 4,
        "strategy_config": {
            "period": 14,
        },
    }
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
        "TradingBotService",
        lambda db: service,
    )
def test_routes_require_authentication():
    client = TestClient(
        build_app(
            authenticated=False
        )
    )
    requests = [
        (
            "GET",
            "/api/v1/trading-bots",
            None,
        ),
        (
            "POST",
            "/api/v1/trading-bots",
            build_payload(),
        ),
        (
            "GET",
            "/api/v1/trading-bots/10",
            None,
        ),
        (
            "PUT",
            "/api/v1/trading-bots/10",
            {
                "name": "Updated Bot",
            },
        ),
        (
            "DELETE",
            "/api/v1/trading-bots/10",
            None,
        ),
    ]
    for method, url, payload in requests:
        response = client.request(
            method,
            url,
            json=payload,
        )
        assert response.status_code == 401
def test_list_trading_bots(
    monkeypatch,
):
    bot = build_bot()
    service = SimpleNamespace(
        list_bots=MagicMock(
            return_value=[bot]
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    client = TestClient(build_app())
    response = client.get(
        (
            "/api/v1/trading-bots"
            "?status=DRAFT"
            "&limit=25"
            "&offset=5"
        )
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["id"] == 10
    assert (
        body["data"][0]["symbol"]
        == "BTCUSDT"
    )
    service.list_bots.assert_called_once()
    call = (
        service.list_bots.call_args.kwargs
    )
    assert call["current_user"].id == 7
    assert call["bot_status"] == "DRAFT"
    assert call["limit"] == 25
    assert call["offset"] == 5
def test_create_trading_bot(
    monkeypatch,
):
    bot = build_bot()
    service = SimpleNamespace(
        create_bot=MagicMock(
            return_value=bot
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    client = TestClient(build_app())
    response = client.post(
        "/api/v1/trading-bots",
        json=build_payload(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == 10
    assert (
        body["message"]
        == (
            "Trading bot created "
            "successfully"
        )
    )
def test_get_trading_bot(
    monkeypatch,
):
    service = SimpleNamespace(
        get_bot=MagicMock(
            return_value=build_bot()
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    client = TestClient(build_app())
    response = client.get(
        "/api/v1/trading-bots/10"
    )
    assert response.status_code == 200
    assert response.json()["data"]["id"] == 10
    call = (
        service.get_bot.call_args.kwargs
    )
    assert call["bot_id"] == 10
    assert call["current_user"].id == 7
def test_update_trading_bot(
    monkeypatch,
):
    service = SimpleNamespace(
        update_bot=MagicMock(
            return_value=build_bot(
                name="Updated Bot",
                status="STOPPED",
            )
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    client = TestClient(build_app())
    response = client.put(
        "/api/v1/trading-bots/10",
        json={
            "name": "Updated Bot",
            "status": "STOPPED",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert (
        body["data"]["name"]
        == "Updated Bot"
    )
    assert (
        body["data"]["status"]
        == "STOPPED"
    )
def test_delete_trading_bot(
    monkeypatch,
):
    service = SimpleNamespace(
        delete_bot=MagicMock(
            return_value=None
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    client = TestClient(build_app())
    response = client.delete(
        "/api/v1/trading-bots/10"
    )
    assert response.status_code == 200
    assert response.json()["data"] is None
    call = (
        service.delete_bot.call_args.kwargs
    )
    assert call["bot_id"] == 10
    assert call["current_user"].id == 7
def test_service_error_is_preserved(
    monkeypatch,
):
    service = SimpleNamespace(
        get_bot=MagicMock(
            side_effect=HTTPException(
                status_code=404,
                detail=(
                    "Trading bot not found"
                ),
            )
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    client = TestClient(build_app())
    response = client.get(
        "/api/v1/trading-bots/999"
    )
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert (
        body["message"]
        == "Trading bot not found"
    )
def test_invalid_filters_are_rejected():
    client = TestClient(build_app())
    response = client.get(
        (
            "/api/v1/trading-bots"
            "?status=UNKNOWN"
            "&limit=0"
        )
    )
    assert response.status_code == 422
    assert response.json()["success"] is False
def test_main_openapi_registers_routes():
    paths = main_app.openapi()["paths"]
    collection = (
        "/api/v1/trading-bots"
    )
    detail = (
        "/api/v1/trading-bots/{bot_id}"
    )
    assert collection in paths
    assert detail in paths
    assert {
        "get",
        "post",
    }.issubset(paths[collection])
    assert {
        "get",
        "put",
        "delete",
    }.issubset(paths[detail])
