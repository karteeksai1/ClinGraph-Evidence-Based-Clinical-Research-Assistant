from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ClinGraph API"
    app_env: str = "development"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    ai_service_url: str = "http://localhost:8001"
    request_timeout_seconds: float = 45.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
