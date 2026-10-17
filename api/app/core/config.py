from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
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
    app_timezone: str = "Asia/Kolkata"
    database_url: str = "postgresql+asyncpg://mindtrail:mindtrail@localhost:5432/mindtrail"
    app_database_url: str | None = None
    auth_database_url: str = "sqlite:///./.data/mindtrail-auth.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)
    csrf_enabled: bool = True
    rate_limit_enabled: bool = True
    llm_provider: Literal["disabled", "openai", "anthropic"] = "disabled"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.app_env != "production":
            return self
        database_url = self.app_database_url or self.auth_database_url
        if self.app_debug:
            raise ValueError("APP_DEBUG must be false in production")
        if not database_url.startswith("postgresql"):
            raise ValueError("APP_DATABASE_URL must use PostgreSQL in production")
        if self.jwt_secret_key.startswith(("dev-only", "replace-with")):
            raise ValueError("JWT_SECRET_KEY must be rotated before production")
        if not self.csrf_enabled or not self.rate_limit_enabled:
            raise ValueError("CSRF and rate limiting must be enabled in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
