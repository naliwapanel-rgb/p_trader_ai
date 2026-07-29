from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware,
)


def build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "api.example.com",
            "testserver",
        ],
        www_redirect=False,
    )

    @app.get("/safe")
    async def safe():
        return {"ok": True}

    return app


def test_trusted_host_is_allowed():
    client = TestClient(build_app())

    response = client.get(
        "/safe",
        headers={
            "Host": "api.example.com",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
    }


def test_untrusted_host_is_rejected():
    client = TestClient(build_app())

    response = client.get(
        "/safe",
        headers={
            "Host": "attacker.example.net",
        },
    )

    assert response.status_code == 400
    assert response.text == (
        "Invalid host header"
    )


def test_wildcard_subdomain_is_not_implicitly_allowed():
    client = TestClient(build_app())

    response = client.get(
        "/safe",
        headers={
            "Host": "other.api.example.com",
        },
    )

    assert response.status_code == 400
