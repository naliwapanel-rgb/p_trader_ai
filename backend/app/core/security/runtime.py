from cryptography.fernet import (
    Fernet,
)
from app.core.config import (
    Settings,
)
PRODUCTION_ENVIRONMENTS = frozenset({
    "prod",
    "production",
})
SUPPORTED_JWT_ALGORITHMS = frozenset({
    "HS256",
    "HS384",
    "HS512",
})
INSECURE_SECRET_KEYS = frozenset({
    "CHANGE_ME_IN_PRODUCTION",
    "change-this-secret-key",
})
INSECURE_ENCRYPTION_KEYS = frozenset({
    "CHANGE_ME_ENCRYPTION_KEY",
    "change-this-fernet-key",
})
def validate_runtime_security(
    settings: Settings,
) -> None:
    environment = (
        settings.environment
        .strip()
        .lower()
    )
    secret_key = (
        settings.secret_key.strip()
    )
    encryption_key = (
        settings.encryption_key.strip()
    )
    algorithm = (
        settings.algorithm
        .strip()
        .upper()
    )
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY cannot be blank"
        )
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
            encryption_key.encode()
        )
    except Exception as error:
        raise RuntimeError(
            "ENCRYPTION_KEY must be a "
            "valid Fernet key"
        ) from error
    if environment not in (
        PRODUCTION_ENVIRONMENTS
    ):
        return
    if settings.debug:
        raise RuntimeError(
            "DEBUG must be disabled in "
            "production"
        )
    if (
        secret_key
        in INSECURE_SECRET_KEYS
        or len(secret_key) < 32
    ):
        raise RuntimeError(
            "Production SECRET_KEY is "
            "insecure"
        )
    if (
        encryption_key
        in INSECURE_ENCRYPTION_KEYS
    ):
        raise RuntimeError(
            "Production ENCRYPTION_KEY is "
            "insecure"
        )
    if "*" in (
        settings.backend_cors_origins
    ):
        raise RuntimeError(
            "Wildcard CORS origins are not "
            "allowed in production"
        )
