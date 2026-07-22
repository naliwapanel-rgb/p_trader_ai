import json
import logging
from types import (
    SimpleNamespace,
)
import pytest
from fastapi import (
    HTTPException,
)
from starlette.requests import (
    Request,
)
from app.core.exceptions import (
    _make_json_safe,
    general_exception_handler,
    http_exception_handler,
    sanitize_validation_errors,
    validation_exception_handler,
)
def build_request():
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/secure",
        "raw_path": b"/secure",
        "query_string": b"",
        "headers": [],
        "client": (
            "127.0.0.1",
            5000,
        ),
        "server": (
            "testserver",
            80,
        ),
    }
    request = Request(scope)
    request.state.request_id = (
        "request-456"
    )
    return request
def response_json(response):
    return json.loads(
        response.body.decode(
            "utf-8"
        )
    )
@pytest.mark.asyncio
async def test_http_exception_detail_is_redacted():
    response = await (
        http_exception_handler(
            build_request(),
            HTTPException(
                status_code=400,
                detail=(
                    "api_key=top-secret"
                ),
                headers={
                    "X-Security-Test": "yes",
                },
            ),
        )
    )
    body_text = response.body.decode(
        "utf-8"
    )
    assert response.status_code == 400
    assert "top-secret" not in body_text
    assert "REDACTED" in body_text
    assert (
        response.headers[
            "x-security-test"
        ]
        == "yes"
    )
    assert (
        response.headers[
            "x-request-id"
        ]
        == "request-456"
    )
def test_sensitive_validation_input_is_redacted():
    errors = [
        {
            "type": "string_too_short",
            "loc": (
                "body",
                "password",
            ),
            "msg": (
                "String should have "
                "at least 8 characters"
            ),
            "input": "short-secret",
        }
    ]
    result = (
        sanitize_validation_errors(
            errors
        )
    )
    assert (
        result[0]["input"]
        == "REDACTED"
    )
    assert (
        "short-secret"
        not in str(result)
    )
def test_normal_validation_input_is_preserved():
    errors = [
        {
            "type": "value_error",
            "loc": (
                "body",
                "symbol",
            ),
            "msg": "Invalid symbol",
            "input": "BADPAIR",
        }
    ]
    result = (
        sanitize_validation_errors(
            errors
        )
    )
    assert (
        result[0]["input"]
        == "BADPAIR"
    )
@pytest.mark.asyncio
async def test_validation_handler_sanitizes_context():
    exception = SimpleNamespace(
        errors=lambda: [
            {
                "type": "value_error",
                "loc": (
                    "body",
                    "api_secret",
                ),
                "msg": (
                    "Invalid api_secret"
                ),
                "input": "secret-value",
                "ctx": {
                    "error": RuntimeError(
                        "token=hidden-token"
                    ),
                },
            }
        ]
    )
    response = await (
        validation_exception_handler(
            build_request(),
            exception,
        )
    )
    body_text = response.body.decode(
        "utf-8"
    )
    assert response.status_code == 422
    assert "secret-value" not in body_text
    assert "hidden-token" not in body_text
    assert "REDACTED" in body_text
@pytest.mark.asyncio
async def test_general_exception_is_generic(
    caplog,
):
    caplog.set_level(
        logging.ERROR,
        logger="app.exceptions",
    )
    response = await (
        general_exception_handler(
            build_request(),
            RuntimeError(
                "password=hidden-password"
            ),
        )
    )
    body = response_json(
        response
    )
    assert response.status_code == 500
    assert (
        body["message"]
        == "Internal server error"
    )
    logs = "\n".join(
        record.getMessage()
        for record in caplog.records
        if (
            record.name
            == "app.exceptions"
        )
    )
    assert (
        "exception_type=RuntimeError"
        in logs
    )
    assert "hidden-password" not in logs
def test_make_json_safe_redacts_exception():
    result = _make_json_safe({
        "error": RuntimeError(
            "access_token=hidden-token"
        ),
    })
    assert "hidden-token" not in (
        str(result)
    )
    assert "REDACTED" in (
        str(result)
    )
