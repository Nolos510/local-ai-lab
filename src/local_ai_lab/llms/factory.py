from local_ai_lab.config.settings import Settings
from local_ai_lab.llms.base import ChatProvider
from local_ai_lab.llms.mock import MockChatProvider
from local_ai_lab.llms.ollama import OllamaChatProvider
from local_ai_lab.llms.openai_compatible import OpenAICompatibleChatProvider


def build_chat_provider(settings: Settings) -> ChatProvider:
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return OllamaChatProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    if provider in {"lm_studio", "openai_compatible"}:
        return OpenAICompatibleChatProvider(
            base_url=settings.lm_studio_base_url,
            model=settings.lm_studio_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    if provider == "mock":
        return MockChatProvider()
    msg = f"Unsupported LLM provider: {settings.llm_provider}"
    raise ValueError(msg)
