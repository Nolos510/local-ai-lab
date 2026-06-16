from local_ai_lab.config.settings import Settings


def test_settings_defaults_are_local_first() -> None:
    settings = Settings(_env_file=None)

    assert settings.qdrant_url == "http://localhost:6333"
    assert settings.embedding_provider == "deterministic"
    assert settings.ollama_embedding_model == "bge-m3"
    assert settings.qdrant_vector_size == 1024
    assert settings.vector_store_provider == "qdrant"
    assert settings.llm_provider == "ollama"
