from typing import Any

import httpx
import pytest

from local_ai_lab.llms.base import (
    ChatProviderConnectionError,
    ChatProviderHTTPError,
    ChatProviderResponseError,
)
from local_ai_lab.llms.ollama import OllamaChatProvider


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
        self.request = httpx.Request("POST", "http://localhost:11434/api/chat")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            response = httpx.Response(self.status_code, request=self.request)
            raise httpx.HTTPStatusError("HTTP error", request=self.request, response=response)

    def json(self) -> dict[str, Any]:
        if self.json_error:
            msg = "invalid json"
            raise ValueError(msg)
        return self.payload


def test_ollama_connection_error_becomes_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = OllamaChatProvider(
        base_url="http://user:secret@localhost:11434/private?token=abc#frag",
        model="qwen3:14b",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del kwargs
        request = httpx.Request("POST", url)
        raise httpx.ConnectError("connection failed", request=request)

    monkeypatch.setattr("local_ai_lab.llms.ollama.httpx.post", fake_post)

    with pytest.raises(ChatProviderConnectionError) as exc_info:
        provider.generate("private prompt")

    message = str(exc_info.value)
    assert "Ollama" in message
    assert "http://localhost:11434" in message
    assert "qwen3:14b" in message
    assert "uv run local-ai-lab doctor" in message
    assert "private prompt" not in message
    assert "secret" not in message
    assert "token=abc" not in message
    assert "/private" not in message
    assert "ollama pull" not in message


def test_ollama_http_404_includes_model_hints(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = OllamaChatProvider(
        base_url="http://localhost:11434",
        model="qwen3:14b",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse(status_code=404)

    monkeypatch.setattr("local_ai_lab.llms.ollama.httpx.post", fake_post)

    with pytest.raises(ChatProviderHTTPError) as exc_info:
        provider.generate("hello")

    message = str(exc_info.value)
    assert "HTTP 404" in message
    assert "ollama list" in message
    assert "ollama pull qwen3:14b" in message


def test_ollama_invalid_json_becomes_response_error(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = OllamaChatProvider(
        base_url="http://localhost:11434",
        model="qwen3:14b",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse(json_error=True)

    monkeypatch.setattr("local_ai_lab.llms.ollama.httpx.post", fake_post)

    with pytest.raises(ChatProviderResponseError) as exc_info:
        provider.generate("hello")

    assert "invalid JSON response" in str(exc_info.value)


def test_ollama_missing_message_content_becomes_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaChatProvider(
        base_url="http://localhost:11434",
        model="qwen3:14b",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse({"message": {}})

    monkeypatch.setattr("local_ai_lab.llms.ollama.httpx.post", fake_post)

    with pytest.raises(ChatProviderResponseError) as exc_info:
        provider.generate("hello")

    assert "unexpected response payload" in str(exc_info.value)


def test_ollama_empty_message_content_becomes_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaChatProvider(
        base_url="http://localhost:11434",
        model="qwen3:14b",
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse({"message": {"content": "   "}})

    monkeypatch.setattr("local_ai_lab.llms.ollama.httpx.post", fake_post)

    with pytest.raises(ChatProviderResponseError) as exc_info:
        provider.generate("hello")

    assert "empty message content" in str(exc_info.value)
