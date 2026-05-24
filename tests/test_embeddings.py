import math

from local_ai_lab.embeddings.deterministic import DeterministicEmbeddingProvider


def test_deterministic_embeddings_are_stable_and_normalized() -> None:
    provider = DeterministicEmbeddingProvider(vector_size=32)

    first = provider.embed("local ai lab")
    second = provider.embed("local ai lab")

    assert first == second
    assert len(first) == 32
    assert math.isclose(math.sqrt(sum(value * value for value in first)), 1.0)
