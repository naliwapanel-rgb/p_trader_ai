import logging
import re
from fastapi import (
    FastAPI,
)
from fastapi.testclient import (
    TestClient,
)
from app.middleware.request_logger import (
    request_logger_middleware,
)
def build_app():
    app = FastAPI()
    app.middleware("http")(
        request_logger_middleware
    )
    @app.get("/safe")
    async def safe():
        return {
            "ok": True,
        }
    @app.get("/failure")
    async def failure():
        raise RuntimeError(
            "api_key=hidden-key"
        )
    return app
def request_log_messages(
    caplog,
) -> str:
    return "\n".join(
        record.getMessage()
        for record in caplog.records
        if record.name == "app.request"
    )
def test_logger_returns_request_id(
    caplog,
):
    caplog.set_level(
        logging.INFO,
        logger="app.request",
    )
    client = TestClient(
        build_app()
    )
    response = client.get(
        "/safe",
        headers={
            "X-Request-ID": (
                "request-123"
            ),
        },
    )
    assert response.status_code == 200
    assert (
        response.headers["X-Request-ID"]
        == "request-123"
    )
    logs = request_log_messages(
        caplog
    )
    assert (
        "request_id=request-123"
        in logs
    )
def test_logger_redacts_query_credentials(
    caplog,
):
    caplog.set_level(
        logging.INFO,
        logger="app.request",
    )
    client = TestClient(
        build_app()
    )
    response = client.get(
        (
            "/safe?"
            "symbol=BTCUSDT"
            "&api_key=top-secret"
        )
    )
    assert response.status_code == 200
    logs = request_log_messages(
        caplog
    )
    assert "BTCUSDT" in logs
    assert "top-secret" not in logs
    assert (
        "api_key=REDACTED"
        in logs
    )
def test_logger_never_logs_authorization_header(
    caplog,
):
    caplog.set_level(
        logging.INFO,
        logger="app.request",
    )
    client = TestClient(
        build_app()
    )
    response = client.get(
        "/safe",
        headers={
            "Authorization": (
                "Bearer header-secret"
            ),
        },
    )
    assert response.status_code == 200
    logs = request_log_messages(
        caplog
    )
    assert "header-secret" not in logs
    assert "Authorization" not in logs
def test_failure_log_exposes_type_not_message(
    caplog,
):
    caplog.set_level(
        logging.ERROR,
        logger="app.request",
    )
    client = TestClient(
        build_app(),
        raise_server_exceptions=False,
    )
    response = client.get(
        "/failure"
    )
    assert response.status_code == 500
    logs = request_log_messages(
        caplog
    )
    assert (
        "exception_type=RuntimeError"
        in logs
    )
    assert "hidden-key" not in logs
