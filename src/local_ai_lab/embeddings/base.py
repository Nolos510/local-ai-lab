from typing import Protocol


class EmbeddingProvider(Protocol):
    @property
    def vector_size(self) -> int:
        """Return the dimensionality of embeddings produced by this provider."""

    def embed(self, text: str) -> list[float]:
        """Embed one string."""

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple strings."""
