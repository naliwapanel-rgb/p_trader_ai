from types import (
    SimpleNamespace,
)

from fastapi import (
    FastAPI,
)
from fastapi.testclient import (
    TestClient,
)

from app.api.v1.endpoints import (
    health as health_endpoint,
)


class FakeRuntime:
    def __init__(
        self,
        *,
        healthy: bool,
    ) -> None:
        self._healthy = healthy

    def health(self):
        return SimpleNamespace(
            healthy=self._healthy
        )


def build_app(
    monkeypatch,
    *,
    database_ready: bool = True,
    automation_enabled: bool = True,
    runtime=...,
    metrics_enabled: bool = True,
) -> FastAPI:
    monkeypatch.setattr(
        health_endpoint,
        "settings",
        SimpleNamespace(
            environment="testing",
            app_version="1.0.0",
            automation_runtime_enabled=(
                automation_enabled
            ),
            metrics_enabled=metrics_enabled,
        ),
    )
    monkeypatch.setattr(
        health_endpoint,
        "database_is_ready",
        lambda: database_ready,
    )

    app = FastAPI()

    if runtime is ...:
        runtime = FakeRuntime(
            healthy=True
        )

    if runtime is not None:
        app.state.automation_runtime = (
            runtime
        )

    app.include_router(
        health_endpoint.router,
        prefix="/api/v1",
    )
    return app


def test_existing_health_endpoint_remains_compatible(
    monkeypatch,
):
    client = TestClient(
        build_app(monkeypatch)
    )

    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "environment": "testing",
        "version": "1.0.0",
    }


def test_liveness_does_not_depend_on_database(
    monkeypatch,
):
    client = TestClient(
        build_app(
            monkeypatch,
            database_ready=False,
        )
    )

    response = client.get(
        "/api/v1/live"
    )

    assert response.status_code == 200
    assert response.json()["status"] == (
        "alive"
    )


def test_readiness_reports_healthy_components(
    monkeypatch,
):
    client = TestClient(
        build_app(monkeypatch)
    )

    response = client.get(
        "/api/v1/ready"
    )

    assert response.status_code == 200
    assert response.json()[
        "status"
    ] == "ready"
    assert response.json()[
        "components"
    ] == {
        "database": "healthy",
        "automation": "healthy",
    }


def test_readiness_fails_when_database_is_unavailable(
    monkeypatch,
):
    client = TestClient(
        build_app(
            monkeypatch,
            database_ready=False,
        )
    )

    response = client.get(
        "/api/v1/ready"
    )

    assert response.status_code == 503
    assert response.json()[
        "status"
    ] == "not_ready"
    assert response.json()[
        "components"
    ]["database"] == "unhealthy"


def test_readiness_fails_when_runtime_is_missing(
    monkeypatch,
):
    client = TestClient(
        build_app(
            monkeypatch,
            runtime=None,
        )
    )

    response = client.get(
        "/api/v1/ready"
    )

    assert response.status_code == 503
    assert response.json()[
        "components"
    ]["automation"] == "unavailable"


def test_disabled_runtime_is_ready(
    monkeypatch,
):
    client = TestClient(
        build_app(
            monkeypatch,
            automation_enabled=False,
            runtime=None,
        )
    )

    response = client.get(
        "/api/v1/ready"
    )

    assert response.status_code == 200
    assert response.json()[
        "components"
    ]["automation"] == "disabled"


def test_unhealthy_runtime_makes_application_not_ready(
    monkeypatch,
):
    client = TestClient(
        build_app(
            monkeypatch,
            runtime=FakeRuntime(
                healthy=False
            ),
        )
    )

    response = client.get(
        "/api/v1/ready"
    )

    assert response.status_code == 503
    assert response.json()[
        "components"
    ]["automation"] == "unhealthy"


def test_metrics_endpoint_is_hidden_when_disabled(
    monkeypatch,
):
    client = TestClient(
        build_app(
            monkeypatch,
            metrics_enabled=False,
        )
    )

    response = client.get(
        "/api/v1/metrics"
    )

    assert response.status_code == 404


def test_metrics_endpoint_returns_prometheus_format(
    monkeypatch,
):
    client = TestClient(
        build_app(
            monkeypatch,
            metrics_enabled=True,
        )
    )

    ready_response = client.get(
        "/api/v1/ready"
    )
    metrics_response = client.get(
        "/api/v1/metrics"
    )

    assert ready_response.status_code == 200
    assert metrics_response.status_code == 200
    assert (
        "text/plain"
        in metrics_response.headers[
            "content-type"
        ]
    )
    assert (
        "p_trader_ai_readiness_component"
        in metrics_response.text
    )
    assert (
        'component="database"'
        in metrics_response.text
    )
