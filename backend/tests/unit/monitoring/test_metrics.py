from fastapi import (
    FastAPI,
)
from fastapi.testclient import (
    TestClient,
)

from app.monitoring.metrics import (
    metrics_middleware,
    metrics_response,
)


def build_app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(
        metrics_middleware
    )

    @app.get(
        "/phase13g/items/{item_id}"
    )
    async def item(
        item_id: int,
    ):
        return {
            "item_id": item_id
        }

    @app.get("/phase13g/metrics")
    async def metrics():
        return metrics_response()

    return app


def test_request_metrics_use_route_template():
    client = TestClient(build_app())

    response = client.get(
        "/phase13g/items/12345"
    )
    metrics = client.get(
        "/phase13g/metrics"
    )

    assert response.status_code == 200
    assert metrics.status_code == 200
    assert (
        'route="/phase13g/items/{item_id}"'
        in metrics.text
    )
    assert (
        'route="/phase13g/items/12345"'
        not in metrics.text
    )


def test_request_duration_and_in_progress_metrics_exist():
    client = TestClient(build_app())

    client.get(
        "/phase13g/items/1"
    )
    metrics = client.get(
        "/phase13g/metrics"
    )

    assert (
        "p_trader_ai_http_request_"
        "duration_seconds"
        in metrics.text
    )
    assert (
        "p_trader_ai_http_requests_"
        "in_progress"
        in metrics.text
    )
