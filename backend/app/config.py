from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ClinGraph"
    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    bm25_weight: float = 0.5
    dense_weight: float = 0.5
    database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
