from urllib.parse import urlparse
from cryptography.fernet import (
    Fernet,
)
from sqlalchemy.engine import (
    make_url,
)
from app.core.config import (
    DEVELOPMENT_ENCRYPTION_KEY,
    DEVELOPMENT_SECRET_KEY,
    Settings,
)
PRODUCTION_ENVIRONMENTS = frozenset({
    "production",
})
HARDENED_ENVIRONMENTS = frozenset({
    "staging",
    "production",
})
SUPPORTED_JWT_ALGORITHMS = frozenset({
    "HS256",
    "HS384",
    "HS512",
})
INSECURE_SECRET_KEYS = frozenset({
    "change_me_in_production",
    "change-this-secret-key",
    (
        "replace_with_at_least_32_"
        "random_characters"
    ),
    DEVELOPMENT_SECRET_KEY.lower(),
})
INSECURE_ENCRYPTION_KEYS = frozenset({
    "change_me_encryption_key",
    "change-this-fernet-key",
    "replace_with_a_fernet_key",
    DEVELOPMENT_ENCRYPTION_KEY.lower(),
})
LOCAL_CORS_HOSTNAMES = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
})
def _plain_secret(
    value: object,
) -> str:
    get_secret_value = getattr(
        value,
        "get_secret_value",
        None,
    )
    if callable(get_secret_value):
        return str(
            get_secret_value()
        ).strip()
    return str(value).strip()
def _validate_hardened_cors_origin(
    origin: str,
) -> None:
    parsed = urlparse(origin)
    if (
        parsed.scheme.lower()
        != "https"
        or not parsed.netloc
    ):
        raise RuntimeError(
            "Production CORS origins must "
            "use HTTPS"
        )
    if (
        parsed.username is not None
        or parsed.password is not None
    ):
        raise RuntimeError(
            "Production CORS origins cannot "
            "contain credentials"
        )
    hostname = (
        parsed.hostname
        or ""
    ).lower()
    if (
        hostname in LOCAL_CORS_HOSTNAMES
        or hostname.endswith(
            ".localhost"
        )
    ):
        raise RuntimeError(
            "Localhost CORS origins are not "
            "allowed in production"
        )
    if (
        parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError(
            "Production CORS origins must "
            "contain only scheme and host"
        )
def validate_runtime_security(
    settings: Settings,
) -> None:
    environment = (
        settings.environment
        .strip()
        .lower()
    )
    secret_key = _plain_secret(
        settings.secret_key
    )
    encryption_key = _plain_secret(
        settings.encryption_key
    )
    algorithm = (
        settings.algorithm
        .strip()
        .upper()
    )
    database_url = (
        settings.database_url
        .strip()
    )
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY cannot be blank"
        )
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL cannot be blank"
        )
    try:
        database_backend = (
            make_url(database_url)
            .get_backend_name()
        )
    except Exception as error:
        raise RuntimeError(
            "DATABASE_URL is invalid"
        ) from error
    if algorithm not in (
        SUPPORTED_JWT_ALGORITHMS
    ):
        raise RuntimeError(
            "JWT algorithm is not supported"
        )
    if (
        settings
        .access_token_expire_minutes
        <= 0
    ):
        raise RuntimeError(
            "Access-token expiration must "
            "be greater than zero"
        )
    try:
        Fernet(
            encryption_key.encode(
                "utf-8"
            )
        )
    except Exception as error:
        raise RuntimeError(
            "ENCRYPTION_KEY must be a "
            "valid Fernet key"
        ) from error
    if settings.ai_external_enabled:
        ai_api_key = (
            _plain_secret(
                settings.ai_api_key
            )
            if settings.ai_api_key
            is not None
            else ""
        )
        if not ai_api_key:
            raise RuntimeError(
                "AI_API_KEY is required when "
                "external AI is enabled"
            )
        if not (
            settings.ai_base_url
            and settings
            .ai_base_url
            .strip()
        ):
            raise RuntimeError(
                "AI_BASE_URL is required when "
                "external AI is enabled"
            )
        if not (
            settings.ai_model_name
            and settings
            .ai_model_name
            .strip()
        ):
            raise RuntimeError(
                "AI_MODEL_NAME is required "
                "when external AI is enabled"
            )
    if (
        settings.automation_runtime_enabled
        and settings.web_concurrency != 1
    ):
        raise RuntimeError(
            "The in-memory automation runtime "
            "requires WEB_CONCURRENCY=1"
        )
    if environment not in (
        HARDENED_ENVIRONMENTS
    ):
        return
    if settings.debug:
        raise RuntimeError(
            "DEBUG must be disabled in "
            "production"
        )
    if not settings.trusted_hosts:
        raise RuntimeError(
            "At least one trusted host is "
            "required in production"
        )
    if "*" in settings.trusted_hosts:
        raise RuntimeError(
            "Wildcard trusted hosts are not "
            "allowed in production"
        )
    if not settings.security_headers_enabled:
        raise RuntimeError(
            "Security headers must be enabled "
            "in production"
        )
    if settings.api_docs_enabled:
        raise RuntimeError(
            "API documentation must be "
            "disabled in hardened environments"
        )
    if not settings.metrics_enabled:
        raise RuntimeError(
            "Metrics must be enabled in "
            "hardened environments"
        )
    if not settings.log_json_enabled:
        raise RuntimeError(
            "JSON logging must be enabled in "
            "hardened environments"
        )
    if (
        secret_key.lower()
        in INSECURE_SECRET_KEYS
        or len(secret_key) < 32
    ):
        raise RuntimeError(
            "Production SECRET_KEY is "
            "insecure"
        )
    if (
        encryption_key.lower()
        in INSECURE_ENCRYPTION_KEYS
    ):
        raise RuntimeError(
            "Production ENCRYPTION_KEY is "
            "insecure"
        )
    if not settings.backend_cors_origins:
        raise RuntimeError(
            "At least one production CORS "
            "origin is required"
        )
    if "*" in settings.backend_cors_origins:
        raise RuntimeError(
            "Wildcard CORS origins are not "
            "allowed in production"
        )
    for origin in (
        settings.backend_cors_origins
    ):
        _validate_hardened_cors_origin(
            origin
        )
    if database_backend != "postgresql":
        raise RuntimeError(
            "Staging and production "
            "require PostgreSQL"
        )
    if settings.ai_external_enabled:
        parsed_ai_url = urlparse(
            settings.ai_base_url.strip()
        )
        if (
            parsed_ai_url.scheme.lower()
            != "https"
            or not parsed_ai_url.netloc
        ):
            raise RuntimeError(
                "External AI must use an "
                "HTTPS base URL in production"
            )
