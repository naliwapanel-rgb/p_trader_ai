from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_headers import (
    SECURITY_HEADERS,
    security_headers_middleware,
)


def build_app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(
        security_headers_middleware
    )

    @app.get("/safe")
    async def safe():
        return {"ok": True}

    return app


def test_security_headers_are_returned():
    client = TestClient(build_app())

    response = client.get("/safe")

    assert response.status_code == 200

    for name, value in SECURITY_HEADERS.items():
        assert response.headers[name] == value


def test_hsts_is_one_year_with_subdomains():
    client = TestClient(build_app())

    response = client.get("/safe")

    assert (
        response.headers[
            "Strict-Transport-Security"
        ]
        == (
            "max-age=31536000; "
            "includeSubDomains"
        )
    )


def test_clickjacking_and_mime_sniffing_are_blocked():
    client = TestClient(build_app())

    response = client.get("/safe")

    assert response.headers[
        "X-Frame-Options"
    ] == "DENY"
    assert response.headers[
        "X-Content-Type-Options"
    ] == "nosniff"


def test_content_security_policy_is_restrictive():
    client = TestClient(build_app())

    response = client.get("/safe")
    policy = response.headers[
        "Content-Security-Policy"
    ]

    assert "default-src 'none'" in policy
    assert "frame-ancestors 'none'" in policy
    assert "form-action 'none'" in policy
