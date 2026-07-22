import pytest
from cryptography.fernet import (
    Fernet,
)
from app.core.config import (
    Settings,
)
from app.core.security.runtime import (
    validate_runtime_security,
)
def build_settings(
    **overrides,
) -> Settings:
    fields = {
        "environment": "development",
        "debug": True,
        "secret_key": "s" * 64,
        "encryption_key": (
            Fernet.generate_key()
            .decode()
        ),
        "algorithm": "HS256",
        (
            "access_token_"
            "expire_minutes"
        ): 60,
        "backend_cors_origins": [
            "http://localhost",
        ],
    }
    fields.update(overrides)
    return Settings(
        _env_file=None,
        **fields,
    )
def test_development_security_is_valid():
    settings = build_settings()
    validate_runtime_security(
        settings
    )
def test_blank_secret_is_rejected():
    settings = build_settings(
        secret_key="  ",
    )
    with pytest.raises(
        RuntimeError,
        match="SECRET_KEY cannot be blank",
    ):
        validate_runtime_security(
            settings
        )
def test_invalid_fernet_key_is_rejected():
    settings = build_settings(
        encryption_key=(
            "not-a-fernet-key"
        ),
    )
    with pytest.raises(
        RuntimeError,
        match="valid Fernet key",
    ):
        validate_runtime_security(
            settings
        )
def test_unsupported_algorithm_is_rejected():
    settings = build_settings(
        algorithm="none",
    )
    with pytest.raises(
        RuntimeError,
        match="not supported",
    ):
        validate_runtime_security(
            settings
        )
def test_production_debug_is_rejected():
    settings = build_settings(
        environment="production",
        debug=True,
    )
    with pytest.raises(
        RuntimeError,
        match="DEBUG must be disabled",
    ):
        validate_runtime_security(
            settings
        )
def test_production_default_secret_is_rejected():
    settings = build_settings(
        environment="production",
        debug=False,
        secret_key=(
            "CHANGE_ME_IN_PRODUCTION"
        ),
    )
    with pytest.raises(
        RuntimeError,
        match="SECRET_KEY is insecure",
    ):
        validate_runtime_security(
            settings
        )
def test_production_wildcard_cors_is_rejected():
    settings = build_settings(
        environment="production",
        debug=False,
        backend_cors_origins=["*"],
    )
    with pytest.raises(
        RuntimeError,
        match="Wildcard CORS",
    ):
        validate_runtime_security(
            settings
        )
