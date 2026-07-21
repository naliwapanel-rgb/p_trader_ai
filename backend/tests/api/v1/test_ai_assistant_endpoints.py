from datetime import (
    UTC,
    datetime,
)
from types import (
    SimpleNamespace,
)
import pytest
from fastapi.testclient import TestClient
from app.api.dependencies import (
    get_current_user,
)
from app.main import app
BASE_URL = "/api/v1/ai-assistant"
def _snapshot_payload():
    now = datetime.now(
        UTC
    ).isoformat()
    return {
        "id": 1,
        "user_id": 99,
        "portfolio_id": 2,
        "exchange_account_id": 3,
        "exchange_name": "BYBIT",
        "account_type": "UNIFIED",
        "category": "linear",
        "settle_coin": "USDT",
        "status": "SUCCESS",
        "fingerprint": "a" * 64,
        "sync_version": 1,
        "total_equity_usd": 1000.0,
        "total_wallet_balance_usd": 950.0,
        (
            "total_available_"
            "balance_usd"
        ): 400.0,
        (
            "total_unrealized_"
            "pnl_usd"
        ): 25.0,
        (
            "total_realized_"
            "pnl_usd"
        ): 10.0,
        (
            "total_position_"
            "value_usd"
        ): 500.0,
        "coin_count": 2,
        "open_position_count": 2,
        "open_order_count": 1,
        "balance_payload": {},
        "positions_payload": [],
        "orders_payload": [],
        "error_message": None,
        "synced_at": now,
        "created_at": now,
    }
def _risk_payload():
    return {
        "question": (
            "Why did this trade pass?"
        ),
        "risk_result": {
            "accepted": True,
            "side": "BUY",
            "risk_reward_ratio": 2.0,
            (
                "projected_total_"
                "exposure_percent"
            ): 35.0,
            (
                "current_daily_"
                "loss_percent"
            ): 1.0,
            (
                "current_drawdown_"
                "percent"
            ): 2.0,
            "checks": [
                {
                    "rule": "MAX_LEVERAGE",
                    "passed": True,
                    "actual_value": 3.0,
                    "limit_value": 10.0,
                    "message": (
                        "Leverage is within "
                        "the configured limit"
                    ),
                },
            ],
            "rejection_reasons": [],
            "warnings": [],
            "summary": (
                "Trade passed all configured "
                "pre-trade risk checks"
            ),
        },
    }
def _valid_requests():
    return [
        (
            f"{BASE_URL}/query",
            {
                "question": (
                    "What should I review?"
                ),
            },
        ),
        (
            (
                f"{BASE_URL}/"
                "market-analysis"
            ),
            {
                "request": {
                    "question": (
                        "Analyze BTC."
                    ),
                    "symbols": [
                        "BTCUSDT",
                    ],
                },
                "tickers": [],
            },
        ),
        (
            (
                f"{BASE_URL}/"
                "portfolio-analysis"
            ),
            {
                "request": {
                    "question": (
                        "Review my portfolio."
                    ),
                    "portfolio_id": 2,
                },
                "snapshot": (
                    _snapshot_payload()
                ),
            },
        ),
        (
            (
                f"{BASE_URL}/"
                "risk-explanation"
            ),
            _risk_payload(),
        ),
        (
            f"{BASE_URL}/trade-plan",
            {
                "question": (
                    "Create a BTC plan."
                ),
                "symbol": "BTCUSDT",
                "side": "BUY",
            },
        ),
        (
            (
                f"{BASE_URL}/"
                "arbitrage-explanation"
            ),
            {
                "question": (
                    "Explain this opportunity."
                ),
                "opportunity_type": (
                    "CROSS_EXCHANGE"
                ),
                "opportunity": {
                    (
                        "gross_spread_"
                        "percent"
                    ): 2.0,
                    (
                        "net_profit_"
                        "percent"
                    ): 1.2,
                },
            },
        ),
    ]
@pytest.fixture
def authenticated_client():
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=99,
        is_active=True,
    )
    try:
        with TestClient(
            app
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
def test_ai_assistant_routes_require_authentication():
    with TestClient(
        app
    ) as client:
        for url, payload in _valid_requests():
            response = client.post(
                url,
                json=payload,
            )
            assert (
                response.status_code
                == 401
            ), (
                url,
                response.text,
            )
def test_general_query_endpoint(
    authenticated_client,
):
    response = authenticated_client.post(
        f"{BASE_URL}/query",
        json={
            "question": (
                "What should I review?"
            ),
            "symbols": [
                "btcusdt",
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert (
        payload["data"]["status"]
        == "PARTIAL"
    )
    assert (
        payload["data"]
        ["metadata"]["provider"]
        == "DETERMINISTIC"
    )
    assert (
        payload["data"]
        ["execution_allowed"]
        is False
    )
def test_market_analysis_endpoint(
    authenticated_client,
):
    response = authenticated_client.post(
        (
            f"{BASE_URL}/"
            "market-analysis"
        ),
        json={
            "request": {
                "question": (
                    "Analyze BTC and ETH."
                ),
                "symbols": [
                    "BTCUSDT",
                    "ETHUSDT",
                ],
            },
            "tickers": [
                {
                    "symbol": "BTCUSDT",
                    "last_price": 100.0,
                    (
                        "price_change_"
                        "percent_24h"
                    ): 3.0,
                    "turnover_24h": 5000,
                },
                {
                    "symbol": "ETHUSDT",
                    "last_price": 50.0,
                    (
                        "price_change_"
                        "percent_24h"
                    ): -1.0,
                    "turnover_24h": 3000,
                },
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "SUCCESS"
    assert (
        data["metadata"]
        ["analysis_type"]
        == "MARKET"
    )
    assert (
        data["sections"][1]
        ["metrics"]["strongest"]
        ["symbol"]
        == "BTCUSDT"
    )
def test_portfolio_analysis_endpoint(
    authenticated_client,
):
    response = authenticated_client.post(
        (
            f"{BASE_URL}/"
            "portfolio-analysis"
        ),
        json={
            "request": {
                "question": (
                    "Review my portfolio."
                ),
                "portfolio_id": 2,
            },
            "snapshot": (
                _snapshot_payload()
            ),
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "SUCCESS"
    assert (
        data["sections"][1]
        ["metrics"]
        ["position_exposure_percent"]
        == 50.0
    )
    assert (
        data["execution_allowed"]
        is False
    )
def test_risk_explanation_endpoint(
    authenticated_client,
):
    response = authenticated_client.post(
        (
            f"{BASE_URL}/"
            "risk-explanation"
        ),
        json=_risk_payload(),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "SUCCESS"
    assert (
        data["sections"][0]
        ["metrics"]["accepted"]
        is True
    )
    assert (
        data["metadata"]
        ["confidence_score"]
        == 1.0
    )
def test_trade_plan_endpoint_is_advisory_only(
    authenticated_client,
):
    response = authenticated_client.post(
        f"{BASE_URL}/trade-plan",
        json={
            "question": (
                "Create a BTC trade plan."
            ),
            "symbol": "BTCUSDT",
            "side": "BUY",
            (
                "reference_entry_"
                "price"
            ): 100.0,
            (
                "reference_stop_"
                "loss_price"
            ): 95.0,
            (
                "reference_take_"
                "profit_price"
            ): 110.0,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "SUCCESS"
    assert (
        data["trade_plan"]
        ["estimated_risk_reward_ratio"]
        == 2.0
    )
    assert (
        data["trade_plan"]
        ["execution_enabled"]
        is False
    )
    assert (
        data["execution_allowed"]
        is False
    )
def test_arbitrage_explanation_endpoint(
    authenticated_client,
):
    response = authenticated_client.post(
        (
            f"{BASE_URL}/"
            "arbitrage-explanation"
        ),
        json={
            "question": (
                "Explain this opportunity."
            ),
            "opportunity_type": (
                "CROSS_EXCHANGE"
            ),
            "opportunity": {
                (
                    "gross_spread_"
                    "percent"
                ): 2.0,
                "net_profit": 5.0,
                (
                    "net_profit_"
                    "percent"
                ): 1.2,
                "estimated_fees": 1.0,
            },
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "SUCCESS"
    assert (
        data["sections"][0]
        ["metrics"]
        ["net_profit_percent"]
        == 1.2
    )
    assert (
        data["metadata"]
        ["analysis_type"]
        == "ARBITRAGE"
    )
def test_invalid_trade_plan_is_rejected(
    authenticated_client,
):
    response = authenticated_client.post(
        f"{BASE_URL}/trade-plan",
        json={
            "question": (
                "Create an invalid plan."
            ),
            "symbol": "BTCUSDT",
            "side": "BUY",
            (
                "reference_entry_"
                "price"
            ): 100.0,
            (
                "reference_stop_"
                "loss_price"
            ): 105.0,
            (
                "reference_take_"
                "profit_price"
            ): 110.0,
        },
    )
    assert response.status_code == 422
def test_portfolio_snapshot_from_another_user_is_rejected(
    authenticated_client,
):
    snapshot = _snapshot_payload()
    snapshot["user_id"] = 100
    response = authenticated_client.post(
        (
            f"{BASE_URL}/"
            "portfolio-analysis"
        ),
        json={
            "request": {
                "question": (
                    "Review this portfolio."
                ),
                "portfolio_id": 2,
            },
            "snapshot": snapshot,
        },
    )
    assert response.status_code == 403
    payload = response.json()
    assert payload["success"] is False
    assert (
        payload["message"]
        == (
            "Portfolio snapshot does not "
            "belong to the current user"
        )
    )
