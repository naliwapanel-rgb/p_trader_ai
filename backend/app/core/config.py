from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "P-TRADER AI Backend"
    app_version: str = "1.0.0"
    app_description: str = "Backend API for P-TRADER AI"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./p_trader_ai.db"

    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
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