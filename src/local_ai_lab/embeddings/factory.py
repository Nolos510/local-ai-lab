from local_ai_lab.config.settings import Settings
from local_ai_lab.embeddings.base import EmbeddingProvider
from local_ai_lab.embeddings.deterministic import DeterministicEmbeddingProvider


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if provider == "deterministic":
        return DeterministicEmbeddingProvider(vector_size=settings.qdrant_vector_size)
    msg = f"Unsupported embedding provider: {settings.embedding_provider}"
    raise ValueError(msg)
