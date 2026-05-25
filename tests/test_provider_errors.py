from local_ai_lab.llms.base import ChatProviderError, sanitize_provider_url


def test_sanitize_provider_url_strips_private_parts() -> None:
    safe_url = sanitize_provider_url("http://user:secret@localhost:11434/private?token=abc#frag")

    assert safe_url == "http://localhost:11434"
    assert "user" not in safe_url
    assert "secret" not in safe_url
    assert "token" not in safe_url
    assert "private" not in safe_url


def test_chat_provider_error_carries_user_message() -> None:
    error = ChatProviderError("safe message")

    assert error.user_message == "safe message"
    assert str(error) == "safe message"
