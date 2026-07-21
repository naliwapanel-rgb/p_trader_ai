from types import (
    SimpleNamespace,
)
import pytest
from fastapi import (
    HTTPException,
)
from fastapi.testclient import (
    TestClient,
)
from app.api.dependencies import (
    get_current_user,
)
from app.api.v1.endpoints.ai_context import (
    get_ai_context_builder_service,
)
from app.main import app
from app.schemas.ai_context import (
    AIUserContextResponse,
)
from app.schemas.risk_management import (
    RiskConfiguration,
)
BASE_URL = "/api/v1/ai-assistant/context"
def _context_response():
    return AIUserContextResponse(
        user_id=99,
        generated_at_ms=123456789,
        portfolios=[],
        selected_portfolio=None,
        latest_portfolio_snapshot=None,
        watchlist=[],
        alerts=[],
        exchange_accounts=[],
        selected_exchange_account=None,
        notification_preferences=None,
        risk_configuration=(
            RiskConfiguration()
        ),
        automation=None,
        data_sources=[
            "RISK_ENGINE",
        ],
        portfolio_count=0,
        watchlist_count=0,
        alert_count=0,
        exchange_account_count=0,
        advisory_only=True,
        execution_enabled=False,
    )
class FakeContextService:
    def __init__(self):
        self.calls = []
    def build(
        self,
        *,
        current_user,
        request,
    ):
        self.calls.append(
            (
                current_user,
                request,
            )
        )
        return _context_response()
@pytest.fixture
def authenticated_client():
    service = FakeContextService()
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=99,
        is_active=True,
    )
    app.dependency_overrides[
        get_ai_context_builder_service
    ] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.clear()
def test_context_route_requires_authentication():
    service = FakeContextService()
    app.dependency_overrides[
        get_ai_context_builder_service
    ] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get(
                BASE_URL
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401
    assert service.calls == []
def test_context_endpoint_returns_safe_context(
    authenticated_client,
):
    client, service = (
        authenticated_client
    )
    response = client.get(
        BASE_URL,
        params={
            "portfolio_id": 10,
            "exchange_account_id": 40,
            "include_automation": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert (
        payload["data"]["user_id"]
        == 99
    )
    assert (
        payload["data"]
        ["advisory_only"]
        is True
    )
    assert (
        payload["data"]
        ["execution_enabled"]
        is False
    )
    request = service.calls[0][1]
    assert request.portfolio_id == 10
    assert request.exchange_account_id == 40
    assert request.include_automation is False
def test_context_endpoint_rejects_invalid_ids(
    authenticated_client,
):
    client, service = (
        authenticated_client
    )
    response = client.get(
        BASE_URL,
        params={
            "portfolio_id": 0,
        },
    )
    assert response.status_code == 422
    assert service.calls == []
def test_context_service_error_is_preserved():
    class MissingPortfolioService:
        def build(
            self,
            *,
            current_user,
            request,
        ):
            raise HTTPException(
                status_code=404,
                detail="Portfolio not found",
            )
    app.dependency_overrides[
        get_current_user
    ] = lambda: SimpleNamespace(
        id=99,
        is_active=True,
    )
    app.dependency_overrides[
        get_ai_context_builder_service
    ] = lambda: MissingPortfolioService()
    try:
        with TestClient(app) as client:
            response = client.get(
                BASE_URL,
                params={
                    "portfolio_id": 10,
                },
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert (
        payload["message"]
        == "Portfolio not found"
    )
