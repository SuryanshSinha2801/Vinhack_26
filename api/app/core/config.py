from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables and the local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MindTrail API"
    app_env: Literal["development", "test", "production"] = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/v1"
    database_url: str = "postgresql+asyncpg://mindtrail:mindtrail@localhost:5432/mindtrail"
    auth_database_url: str = "sqlite:///./.data/mindtrail-auth.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)
    llm_provider: Literal["disabled", "openai", "anthropic"] = "disabled"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
