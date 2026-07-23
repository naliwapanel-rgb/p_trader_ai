from functools import lru_cache
from pydantic import (
    Field,
    SecretStr,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
ENVIRONMENT_ALIASES = {
    "dev": "development",
    "development": "development",
    "test": "testing",
    "testing": "testing",
    "stage": "staging",
    "staging": "staging",
    "prod": "production",
    "production": "production",
}
SUPPORTED_ENVIRONMENTS = frozenset(
    ENVIRONMENT_ALIASES.values()
)
DEVELOPMENT_SECRET_KEY = (
    "development-only-secret-key-"
    "change-before-production"
)
DEVELOPMENT_ENCRYPTION_KEY = (
    "WokfjCgTZ0yVLZwYhDRQNS6nZ_"
    "CTX2O8eaIXq2IP0zg="
)
class Settings(BaseSettings):
    app_name: str = "P-TRADER AI Backend"
    app_version: str = "1.0.0"
    app_description: str = (
        "Backend API for P-TRADER AI"
    )
    environment: str = "development"
    debug: bool = True
    exchange_trading_enabled: bool = False
    exchange_dry_run: bool = True
    max_order_quantity: float = 1.0
    max_order_value_usd: float = 25.0
    ai_external_enabled: bool = False
    ai_provider: str = "OPENAI_COMPATIBLE"
    ai_api_key: SecretStr | None = None
    ai_base_url: str | None = None
    ai_model_name: str | None = None
    ai_request_timeout_seconds: float = Field(
        default=20.0,
        gt=0,
        le=120,
    )
    database_url: str = (
        "sqlite:///./p_trader_ai.db"
    )
    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
    )
    database_pool_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=300,
    )
    database_pool_recycle_seconds: int = Field(
        default=1800,
        ge=0,
        le=86400,
    )
    secret_key: str = (
        DEVELOPMENT_SECRET_KEY
    )
    encryption_key: str = (
        DEVELOPMENT_ENCRYPTION_KEY
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    backend_cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    @field_validator(
        "environment",
        mode="before",
    )
    @classmethod
    def normalize_environment(
        cls,
        value: object,
    ) -> str:
        normalized = (
            str(value)
            .strip()
            .lower()
        )
        canonical = ENVIRONMENT_ALIASES.get(
            normalized
        )
        if canonical is None:
            supported = ", ".join(
                sorted(
                    SUPPORTED_ENVIRONMENTS
                )
            )
            raise ValueError(
                "Unsupported environment. "
                f"Supported values: {supported}"
            )
        return canonical
    @field_validator(
        "algorithm",
        mode="before",
    )
    @classmethod
    def normalize_algorithm(
        cls,
        value: object,
    ) -> str:
        return (
            str(value)
            .strip()
            .upper()
        )
    @field_validator(
        "backend_cors_origins",
    )
    @classmethod
    def normalize_cors_origins(
        cls,
        origins: list[str],
    ) -> list[str]:
        normalized_origins = []
        for origin in origins:
            normalized = (
                origin
                .strip()
                .rstrip("/")
            )
            if (
                normalized
                and normalized
                not in normalized_origins
            ):
                normalized_origins.append(
                    normalized
                )
        return normalized_origins
    @property
    def is_production(
        self,
    ) -> bool:
        return (
            self.environment
            == "production"
        )
    @property
    def is_hardened_environment(
        self,
    ) -> bool:
        return self.environment in {
            "staging",
            "production",
        }
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
@lru_cache
def get_settings() -> Settings:
    return Settings()
