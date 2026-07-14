from local_ai_lab.config.settings import Settings
from local_ai_lab.rerankers.base import Reranker
from local_ai_lab.rerankers.cross_encoder import CrossEncoderReranker
from local_ai_lab.rerankers.identity import IdentityReranker


def build_reranker(settings: Settings) -> Reranker:
    provider = settings.reranker_provider.lower()
    if provider == "identity":
        return IdentityReranker()
    if provider == "cross_encoder":
        return CrossEncoderReranker(model_path=settings.reranker_model_path)
    msg = (
        f"Unsupported reranker provider: {settings.reranker_provider}. "
        "Supported providers: identity, cross_encoder."
    )
    raise ValueError(msg)
