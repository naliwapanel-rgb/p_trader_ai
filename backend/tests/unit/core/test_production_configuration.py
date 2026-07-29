from pathlib import Path
import pytest
from cryptography.fernet import (
    Fernet,
)
from pydantic import ValidationError
from app.core.config import (
    DEVELOPMENT_ENCRYPTION_KEY,
    DEVELOPMENT_SECRET_KEY,
    Settings,
)
from app.core.security.runtime import (
    validate_runtime_security,
)
def build_hardened_settings(
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
            Fernet
            .generate_key()
            .decode("utf-8")
        ),
        "algorithm": "HS256",
        "trusted_hosts": ["api.example.com"],
        "security_headers_enabled": True,
        "api_docs_enabled": False,
        "metrics_enabled": True,
        "log_json_enabled": True,
        "access_token_expire_minutes": 60,
        "backend_cors_origins": [
            "https://app.example.com",
        ],
    }
    values.update(
        overrides
    )
    return Settings(
        _env_file=None,
        **values,
    )
@pytest.mark.parametrize(
    (
        "provided",
        "expected",
    ),
    [
        ("dev", "development"),
        ("development", "development"),
        ("test", "testing"),
        ("testing", "testing"),
        ("stage", "staging"),
        ("staging", "staging"),
        ("prod", "production"),
        ("production", "production"),
    ],
)
def test_environment_aliases_are_normalized(
    provided: str,
    expected: str,
) -> None:
    settings = Settings(
        _env_file=None,
        environment=provided,
    )
    assert (
        settings.environment
        == expected
    )
def test_unknown_environment_is_rejected(
) -> None:
    with pytest.raises(
        ValidationError,
        match="Unsupported environment",
    ):
        Settings(
            _env_file=None,
            environment="unknown",
        )
def test_development_defaults_are_valid(
) -> None:
    settings = Settings(
        _env_file=None,
    )
    validate_runtime_security(
        settings
    )
    assert (
        settings.secret_key
        == DEVELOPMENT_SECRET_KEY
    )
    assert (
        settings.encryption_key
        == DEVELOPMENT_ENCRYPTION_KEY
    )
def test_secure_production_configuration_is_valid(
) -> None:
    settings = (
        build_hardened_settings()
    )
    validate_runtime_security(
        settings
    )
    assert settings.is_production
    assert (
        settings
        .is_hardened_environment
    )
def test_staging_uses_hardened_validation(
) -> None:
    settings = (
        build_hardened_settings(
            environment="staging",
            debug=True,
        )
    )
    with pytest.raises(
        RuntimeError,
        match="DEBUG must be disabled",
    ):
        validate_runtime_security(
            settings
        )
def test_production_development_secret_is_rejected(
) -> None:
    settings = (
        build_hardened_settings(
            secret_key=(
                DEVELOPMENT_SECRET_KEY
            ),
        )
    )
    with pytest.raises(
        RuntimeError,
        match=(
            "Production SECRET_KEY "
            "is insecure"
        ),
    ):
        validate_runtime_security(
            settings
        )
def test_production_development_encryption_key_is_rejected(
) -> None:
    settings = (
        build_hardened_settings(
            encryption_key=(
                DEVELOPMENT_ENCRYPTION_KEY
            ),
        )
    )
    with pytest.raises(
        RuntimeError,
        match=(
            "Production ENCRYPTION_KEY "
            "is insecure"
        ),
    ):
        validate_runtime_security(
            settings
        )
def test_production_requires_cors_origin(
) -> None:
    settings = (
        build_hardened_settings(
            backend_cors_origins=[],
        )
    )
    with pytest.raises(
        RuntimeError,
        match=(
            "At least one production "
            "CORS origin"
        ),
    ):
        validate_runtime_security(
            settings
        )
def test_production_cors_requires_https(
) -> None:
    settings = (
        build_hardened_settings(
            backend_cors_origins=[
                "http://app.example.com",
            ],
        )
    )
    with pytest.raises(
        RuntimeError,
        match="must use HTTPS",
    ):
        validate_runtime_security(
            settings
        )
def test_production_cors_rejects_localhost(
) -> None:
    settings = (
        build_hardened_settings(
            backend_cors_origins=[
                "https://localhost",
            ],
        )
    )
    with pytest.raises(
        RuntimeError,
        match="Localhost CORS origins",
    ):
        validate_runtime_security(
            settings
        )
def test_external_ai_requires_api_key(
) -> None:
    settings = (
        build_hardened_settings(
            ai_external_enabled=True,
            ai_api_key=None,
            ai_base_url=(
                "https://ai.example.com"
            ),
            ai_model_name="model",
        )
    )
    with pytest.raises(
        RuntimeError,
        match="AI_API_KEY is required",
    ):
        validate_runtime_security(
            settings
        )
def test_environment_templates_are_present(
) -> None:
    assert Path(
        ".env.example"
    ).is_file()
    assert Path(
        ".env.production.example"
    ).is_file()


def test_hardened_environment_requires_metrics(
) -> None:
    settings = build_hardened_settings(
        metrics_enabled=False,
    )

    with pytest.raises(
        RuntimeError,
        match="Metrics must be enabled",
    ):
        validate_runtime_security(
            settings
        )


def test_hardened_environment_requires_json_logging(
) -> None:
    settings = build_hardened_settings(
        log_json_enabled=False,
    )

    with pytest.raises(
        RuntimeError,
        match="JSON logging must be enabled",
    ):
        validate_runtime_security(
            settings
        )


def test_log_level_is_normalized(
) -> None:
    settings = Settings(
        _env_file=None,
        log_level=" warning ",
    )

    assert settings.log_level == "WARNING"


def test_unknown_log_level_is_rejected(
) -> None:
    with pytest.raises(
        ValidationError,
        match="Unsupported logging level",
    ):
        Settings(
            _env_file=None,
            log_level="verbose",
        )
