from local_ai_lab.config.settings import Settings, get_settings
from local_ai_lab.embeddings.factory import build_embedding_provider
from local_ai_lab.llms.factory import build_chat_provider
from local_ai_lab.rag.service import RAGService
from local_ai_lab.vectorstores.factory import build_vector_store


def build_rag_service(settings: Settings | None = None) -> RAGService:
    resolved_settings = settings or get_settings()
    return RAGService(
        settings=resolved_settings,
        embedding_provider=build_embedding_provider(resolved_settings),
        vector_store=build_vector_store(resolved_settings),
        chat_provider=build_chat_provider(resolved_settings),
    )
