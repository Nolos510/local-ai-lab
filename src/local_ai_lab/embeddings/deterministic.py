import hashlib
import math
import re

TOKEN_RE = re.compile(r"[A-Za-z0-9_./:-]+")


class DeterministicEmbeddingProvider:
    """Small deterministic embedding provider for local tests and offline smoke runs.

    This is intentionally not a semantic model. It provides stable vectors so the v0
    pipeline can be exercised before a real local embedding model is wired in.
    """

    def __init__(self, vector_size: int = 384) -> None:
        self._vector_size = vector_size

    @property
    def vector_size(self) -> int:
        return self._vector_size

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self._vector_size
        tokens = TOKEN_RE.findall(text.lower())
        if not tokens:
            tokens = [hashlib.sha256(text.encode("utf-8")).hexdigest()]

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._vector_size
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + min(len(token), 24) / 24.0
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]
