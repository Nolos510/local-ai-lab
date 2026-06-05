from typing import Protocol
from urllib.parse import urlsplit, urlunsplit


class EmbeddingProviderError(RuntimeError):
    """Base error for local embedding provider failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


class EmbeddingProviderConnectionError(EmbeddingProviderError):
    """Raised when an embedding endpoint cannot be reached."""


class EmbeddingProviderHTTPError(EmbeddingProviderError):
    """Raised when an embedding endpoint returns an HTTP error."""


class EmbeddingProviderResponseError(EmbeddingProviderError):
    """Raised when an embedding endpoint returns an invalid response payload."""


class EmbeddingProvider(Protocol):
    @property
    def vector_size(self) -> int:
        """Return the dimensionality of embeddings produced by this provider."""

    def embed(self, text: str) -> list[float]:
        """Embed one string."""

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple strings."""


def sanitize_provider_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.scheme or not parts.hostname:
        return "configured URL"
    netloc = parts.hostname
    if parts.port is not None:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, "", "", ""))
