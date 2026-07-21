from datetime import (
    UTC,
    datetime,
    timedelta,
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
from fastapi.testclient import (
    TestClient,
)
from app.api.dependencies import (
    get_current_user,
)
from app.api.v1.endpoints import (
    trading_bot_backtest,
)
from app.database.session import (
    get_db,
)
from app.main import (
    app as main_app,
)
from app.schemas.trading_bot_backtest import (
    BacktestExecutionStep,
    BacktestPortfolioSnapshot,
    TradingBotBacktestExecutionResult,
)
from app.services.backtest_performance_service import (
    BacktestPerformanceService,
)
BASE_TIME = datetime(
    2026,
    6,
    1,
    tzinfo=UTC,
)
def request_payload():
    candles = []
    for index, price in enumerate([
        100,
        105,
    ]):
        opened_at = (
            BASE_TIME
            + timedelta(days=index)
        )
        candles.append({
            "opened_at": (
                opened_at.isoformat()
            ),
            "closed_at": (
                opened_at
                + timedelta(days=1)
            ).isoformat(),
            "open_price": price,
            "high_price": price + 2,
            "low_price": price - 2,
            "close_price": price,
            "volume": 100,
            "turnover_usd": (
                price * 100
            ),
        })
    return {
        "initial_balance_usd": 10000,
        "fee_rate": 0.0006,
        "slippage_rate": 0.0001,
        "force_close_at_end": True,
        "candles": candles,
    }
def build_result():
    portfolio = BacktestPortfolioSnapshot(
        initial_balance_usd=10000,
        cash_balance_usd=10000,
        reserved_balance_usd=0,
        equity_usd=10000,
        realized_pnl_usd=0,
        unrealized_pnl_usd=0,
        total_fees_usd=0,
        open_position=None,
    )
    execution = (
        TradingBotBacktestExecutionResult(
            bot_id=10,
            symbol="BTCUSDT",
            category="linear",
            timeframe="1d",
            started_at=BASE_TIME,
            ended_at=(
                BASE_TIME
                + timedelta(days=2)
            ),
            frames_processed=2,
            warmup_frame_count=1,
            evaluated_frame_count=1,
            order_count=0,
            completed_trade_count=0,
            orders=[],
            completed_trades=[],
            steps=[
                BacktestExecutionStep(
                    sequence=1,
                    candle_closed_at=(
                        BASE_TIME
                        + timedelta(days=1)
                    ),
                    warmup_complete=False,
                    decision=None,
                    outcomes=["WARMUP"],
                    orders=[],
                    portfolio=portfolio,
                ),
                BacktestExecutionStep(
                    sequence=2,
                    candle_closed_at=(
                        BASE_TIME
                        + timedelta(days=2)
                    ),
                    warmup_complete=True,
                    decision=None,
                    outcomes=[
                        "NO_ACTION"
                    ],
                    orders=[],
                    portfolio=portfolio,
                ),
            ],
            final_portfolio=portfolio,
        )
    )
    return (
        BacktestPerformanceService
        .analyze(execution)
    )
def build_app(
    *,
    authenticated: bool,
):
    app = FastAPI()
    app.include_router(
        trading_bot_backtest.router
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
        trading_bot_backtest,
        "TradingBotBacktestService",
        lambda db: service,
    )
def test_backtest_requires_authentication():
    app, _, _ = build_app(
        authenticated=False
    )
    with TestClient(app) as client:
        response = client.post(
            "/trading-bots/10/backtest",
            json=request_payload(),
        )
    assert response.status_code == 401
def test_run_backtest_endpoint(
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
    service.run_backtest = AsyncMock(
        return_value=build_result()
    )
    install_service(
        monkeypatch,
        service,
    )
    payload = request_payload()
    with TestClient(app) as client:
        response = client.post(
            "/trading-bots/10/backtest",
            json=payload,
        )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert (
        body["message"]
        == (
            "Trading bot backtest completed "
            "successfully"
        )
    )
    data = body["data"]
    assert (
        data["execution"]["bot_id"]
        == 10
    )
    assert (
        data["execution"]
        ["frames_processed"]
        == 2
    )
    assert (
        data["performance"]
        ["final_equity_usd"]
        == 10000
    )
    call = (
        service.run_backtest
        .await_args
    )
    assert (
        call.kwargs["current_user"]
        is current_user
    )
    assert call.kwargs["bot_id"] == 10
    assert (
        len(
            call.kwargs[
                "data"
            ].candles
        )
        == 2
    )
def test_backtest_service_error_is_preserved(
    monkeypatch,
):
    app, _, _ = build_app(
        authenticated=True
    )
    service = MagicMock()
    service.run_backtest = AsyncMock(
        side_effect=HTTPException(
            status_code=404,
            detail="Trading bot not found",
        )
    )
    install_service(
        monkeypatch,
        service,
    )
    with TestClient(app) as client:
        response = client.post(
            "/trading-bots/999/backtest",
            json=request_payload(),
        )
    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Trading bot not found"
    )
def test_backtest_requires_two_candles(
    monkeypatch,
):
    app, _, _ = build_app(
        authenticated=True
    )
    service = MagicMock()
    service.run_backtest = AsyncMock()
    install_service(
        monkeypatch,
        service,
    )
    payload = request_payload()
    payload["candles"] = (
        payload["candles"][:1]
    )
    with TestClient(app) as client:
        response = client.post(
            "/trading-bots/10/backtest",
            json=payload,
        )
    assert response.status_code == 422
    service.run_backtest.assert_not_awaited()
def test_backtest_rejects_unknown_settings(
    monkeypatch,
):
    app, _, _ = build_app(
        authenticated=True
    )
    service = MagicMock()
    service.run_backtest = AsyncMock()
    install_service(
        monkeypatch,
        service,
    )
    payload = request_payload()
    payload["live_execution"] = True
    with TestClient(app) as client:
        response = client.post(
            "/trading-bots/10/backtest",
            json=payload,
        )
    assert response.status_code == 422
    service.run_backtest.assert_not_awaited()
def test_main_openapi_registers_backtest_route():
    main_app.openapi_schema = None
    paths = main_app.openapi()["paths"]
    assert (
        "/api/v1/trading-bots/"
        "{bot_id}/backtest"
        in paths
    )
    methods = paths[
        (
            "/api/v1/trading-bots/"
            "{bot_id}/backtest"
        )
    ]
    assert "post" in methods
