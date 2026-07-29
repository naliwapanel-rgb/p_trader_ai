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
def hardened_settings(
    **overrides: object,
) -> Settings:
    values = {
        "environment": "production",
        "debug": False,
        "database_url": (
            "postgresql+psycopg2://"
            "user:password@database:5432/"
            "p_trader_ai"
        ),
        "secret_key": "s" * 64,
        "encryption_key": (
            Fernet.generate_key()
            .decode("utf-8")
        ),
        "backend_cors_origins": [
            "https://app.example.com",
        ],
        "trusted_hosts": ["api.example.com"],
        "security_headers_enabled": True,
        "api_docs_enabled": False,
    }
    values.update(overrides)
    return Settings(
        _env_file=None,
        **values,
    )
def test_database_pool_defaults(
) -> None:
    settings = Settings(
        _env_file=None,
    )
    assert settings.database_pool_size == 5
    assert settings.database_max_overflow == 10
    assert (
        settings.database_pool_timeout_seconds
        == 30.0
    )
    assert (
        settings.database_pool_recycle_seconds
        == 1800
    )
def test_secure_postgresql_production_is_valid(
) -> None:
    validate_runtime_security(
        hardened_settings()
    )
def test_production_rejects_sqlite(
) -> None:
    settings = hardened_settings(
        database_url=(
            "sqlite:///./production.db"
        ),
    )
    with pytest.raises(
        RuntimeError,
        match="require PostgreSQL",
    ):
        validate_runtime_security(
            settings
        )
def test_staging_rejects_sqlite(
) -> None:
    settings = hardened_settings(
        environment="staging",
        database_url=(
            "sqlite:///./staging.db"
        ),
    )
    with pytest.raises(
        RuntimeError,
        match="require PostgreSQL",
    ):
        validate_runtime_security(
            settings
        )
