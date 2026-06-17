import pytest

from local_ai_lab.config.settings import Settings


def test_settings_defaults_are_local_first() -> None:
    settings = Settings()

    assert settings.qdrant_url == "http://localhost:6333"
    assert settings.embedding_provider == "deterministic"
    assert settings.ollama_embedding_model == "bge-m3"
    assert settings.qdrant_vector_size == 1024
    assert settings.vector_store_provider == "qdrant"
    assert settings.llm_provider == "ollama"


def test_settings_reject_remote_service_urls() -> None:
    with pytest.raises(ValueError, match="loopback"):
        Settings(qdrant_url="http://192.168.1.10:6333")
    with pytest.raises(ValueError, match="loopback"):
        Settings(ollama_base_url="http://203.0.113.10:11434")
    with pytest.raises(ValueError, match="loopback"):
        Settings(lm_studio_base_url="http://example.com/v1")


def test_settings_reject_large_top_k() -> None:
    with pytest.raises(ValueError):
        Settings(top_k=21)
