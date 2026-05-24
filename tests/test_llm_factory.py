from local_ai_lab.config.settings import Settings
from local_ai_lab.llms.factory import build_chat_provider
from local_ai_lab.llms.mock import MockChatProvider


def test_build_mock_chat_provider() -> None:
    settings = Settings(llm_provider="mock")

    provider = build_chat_provider(settings)

    assert isinstance(provider, MockChatProvider)
    assert "Mock local answer" in provider.generate("hello")
