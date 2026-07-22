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
import pytest
from fastapi import (
    FastAPI,
)
from fastapi.testclient import (
    TestClient,
)
from app.api.dependencies import (
    get_current_user,
)
from app.api.v1.endpoints import (
    copy_trading,
    strategy_templates,
)
from app.database.session import (
    get_db,
)
from app.main import (
    app as main_app,
)
NOW = datetime(
    2026,
    7,
    22,
    17,
    0,
    tzinfo=UTC,
)
def build_template(
    *,
    status="DRAFT",
    visibility="PRIVATE",
):
    return SimpleNamespace(
        id=10,
        user_id=7,
        name="Momentum Template",
        description="Reusable template",
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        visibility=visibility,
        status=status,
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1.0,
        max_position_value_usd=25.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        stop_loss_percent=None,
        take_profit_percent=None,
        strategy_config={
            "buy_change_percent_24h": 1.0,
            "sell_change_percent_24h": -1.0,
            "maximum_spread_percent": 0.5,
            "minimum_turnover_24h": 0.0,
            "confidence_scale_percent": 5.0,
        },
        version=1,
        published_at=(
            NOW
            if status == "PUBLISHED"
            else None
        ),
        created_at=NOW,
        updated_at=NOW,
    )
def build_bot():
    return SimpleNamespace(
        id=30,
        user_id=7,
        exchange_account_id=None,
        name="Copied Bot",
        description="Reusable template",
        strategy_type="RULE_BASED",
        symbol="BTCUSDT",
        category="linear",
        timeframe="5m",
        status="DRAFT",
        paper_trading=True,
        dry_run=True,
        risk_per_trade_percent=1.0,
        max_position_value_usd=25.0,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        stop_loss_percent=None,
        take_profit_percent=None,
        strategy_config={
            "buy_change_percent_24h": 1.0,
            "sell_change_percent_24h": -1.0,
            "maximum_spread_percent": 0.5,
            "minimum_turnover_24h": 0.0,
            "confidence_scale_percent": 5.0,
        },
        last_error=None,
        started_at=None,
        stopped_at=None,
        last_run_at=None,
        created_at=NOW,
        updated_at=NOW,
    )
def build_subscription(
    *,
    status="ACTIVE",
):
    return SimpleNamespace(
        id=40,
        follower_user_id=7,
        source_template_id=10,
        follower_bot_id=30,
        status=status,
        execution_mode="PAPER_ONLY",
        subscribed_template_version=1,
        last_error=None,
        last_mirrored_at=None,
        created_at=NOW,
        updated_at=NOW,
    )
def build_test_app(
    *,
    authenticated=True,
):
    app = FastAPI()
    app.include_router(
        strategy_templates.router
    )
    app.include_router(
        copy_trading.router
    )
    app.dependency_overrides[
        get_db
    ] = lambda: MagicMock()
    if authenticated:
        app.dependency_overrides[
            get_current_user
        ] = lambda: SimpleNamespace(
            id=7
        )
    return app
def install_services(
    monkeypatch,
    *,
    template_service=None,
    subscription_service=None,
):
    template_service = (
        template_service
        or MagicMock()
    )
    subscription_service = (
        subscription_service
        or MagicMock()
    )
    monkeypatch.setattr(
        strategy_templates,
        "StrategyTemplateService",
        lambda db: template_service,
    )
    monkeypatch.setattr(
        copy_trading,
        "CopyTradingSubscriptionService",
        lambda db: subscription_service,
    )
    return (
        template_service,
        subscription_service,
    )
def test_routes_require_authentication():
    client = TestClient(
        build_test_app(
            authenticated=False
        )
    )
    responses = [
        client.get(
            "/strategy-templates"
        ),
        client.get(
            "/strategy-templates/public"
        ),
        client.get(
            "/copy-trading/subscriptions"
        ),
    ]
    assert all(
        response.status_code == 401
        for response in responses
    )
def test_list_owned_templates(
    monkeypatch,
):
    service, _ = install_services(
        monkeypatch
    )
    service.list_templates.return_value = [
        build_template()
    ]
    client = TestClient(
        build_test_app()
    )
    response = client.get(
        "/strategy-templates",
        params={
            "status": "DRAFT",
            "visibility": "PRIVATE",
            "limit": 20,
            "offset": 5,
        },
    )
    assert response.status_code == 200
    assert (
        response.json()["data"][0]["id"]
        == 10
    )
    service.list_templates.assert_called_once()
    kwargs = (
        service.list_templates
        .call_args
        .kwargs
    )
    assert kwargs["current_user"].id == 7
    assert kwargs["template_status"] == (
        "DRAFT"
    )
    assert kwargs["visibility"] == (
        "PRIVATE"
    )
    assert kwargs["limit"] == 20
    assert kwargs["offset"] == 5
def test_list_public_templates(
    monkeypatch,
):
    service, _ = install_services(
        monkeypatch
    )
    service.list_public_templates.return_value = [
        build_template(
            status="PUBLISHED",
            visibility="PUBLIC",
        )
    ]
    client = TestClient(
        build_test_app()
    )
    response = client.get(
        "/strategy-templates/public"
    )
    assert response.status_code == 200
    assert (
        response.json()
        ["data"][0]["status"]
        == "PUBLISHED"
    )
def test_create_template(
    monkeypatch,
):
    service, _ = install_services(
        monkeypatch
    )
    service.create_template.return_value = (
        build_template()
    )
    client = TestClient(
        build_test_app()
    )
    response = client.post(
        "/strategy-templates",
        json={
            "name": "Momentum Template",
            "strategy_type": "RULE_BASED",
            "symbol": "BTCUSDT",
            "strategy_config": {},
        },
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["name"]
        == "Momentum Template"
    )
    service.create_template.assert_called_once()
def test_get_template(
    monkeypatch,
):
    service, _ = install_services(
        monkeypatch
    )
    service.get_template.return_value = (
        build_template()
    )
    client = TestClient(
        build_test_app()
    )
    response = client.get(
        "/strategy-templates/10"
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["id"]
        == 10
    )
def test_update_template(
    monkeypatch,
):
    service, _ = install_services(
        monkeypatch
    )
    updated = build_template()
    updated.name = "Updated Template"
    service.update_template.return_value = (
        updated
    )
    client = TestClient(
        build_test_app()
    )
    response = client.put(
        "/strategy-templates/10",
        json={
            "name": "Updated Template",
        },
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["name"]
        == "Updated Template"
    )
def test_publish_template(
    monkeypatch,
):
    service, _ = install_services(
        monkeypatch
    )
    service.get_template.return_value = (
        build_template()
    )
    service.publish_template.return_value = (
        build_template(
            status="PUBLISHED",
            visibility="PUBLIC",
        )
    )
    client = TestClient(
        build_test_app()
    )
    response = client.post(
        "/strategy-templates/10/publish"
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["action"] == "PUBLISH"
    assert data["previous_status"] == (
        "DRAFT"
    )
    assert data["status"] == "PUBLISHED"
    assert data["changed"] is True
def test_create_bot_from_template(
    monkeypatch,
):
    service, _ = install_services(
        monkeypatch
    )
    service.create_bot_from_template.return_value = (
        build_bot()
    )
    client = TestClient(
        build_test_app()
    )
    response = client.post(
        "/strategy-templates/10/create-bot",
        json={
            "name": "Copied Bot",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Copied Bot"
    assert data["paper_trading"] is True
    assert data["dry_run"] is True
def test_delete_template(
    monkeypatch,
):
    service, _ = install_services(
        monkeypatch
    )
    client = TestClient(
        build_test_app()
    )
    response = client.delete(
        "/strategy-templates/10"
    )
    assert response.status_code == 200
    service.delete_template.assert_called_once()
def test_list_subscriptions(
    monkeypatch,
):
    _, service = install_services(
        monkeypatch
    )
    service.list_subscriptions.return_value = [
        build_subscription()
    ]
    client = TestClient(
        build_test_app()
    )
    response = client.get(
        "/copy-trading/subscriptions",
        params={
            "status": "ACTIVE",
        },
    )
    assert response.status_code == 200
    assert (
        response.json()
        ["data"][0]["execution_mode"]
        == "PAPER_ONLY"
    )
def test_create_subscription(
    monkeypatch,
):
    _, service = install_services(
        monkeypatch
    )
    service.create_subscription.return_value = (
        build_subscription()
    )
    client = TestClient(
        build_test_app()
    )
    response = client.post(
        "/copy-trading/subscriptions",
        json={
            "source_template_id": 10,
            "follower_bot_id": 30,
        },
    )
    assert response.status_code == 200
    assert (
        response.json()
        ["data"]["follower_bot_id"]
        == 30
    )
def test_get_subscription(
    monkeypatch,
):
    _, service = install_services(
        monkeypatch
    )
    service.get_subscription.return_value = (
        build_subscription()
    )
    client = TestClient(
        build_test_app()
    )
    response = client.get(
        "/copy-trading/subscriptions/40"
    )
    assert response.status_code == 200
    assert (
        response.json()["data"]["id"]
        == 40
    )
@pytest.mark.parametrize(
    (
        "action",
        "service_method",
        "previous_status",
        "result_status",
    ),
    [
        (
            "pause",
            "pause_subscription",
            "ACTIVE",
            "PAUSED",
        ),
        (
            "resume",
            "resume_subscription",
            "PAUSED",
            "ACTIVE",
        ),
        (
            "stop",
            "stop_subscription",
            "ACTIVE",
            "STOPPED",
        ),
    ],
)
def test_subscription_actions(
    monkeypatch,
    action,
    service_method,
    previous_status,
    result_status,
):
    _, service = install_services(
        monkeypatch
    )
    service.get_subscription.return_value = (
        build_subscription(
            status=previous_status
        )
    )
    getattr(
        service,
        service_method,
    ).return_value = build_subscription(
        status=result_status
    )
    client = TestClient(
        build_test_app()
    )
    response = client.post(
        (
            "/copy-trading/subscriptions/"
            f"40/{action}"
        )
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == result_status
    assert data["changed"] is (
        previous_status
        != result_status
    )
def test_delete_subscription(
    monkeypatch,
):
    _, service = install_services(
        monkeypatch
    )
    client = TestClient(
        build_test_app()
    )
    response = client.delete(
        "/copy-trading/subscriptions/40"
    )
    assert response.status_code == 200
    service.delete_subscription.assert_called_once()
def test_query_validation():
    client = TestClient(
        build_test_app()
    )
    responses = [
        client.get(
            "/strategy-templates",
            params={
                "limit": 0,
            },
        ),
        client.get(
            "/strategy-templates",
            params={
                "status": "RUNNING",
            },
        ),
        client.get(
            "/copy-trading/subscriptions",
            params={
                "status": "UNKNOWN",
            },
        ),
    ]
    assert all(
        response.status_code == 422
        for response in responses
    )
def test_main_openapi_registers_phase_12l_routes():
    paths = main_app.openapi()[
        "paths"
    ]
    required = {
        "/api/v1/strategy-templates": {
            "get",
            "post",
        },
        (
            "/api/v1/"
            "strategy-templates/public"
        ): {
            "get",
        },
        (
            "/api/v1/"
            "strategy-templates/"
            "{template_id}"
        ): {
            "get",
            "put",
            "delete",
        },
        (
            "/api/v1/"
            "strategy-templates/"
            "{template_id}/publish"
        ): {
            "post",
        },
        (
            "/api/v1/"
            "strategy-templates/"
            "{template_id}/create-bot"
        ): {
            "post",
        },
        (
            "/api/v1/"
            "copy-trading/subscriptions"
        ): {
            "get",
            "post",
        },
        (
            "/api/v1/"
            "copy-trading/subscriptions/"
            "{subscription_id}"
        ): {
            "get",
            "delete",
        },
        (
            "/api/v1/"
            "copy-trading/subscriptions/"
            "{subscription_id}/pause"
        ): {
            "post",
        },
        (
            "/api/v1/"
            "copy-trading/subscriptions/"
            "{subscription_id}/resume"
        ): {
            "post",
        },
        (
            "/api/v1/"
            "copy-trading/subscriptions/"
            "{subscription_id}/stop"
        ): {
            "post",
        },
    }
    for route, methods in required.items():
        assert route in paths
        actual = {
            method.lower()
            for method
            in paths[route]
        }
        assert not (
            methods - actual
        )
