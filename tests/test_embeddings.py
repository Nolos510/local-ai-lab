import math
from typing import Any

import httpx
import pytest

from local_ai_lab.config.settings import Settings
from local_ai_lab.embeddings.base import (
    EmbeddingProviderConnectionError,
    EmbeddingProviderHTTPError,
    EmbeddingProviderResponseError,
)
from local_ai_lab.embeddings.deterministic import DeterministicEmbeddingProvider
from local_ai_lab.embeddings.factory import build_embedding_provider
from local_ai_lab.embeddings.ollama import OllamaEmbeddingProvider


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
        self.request = httpx.Request("POST", "http://localhost:11434/api/embed")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            response = httpx.Response(self.status_code, request=self.request)
            raise httpx.HTTPStatusError("HTTP error", request=self.request, response=response)

    def json(self) -> dict[str, Any]:
        if self.json_error:
            msg = "invalid json"
            raise ValueError(msg)
        return self.payload


def test_deterministic_embeddings_are_stable_and_normalized() -> None:
    provider = DeterministicEmbeddingProvider(vector_size=32)

    first = provider.embed("local ai lab")
    second = provider.embed("local ai lab")

    assert first == second
    assert len(first) == 32
    assert math.isclose(math.sqrt(sum(value * value for value in first)), 1.0)


def test_ollama_embedding_provider_returns_configured_vectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaEmbeddingProvider(
        base_url="http://localhost:11434",
        model="bge-m3",
        vector_size=3,
        timeout_seconds=1,
    )
    calls: list[dict[str, Any]] = []

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        calls.append({"url": url, **kwargs})
        return FakeResponse({"embeddings": [[1, 2, 3], [4.5, 5.5, 6.5]]})

    monkeypatch.setattr("local_ai_lab.embeddings.ollama.httpx.post", fake_post)

    vectors = provider.embed_many(["first", "second"])

    assert vectors == [[1.0, 2.0, 3.0], [4.5, 5.5, 6.5]]
    assert provider.vector_size == 3
    assert calls[0]["url"] == "http://localhost:11434/api/embed"
    assert calls[0]["json"] == {"model": "bge-m3", "input": ["first", "second"]}


def test_ollama_embedding_provider_accepts_legacy_single_embedding_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaEmbeddingProvider(
        base_url="http://localhost:11434",
        model="bge-m3",
        vector_size=2,
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse({"embedding": [0.1, 0.2]})

    monkeypatch.setattr("local_ai_lab.embeddings.ollama.httpx.post", fake_post)

    assert provider.embed("hello") == [0.1, 0.2]


def test_ollama_embedding_connection_error_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaEmbeddingProvider(
        base_url="http://user:secret@localhost:11434/private?token=abc#frag",
        model="bge-m3",
        vector_size=3,
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del kwargs
        request = httpx.Request("POST", url)
        raise httpx.ConnectError("connection failed", request=request)

    monkeypatch.setattr("local_ai_lab.embeddings.ollama.httpx.post", fake_post)

    with pytest.raises(EmbeddingProviderConnectionError) as exc_info:
        provider.embed("private doc text")

    message = str(exc_info.value)
    assert "Ollama embedding provider failed" in message
    assert "http://localhost:11434" in message
    assert "bge-m3" in message
    assert "uv run local-ai-lab doctor" in message
    assert "private doc text" not in message
    assert "secret" not in message
    assert "token=abc" not in message
    assert "/private" not in message


def test_ollama_embedding_http_404_includes_pull_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaEmbeddingProvider(
        base_url="http://localhost:11434",
        model="bge-m3",
        vector_size=3,
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse(status_code=404)

    monkeypatch.setattr("local_ai_lab.embeddings.ollama.httpx.post", fake_post)

    with pytest.raises(EmbeddingProviderHTTPError) as exc_info:
        provider.embed("hello")

    message = str(exc_info.value)
    assert "HTTP 404" in message
    assert "ollama list" in message
    assert "ollama pull bge-m3" in message


def test_ollama_embedding_bad_payload_becomes_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OllamaEmbeddingProvider(
        base_url="http://localhost:11434",
        model="bge-m3",
        vector_size=3,
        timeout_seconds=1,
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        del url, kwargs
        return FakeResponse({"embeddings": [[1.0, 2.0]]})

    monkeypatch.setattr("local_ai_lab.embeddings.ollama.httpx.post", fake_post)

    with pytest.raises(EmbeddingProviderResponseError) as exc_info:
        provider.embed("hello")

    assert "embedding dimension mismatch" in str(exc_info.value)


def test_embedding_factory_returns_ollama_provider() -> None:
    provider = build_embedding_provider(
        Settings(
            embedding_provider="ollama",
            ollama_base_url="http://localhost:11434",
            ollama_embedding_model="bge-m3",
            qdrant_vector_size=1024,
        )
    )

    assert isinstance(provider, OllamaEmbeddingProvider)
    assert provider.vector_size == 1024


def test_embedding_default_stays_deterministic_with_bge_m3_available_as_option() -> None:
    settings = Settings()
    provider = build_embedding_provider(settings)

    assert settings.embedding_provider == "deterministic"
    assert settings.ollama_embedding_model == "bge-m3"
    assert isinstance(provider, DeterministicEmbeddingProvider)
