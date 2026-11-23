from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ClinGraph AI Service"
    app_env: str = "development"
    ai_host: str = "0.0.0.0"
    ai_port: int = 8001
    backend_shared_secret: str = "dev-only-secret"
    bm25_weight: float = 0.5
    dense_weight: float = 0.5
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    embedding_local_files_only: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
