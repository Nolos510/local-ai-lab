from typing import Any

import httpx
import pytest

from local_ai_lab.llms.base import (
    ChatProviderConnectionError,
    ChatProviderHTTPError,
    ChatProviderResponseError,
)
from local_ai_lab.llms.openai_compatible import OpenAICompatibleChatProvider


class FakeResponse:
    def __init__(
        self,
        payload: dict[str, Any] | None = None,
        *,
        status_code: int = 200,
        json_error: bool = False,
    ) -> None:
        self.payload = payload or {}
        self.status_code = status_code
        self.json_error = json_error
        self.request = httpx.Request("POST", "http://localhost:1234/v1/chat/completions")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            response = httpx.Response(self.status_code, request=self.request)
            raise httpx.HTTPStatusError("HTTP error", request=self.request, response=response)

    def json(self) -> dict[str, Any]:
        if self.json_error:
            msg = "invalid json"
            raise ValueError(msg)
        return self.payload


def test_openai_compatible_connection_error_becomes_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatibleChatProvider(
        base_url="http://user:secret@localhost:1234/private/v1?token=abc#frag",
        model="local-model",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del kwargs
        request = httpx.Request("POST", url)
        raise httpx.ConnectError("connection failed", request=request)

    monkeypatch.setattr("local_ai_lab.llms.openai_compatible.httpx.post", fake_post)

    with pytest.raises(ChatProviderConnectionError) as exc_info:
        provider.generate("private prompt")

    message = str(exc_info.value)
    assert "LM Studio/OpenAI-compatible" in message
    assert "http://localhost:1234" in message
    assert "local-model" in message
    assert "Verify the LM Studio local server is running" in message
    assert "uv run local-ai-lab doctor" in message
    assert "private prompt" not in message
    assert "secret" not in message
    assert "token=abc" not in message
    assert "/private" not in message


def test_openai_compatible_http_error_becomes_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatibleChatProvider(
        base_url="http://localhost:1234/v1",
        model="local-model",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse(status_code=500)

    monkeypatch.setattr("local_ai_lab.llms.openai_compatible.httpx.post", fake_post)

    with pytest.raises(ChatProviderHTTPError) as exc_info:
        provider.generate("hello")

    message = str(exc_info.value)
    assert "HTTP 500" in message
    assert "local-model" in message
    assert "uv run local-ai-lab doctor" in message


def test_openai_compatible_invalid_json_becomes_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatibleChatProvider(
        base_url="http://localhost:1234/v1",
        model="local-model",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse(json_error=True)

    monkeypatch.setattr("local_ai_lab.llms.openai_compatible.httpx.post", fake_post)

    with pytest.raises(ChatProviderResponseError) as exc_info:
        provider.generate("hello")

    assert "invalid JSON response" in str(exc_info.value)


def test_openai_compatible_missing_choices_becomes_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatibleChatProvider(
        base_url="http://localhost:1234/v1",
        model="local-model",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse({})

    monkeypatch.setattr("local_ai_lab.llms.openai_compatible.httpx.post", fake_post)

    with pytest.raises(ChatProviderResponseError) as exc_info:
        provider.generate("hello")

    assert "empty choices in response" in str(exc_info.value)


def test_openai_compatible_empty_choices_becomes_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatibleChatProvider(
        base_url="http://localhost:1234/v1",
        model="local-model",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse({"choices": []})

    monkeypatch.setattr("local_ai_lab.llms.openai_compatible.httpx.post", fake_post)

    with pytest.raises(ChatProviderResponseError) as exc_info:
        provider.generate("hello")

    message = str(exc_info.value)
    assert "LM Studio/OpenAI-compatible" in message
    assert "http://localhost:1234" in message
    assert "local-model" in message
    assert "uv run local-ai-lab doctor" in message


def test_openai_compatible_malformed_message_content_becomes_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatibleChatProvider(
        base_url="http://localhost:1234/v1",
        model="local-model",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse({"choices": [{"message": {}}]})

    monkeypatch.setattr("local_ai_lab.llms.openai_compatible.httpx.post", fake_post)

    with pytest.raises(ChatProviderResponseError) as exc_info:
        provider.generate("hello")

    assert "unexpected response payload" in str(exc_info.value)


def test_openai_compatible_empty_message_content_becomes_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatibleChatProvider(
        base_url="http://localhost:1234/v1",
        model="local-model",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse({"choices": [{"message": {"content": "   "}}]})

    monkeypatch.setattr("local_ai_lab.llms.openai_compatible.httpx.post", fake_post)

    with pytest.raises(ChatProviderResponseError) as exc_info:
        provider.generate("hello")

    assert "empty message content" in str(exc_info.value)
