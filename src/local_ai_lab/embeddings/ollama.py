from __future__ import annotations

from typing import Any

import httpx

from local_ai_lab.embeddings.base import (
    EmbeddingProviderConnectionError,
    EmbeddingProviderHTTPError,
    EmbeddingProviderResponseError,
    sanitize_provider_url,
)


class OllamaEmbeddingProvider:
    """Local semantic embedding provider backed by Ollama's `/api/embed` endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        vector_size: int,
        timeout_seconds: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._vector_size = vector_size
        self.timeout_seconds = timeout_seconds

    @property
    def vector_size(self) -> int:
        return self._vector_size

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = self._request_embeddings(texts)
        embeddings = self._extract_embeddings(payload, expected_count=len(texts))
        return [self._validate_vector(vector) for vector in embeddings]

    def _request_embeddings(self, texts: list[str]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model,
                    "input": texts,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            include_pull_hint = exc.response.status_code == 404
            raise EmbeddingProviderHTTPError(
                self._error_message(
                    f"HTTP {exc.response.status_code}",
                    include_pull_hint=include_pull_hint,
                )
            ) from exc
        except httpx.RequestError as exc:
            raise EmbeddingProviderConnectionError(
                self._error_message("connection failed")
            ) from exc
        except ValueError as exc:
            raise EmbeddingProviderResponseError(
                self._error_message("invalid JSON response")
            ) from exc

        if not isinstance(payload, dict):
            raise EmbeddingProviderResponseError(
                self._error_message("unexpected response payload")
            )
        return payload

    def _extract_embeddings(
        self,
        payload: dict[str, Any],
        *,
        expected_count: int,
    ) -> list[list[Any]]:
        embeddings = payload.get("embeddings")
        if isinstance(embeddings, list):
            if len(embeddings) != expected_count:
                raise EmbeddingProviderResponseError(
                    self._error_message(
                        "embedding count did not match requested input count"
                    )
                )
            return embeddings

        legacy_embedding = payload.get("embedding")
        if expected_count == 1 and isinstance(legacy_embedding, list):
            return [legacy_embedding]

        raise EmbeddingProviderResponseError(
            self._error_message("unexpected response payload")
        )

    def _validate_vector(self, vector: list[Any]) -> list[float]:
        if len(vector) != self._vector_size:
            raise EmbeddingProviderResponseError(
                self._error_message(
                    "embedding dimension mismatch; reindex with matching "
                    "LOCAL_AI_LAB_QDRANT_VECTOR_SIZE"
                )
            )
        try:
            return [float(value) for value in vector]
        except (TypeError, ValueError) as exc:
            raise EmbeddingProviderResponseError(
                self._error_message("embedding vector contained non-numeric values")
            ) from exc

    def _error_message(self, reason: str, *, include_pull_hint: bool = False) -> str:
        message = (
            f"Ollama embedding provider failed: {reason}. "
            f"Endpoint: {sanitize_provider_url(self.base_url)}. "
            f"Configured embedding model: {self.model}. "
            "Run `uv run local-ai-lab doctor`. "
            "Check installed models with `ollama list`."
        )
        if include_pull_hint:
            message = f"{message} Pull the configured model with `ollama pull {self.model}`."
        return message
