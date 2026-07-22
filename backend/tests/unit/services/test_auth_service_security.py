from types import (
    SimpleNamespace,
)
from unittest.mock import (
    MagicMock,
)
import pytest
from fastapi import (
    HTTPException,
)
from app.schemas.auth import (
    UserLoginRequest,
)
from app.services import (
    auth_service as module,
)
from app.services.auth_service import (
    AuthService,
)
def login_request():
    return UserLoginRequest(
        email="user@example.com",
        password="Password123",
    )
def test_inactive_user_cannot_login(
    monkeypatch,
):
    service = AuthService(
        MagicMock()
    )
    service.user_repository = (
        MagicMock()
    )
    service.user_repository.get_by_email.return_value = (
        SimpleNamespace(
            id=7,
            hashed_password="hash",
            is_active=False,
        )
    )
    monkeypatch.setattr(
        module,
        "verify_password",
        lambda plain, hashed: True,
    )
    create_token = MagicMock()
    monkeypatch.setattr(
        module,
        "create_access_token",
        create_token,
    )
    with pytest.raises(
        HTTPException,
    ) as error:
        service.login_user(
            login_request()
        )
    assert error.value.status_code == 403
    assert error.value.detail == (
        "Inactive user"
    )
    create_token.assert_not_called()
def test_active_user_receives_token(
    monkeypatch,
):
    service = AuthService(
        MagicMock()
    )
    service.user_repository = (
        MagicMock()
    )
    service.user_repository.get_by_email.return_value = (
        SimpleNamespace(
            id=7,
            hashed_password="hash",
            is_active=True,
        )
    )
    monkeypatch.setattr(
        module,
        "verify_password",
        lambda plain, hashed: True,
    )
    monkeypatch.setattr(
        module,
        "create_access_token",
        lambda subject: "signed-token",
    )
    result = service.login_user(
        login_request()
    )
    assert result.access_token == (
        "signed-token"
    )
