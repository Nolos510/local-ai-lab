from local_ai_lab.config.settings import Settings
from local_ai_lab.vectorstores.qdrant import QdrantVectorStore


def build_vector_store(settings: Settings) -> QdrantVectorStore:
    return QdrantVectorStore(
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        vector_size=settings.qdrant_vector_size,
    )
