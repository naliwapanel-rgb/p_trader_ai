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
from fastapi.testclient import (
    TestClient,
)
from app.api.dependencies import (
    get_current_user,
)
from app.api.v1.endpoints import (
    trading_bot_history,
)
from app.database.session import (
    get_db,
)
from app.main import (
    app as main_app,
)
from app.schemas.paper_trading import (
    PaperTradingAccountResponse,
    PaperTradingOrderResponse,
    PaperTradingPositionResponse,
)
from app.schemas.trading_bot_performance import (
    PaperTradingAccountSummaryResult,
    PaperTradingOrderHistoryResult,
    PaperTradingPerformanceResult,
    PaperTradingPositionHistoryResult,
)
NOW = datetime(
    2026,
    7,
    21,
    19,
    0,
    tzinfo=UTC,
)
def build_account():
    return PaperTradingAccountResponse(
        id=20,
        user_id=7,
        trading_bot_id=10,
        currency="USDT",
        initial_balance_usd=10000,
        cash_balance_usd=9980,
        reserved_balance_usd=25,
        equity_usd=10010,
        realized_pnl_usd=8,
        unrealized_pnl_usd=5,
        total_fees_usd=3,
        status="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
    )
def build_order():
    return PaperTradingOrderResponse(
        id=30,
        user_id=7,
        trading_bot_id=10,
        paper_account_id=20,
        paper_position_id=40,
        symbol="BTCUSDT",
        category="linear",
        side="BUY",
        position_effect="OPEN",
        status="FILLED",
        quantity=0.25,
        reference_price=100,
        fill_price=100.01,
        gross_value_usd=25.0025,
        fee_rate=0.0006,
        fee_usd=0.0150015,
        slippage_rate=0.0001,
        slippage_usd=0.0025,
        realized_pnl_usd=0,
        decision_reason="Test signal",
        filled_at=NOW,
        created_at=NOW,
    )
def build_position():
    return PaperTradingPositionResponse(
        id=40,
        user_id=7,
        trading_bot_id=10,
        paper_account_id=20,
        symbol="BTCUSDT",
        category="linear",
        side="LONG",
        status="CLOSED",
        quantity=0.25,
        average_entry_price=100.01,
        current_price=110,
        position_value_usd=0,
        reserved_margin_usd=0,
        unrealized_pnl_usd=0,
        realized_pnl_usd=2.4975,
        total_fees_usd=0.0315,
        opened_at=NOW,
        closed_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
def build_app(
    *,
    authenticated: bool,
):
    app = FastAPI()
    app.include_router(
        trading_bot_history.router
    )
    current_user = SimpleNamespace(
        id=7
    )
    db = MagicMock()
    if authenticated:
        app.dependency_overrides[
            get_current_user
        ] = lambda: current_user
        app.dependency_overrides[
            get_db
        ] = lambda: db
    return (
        app,
        current_user,
        db,
    )
def install_service(
    monkeypatch,
    service,
):
    monkeypatch.setattr(
        trading_bot_history,
        "PaperTradingHistoryService",
        lambda db: service,
    )
def test_history_routes_require_authentication():
    app, _, _ = build_app(
        authenticated=False
    )
    paths = [
        (
            "/trading-bots/10/"
            "paper-trading/account"
        ),
        (
            "/trading-bots/10/"
            "paper-trading/orders"
        ),
        (
            "/trading-bots/10/"
            "paper-trading/positions"
        ),
        (
            "/trading-bots/10/"
            "paper-trading/performance"
        ),
    ]
    with TestClient(app) as client:
        responses = [
            client.get(path)
            for path in paths
        ]
    assert all(
        response.status_code == 401
        for response in responses
    )
def test_get_paper_trading_account(
    monkeypatch,
):
    (
        app,
        current_user,
        _,
    ) = build_app(
        authenticated=True
    )
    service = MagicMock()
    service.get_account_summary.return_value = (
        PaperTradingAccountSummaryResult(
            bot_id=10,
            account=build_account(),
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    with TestClient(app) as client:
        response = client.get(
            (
                "/trading-bots/10/"
                "paper-trading/account"
            )
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["bot_id"] == 10
    assert data["account"]["id"] == 20
    assert data["account"]["equity_usd"] == 10010
    service.get_account_summary.assert_called_once_with(
        current_user=current_user,
        bot_id=10,
    )
def test_list_paper_trading_orders(
    monkeypatch,
):
    (
        app,
        current_user,
        _,
    ) = build_app(
        authenticated=True
    )
    service = MagicMock()
    service.list_orders.return_value = (
        PaperTradingOrderHistoryResult(
            bot_id=10,
            paper_account_id=20,
            total_count=7,
            limit=2,
            offset=4,
            items=[
                build_order()
            ],
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    with TestClient(app) as client:
        response = client.get(
            (
                "/trading-bots/10/"
                "paper-trading/orders"
                "?limit=2&offset=4"
            )
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_count"] == 7
    assert data["limit"] == 2
    assert data["offset"] == 4
    assert data["items"][0]["id"] == 30
    service.list_orders.assert_called_once_with(
        current_user=current_user,
        bot_id=10,
        limit=2,
        offset=4,
    )
def test_list_paper_trading_positions(
    monkeypatch,
):
    (
        app,
        current_user,
        _,
    ) = build_app(
        authenticated=True
    )
    service = MagicMock()
    service.list_positions.return_value = (
        PaperTradingPositionHistoryResult(
            bot_id=10,
            paper_account_id=20,
            position_status="CLOSED",
            total_count=3,
            limit=10,
            offset=0,
            items=[
                build_position()
            ],
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    with TestClient(app) as client:
        response = client.get(
            (
                "/trading-bots/10/"
                "paper-trading/positions"
                "?status=CLOSED"
                "&limit=10"
                "&offset=0"
            )
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["position_status"] == "CLOSED"
    assert data["total_count"] == 3
    assert data["items"][0]["status"] == "CLOSED"
    service.list_positions.assert_called_once_with(
        current_user=current_user,
        bot_id=10,
        position_status="CLOSED",
        limit=10,
        offset=0,
    )
def test_get_paper_trading_performance(
    monkeypatch,
):
    (
        app,
        current_user,
        _,
    ) = build_app(
        authenticated=True
    )
    service = MagicMock()
    service.get_performance.return_value = (
        PaperTradingPerformanceResult(
            bot_id=10,
            paper_account_id=20,
            currency="USDT",
            initial_balance_usd=10000,
            cash_balance_usd=9980,
            reserved_balance_usd=25,
            equity_usd=10010,
            order_count=8,
            trade_count=4,
            completed_trade_count=3,
            open_trade_count=1,
            winning_trade_count=2,
            losing_trade_count=1,
            breakeven_trade_count=0,
            gross_realized_pnl_usd=13,
            realized_fees_usd=3,
            net_realized_pnl_usd=10,
            unrealized_pnl_usd=5,
            total_fees_usd=4,
            total_net_pnl_usd=10,
            gross_profit_usd=15,
            gross_loss_usd=5,
            win_rate_percent=(
                66.6666666667
            ),
            average_win_usd=7.5,
            average_loss_usd=-5,
            profit_factor=3,
            return_percent=0.1,
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    with TestClient(app) as client:
        response = client.get(
            (
                "/trading-bots/10/"
                "paper-trading/performance"
            )
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["order_count"] == 8
    assert data["trade_count"] == 4
    assert data["completed_trade_count"] == 3
    assert data["win_rate_percent"] > 66
    assert data["profit_factor"] == 3
    service.get_performance.assert_called_once_with(
        current_user=current_user,
        bot_id=10,
    )
def test_history_service_error_is_preserved(
    monkeypatch,
):
    app, _, _ = build_app(
        authenticated=True
    )
    service = MagicMock()
    service.get_performance.side_effect = (
        HTTPException(
            status_code=404,
            detail=(
                "Paper trading account "
                "not found"
            ),
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    with TestClient(app) as client:
        response = client.get(
            (
                "/trading-bots/10/"
                "paper-trading/performance"
            )
        )
    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Paper trading account not found"
    )
def test_history_query_validation():
    app, _, _ = build_app(
        authenticated=True
    )
    with TestClient(app) as client:
        bad_limit = client.get(
            (
                "/trading-bots/10/"
                "paper-trading/orders"
                "?limit=0"
            )
        )
        bad_offset = client.get(
            (
                "/trading-bots/10/"
                "paper-trading/orders"
                "?offset=-1"
            )
        )
        bad_status = client.get(
            (
                "/trading-bots/10/"
                "paper-trading/positions"
                "?status=INVALID"
            )
        )
    assert bad_limit.status_code == 422
    assert bad_offset.status_code == 422
    assert bad_status.status_code == 422
def test_main_openapi_registers_history_routes():
    paths = main_app.openapi()["paths"]
    expected = {
        (
            "/api/v1/trading-bots/"
            "{bot_id}/paper-trading/account"
        ),
        (
            "/api/v1/trading-bots/"
            "{bot_id}/paper-trading/orders"
        ),
        (
            "/api/v1/trading-bots/"
            "{bot_id}/paper-trading/positions"
        ),
        (
            "/api/v1/trading-bots/"
            "{bot_id}/paper-trading/performance"
        ),
    }
    assert expected.issubset(
        set(paths)
    )
