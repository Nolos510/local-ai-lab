import pytest

from local_ai_lab.config.settings import Settings
from local_ai_lab.vectorstores.factory import build_vector_store
from local_ai_lab.vectorstores.qdrant import QdrantVectorStore


def test_build_qdrant_vector_store() -> None:
    store = build_vector_store(Settings(vector_store_provider="qdrant"))

    assert isinstance(store, QdrantVectorStore)


def test_build_vector_store_rejects_unsupported_provider() -> None:
    settings = Settings(vector_store_provider="unsupported")

    with pytest.raises(ValueError, match="Unsupported vector store provider"):
        build_vector_store(settings)
