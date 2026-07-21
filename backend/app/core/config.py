from functools import lru_cache

from pydantic import (
    Field,
    SecretStr,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "P-TRADER AI Backend"
    app_version: str = "1.0.0"
    app_description: str = "Backend API for P-TRADER AI"
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
    database_url: str = "sqlite:///./p_trader_ai.db"

    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    encryption_key: str = "CHANGE_ME_ENCRYPTION_KEY"

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    backend_cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
