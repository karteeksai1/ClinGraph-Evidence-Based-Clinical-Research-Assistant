from functools import lru_cache
from pathlib import Path

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
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    database_url: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "clingraph-evidence"
    pinecone_index_host: str = ""
    pinecone_namespace: str = "clinical-evidence"
    redis_url: str = ""
    redis_cache_ttl_seconds: int = 3600
    evaluation_dataset_path: str = "evaluations/dataset.jsonl"

    # Resolve the repository .env regardless of whether uvicorn is started from
    # the repository root, services/ai, or a process manager's working folder.
    _repo_root = Path(__file__).resolve().parents[3]
    model_config = SettingsConfigDict(
        env_file=(str(_repo_root / ".env"), ".env"),
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
