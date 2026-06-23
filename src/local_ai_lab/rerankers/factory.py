from local_ai_lab.config.settings import Settings
from local_ai_lab.rerankers.base import Reranker
from local_ai_lab.rerankers.identity import IdentityReranker


def build_reranker(settings: Settings) -> Reranker:
    provider = settings.reranker_provider.lower()
    if provider == "identity":
        return IdentityReranker()
    msg = (
        f"Unsupported reranker provider: {settings.reranker_provider}. "
        "The default provider is 'identity'. Local cross-encoder support is "
        "reserved for the optional [rerank] extra and a reviewed backend."
    )
    raise ValueError(msg)
