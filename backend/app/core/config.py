from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "P-TRADER AI Backend"
    app_version: str = "1.0.0"
    app_description: str = "Backend API for P-TRADER AI"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./p_trader_ai.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()