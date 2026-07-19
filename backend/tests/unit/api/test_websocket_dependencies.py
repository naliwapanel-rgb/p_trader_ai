from types import SimpleNamespace
from unittest.mock import patch
import pytest
from fastapi import WebSocketException
from app.api.websocket_dependencies import (
    WS_FORBIDDEN,
    WS_UNAUTHORIZED,
    get_current_websocket_user,
    get_websocket_token,
)
class FakeWebSocket:
    def __init__(
        self,
        *,
        authorization: str | None = None,
        token: str | None = None,
    ):
        self.headers = {}
        if authorization is not None:
            self.headers[
                "authorization"
            ] = authorization
        self.query_params = {}
        if token is not None:
            self.query_params["token"] = token
class FakeUserRepository:
    def __init__(self, user):
        self.user = user
        self.requested_user_id = None
    def get_by_id(self, user_id):
        self.requested_user_id = user_id
        return self.user
def test_websocket_token_prefers_bearer_header():
    websocket = FakeWebSocket(
        authorization="Bearer header-token",
        token="query-token",
    )
    assert (
        get_websocket_token(websocket)
        == "header-token"
    )
def test_websocket_token_uses_query_parameter():
    websocket = FakeWebSocket(
        token="query-token"
    )
    assert (
        get_websocket_token(websocket)
        == "query-token"
    )
def test_websocket_token_rejects_missing_token():
    websocket = FakeWebSocket()
    with pytest.raises(
        WebSocketException
    ) as exc_info:
        get_websocket_token(websocket)
    assert (
        exc_info.value.code
        == WS_UNAUTHORIZED
    )
    assert (
        exc_info.value.reason
        == "Not authenticated"
    )
def test_websocket_user_is_authenticated():
    websocket = FakeWebSocket(
        token="valid-token"
    )
    user = SimpleNamespace(
        id=7,
        is_active=True,
    )
    repository = FakeUserRepository(user)
    with (
        patch(
            (
                "app.api.websocket_dependencies."
                "verify_access_token"
            ),
            return_value="7",
        ),
        patch(
            (
                "app.api.websocket_dependencies."
                "UserRepository"
            ),
            return_value=repository,
        ),
    ):
        result = get_current_websocket_user(
            websocket=websocket,
            db=SimpleNamespace(),
        )
    assert result is user
    assert repository.requested_user_id == 7
def test_websocket_user_rejects_bad_token():
    websocket = FakeWebSocket(
        token="invalid-token"
    )
    with patch(
        (
            "app.api.websocket_dependencies."
            "verify_access_token"
        ),
        return_value=None,
    ):
        with pytest.raises(
            WebSocketException
        ) as exc_info:
            get_current_websocket_user(
                websocket=websocket,
                db=SimpleNamespace(),
            )
    assert (
        exc_info.value.code
        == WS_UNAUTHORIZED
    )
    assert (
        exc_info.value.reason
        == "Invalid or expired token"
    )
def test_websocket_user_rejects_missing_user():
    websocket = FakeWebSocket(
        token="valid-token"
    )
    repository = FakeUserRepository(None)
    with (
        patch(
            (
                "app.api.websocket_dependencies."
                "verify_access_token"
            ),
            return_value="7",
        ),
        patch(
            (
                "app.api.websocket_dependencies."
                "UserRepository"
            ),
            return_value=repository,
        ),
    ):
        with pytest.raises(
            WebSocketException
        ) as exc_info:
            get_current_websocket_user(
                websocket=websocket,
                db=SimpleNamespace(),
            )
    assert (
        exc_info.value.code
        == WS_UNAUTHORIZED
    )
    assert exc_info.value.reason == "User not found"
def test_websocket_user_rejects_inactive_user():
    websocket = FakeWebSocket(
        token="valid-token"
    )
    user = SimpleNamespace(
        id=7,
        is_active=False,
    )
    repository = FakeUserRepository(user)
    with (
        patch(
            (
                "app.api.websocket_dependencies."
                "verify_access_token"
            ),
            return_value="7",
        ),
        patch(
            (
                "app.api.websocket_dependencies."
                "UserRepository"
            ),
            return_value=repository,
        ),
    ):
        with pytest.raises(
            WebSocketException
        ) as exc_info:
            get_current_websocket_user(
                websocket=websocket,
                db=SimpleNamespace(),
            )
    assert (
        exc_info.value.code
        == WS_FORBIDDEN
    )
    assert exc_info.value.reason == "Inactive user"
