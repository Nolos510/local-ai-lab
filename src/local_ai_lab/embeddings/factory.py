from local_ai_lab.config.settings import Settings
from local_ai_lab.embeddings.base import EmbeddingProvider
from local_ai_lab.embeddings.deterministic import DeterministicEmbeddingProvider
from local_ai_lab.embeddings.ollama import OllamaEmbeddingProvider


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if provider == "deterministic":
        return DeterministicEmbeddingProvider(vector_size=settings.qdrant_vector_size)
    if provider == "ollama":
        return OllamaEmbeddingProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
            vector_size=settings.qdrant_vector_size,
            timeout_seconds=settings.request_timeout_seconds,
        )
    msg = f"Unsupported embedding provider: {settings.embedding_provider}"
    raise ValueError(msg)
