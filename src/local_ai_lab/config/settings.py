from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and optional .env files."""

    model_config = SettingsConfigDict(
        env_prefix="LOCAL_AI_LAB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "local-ai-lab"
    env: str = "local"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "local_ai_lab_chunks"
    qdrant_vector_size: int = Field(default=1024, ge=8)

    embedding_provider: str = "deterministic"
    ollama_embedding_model: str = "bge-m3"

    vector_store_provider: str = "qdrant"

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:14b"
    lm_studio_base_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "local-model"

    top_k: int = Field(default=5, ge=1)
    chunk_size: int = Field(default=900, ge=100)
    chunk_overlap: int = Field(default=120, ge=0)
    request_timeout_seconds: float = Field(default=120.0, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
