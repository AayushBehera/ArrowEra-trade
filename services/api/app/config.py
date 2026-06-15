from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "ArrowEra Trade API"
    version: str = "0.2.0"
    environment: str = "development"
    debug: bool = False
    secret_key: str = Field(default="development-only-change-this-secret-key", min_length=32)
    database_url: str = "sqlite+aiosqlite:///./arrowera.db"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    rate_limit_per_minute: int = Field(default=120, ge=1)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = Field(default=30, ge=1)
    llm_provider_order: list[str] = ["openai", "anthropic", "gemini", "deepseek", "ollama"]
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-chat"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    @field_validator("cors_origins", "allowed_hosts", "llm_provider_order", mode="before")
    @classmethod
    def split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("secret_key")
    @classmethod
    def reject_default_in_production(cls, value: str, info):
        environment = info.data.get("environment", "development")
        if environment == "production" and value.startswith("development-only"):
            raise ValueError("SECRET_KEY must be replaced in production")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
