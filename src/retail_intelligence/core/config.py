from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "retail-store-intelligence"
    app_version: str = "0.1.0"
    app_env: str = "local"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"
    health_path: str = "/health"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://retail:retail@postgres:5432/retail_intelligence"
    redis_url: str = "redis://redis:6379/0"
    redis_stream_events: str = "store_events"
    redis_stream_store_ids: str = ""
    health_stale_feed_minutes: int = 15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
