from types import (
    SimpleNamespace,
)
from unittest.mock import (
    MagicMock,
)
import pytest
from fastapi import (
    HTTPException,
    WebSocketException,
)
from app.api import (
    dependencies,
    websocket_dependencies,
)
def test_http_rejects_malformed_subject(
    monkeypatch,
):
    monkeypatch.setattr(
        dependencies,
        "verify_access_token",
        lambda token: "not-a-user-id",
    )
    repository_class = MagicMock()
    monkeypatch.setattr(
        dependencies,
        "UserRepository",
        repository_class,
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        dependencies.get_current_user(
            token="token",
            db=MagicMock(),
        )
    assert error.value.status_code == 401
    assert (
        error.value.detail
        == "Invalid token subject"
    )
    repository_class.assert_not_called()
def test_http_rejects_non_positive_subject(
    monkeypatch,
):
    monkeypatch.setattr(
        dependencies,
        "verify_access_token",
        lambda token: "0",
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        dependencies.get_current_user(
            token="token",
            db=MagicMock(),
        )
    assert error.value.status_code == 401
    assert (
        error.value.detail
        == "Invalid token subject"
    )
def test_http_returns_active_user(
    monkeypatch,
):
    user = SimpleNamespace(
        id=7,
        is_active=True,
    )
    repository = MagicMock()
    repository.get_by_id.return_value = (
        user
    )
    monkeypatch.setattr(
        dependencies,
        "verify_access_token",
        lambda token: "7",
    )
    monkeypatch.setattr(
        dependencies,
        "UserRepository",
        lambda db: repository,
    )
    result = dependencies.get_current_user(
        token="token",
        db=MagicMock(),
    )
    assert result is user
    repository.get_by_id.assert_called_once_with(
        7
    )
def test_websocket_rejects_non_positive_subject(
    monkeypatch,
):
    websocket = SimpleNamespace(
        headers={
            "authorization": (
                "Bearer websocket-token"
            ),
        },
        query_params={},
    )
    monkeypatch.setattr(
        websocket_dependencies,
        "verify_access_token",
        lambda token: "-2",
    )
    repository_class = MagicMock()
    monkeypatch.setattr(
        websocket_dependencies,
        "UserRepository",
        repository_class,
    )
    with pytest.raises(
        WebSocketException,
    ) as error:
        (
            websocket_dependencies
            .get_current_websocket_user(
                websocket=websocket,
                db=MagicMock(),
            )
        )
    assert error.value.code == 4401
    assert (
        error.value.reason
        == "Invalid token subject"
    )
    repository_class.assert_not_called()
