# ADR 0002: Local semantic embeddings via Ollama

## Status

Accepted

## Context

The initial RAG path used `DeterministicEmbeddingProvider`, a hash-based local
test provider. It is reproducible and useful for offline tests, but it is not
semantic. Retrieval quality work and retrieval evals require a real local
embedding model.

The project already treats Ollama as a native macOS runtime and already has
Ollama provider health checks. The v1 improvement brief identifies BGE-M3 as
the first semantic embedding target.

## Decision

- Keep deterministic embeddings as the default test/offline provider.
- Add `OllamaEmbeddingProvider` behind `LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama`.
- Use Ollama's local `/api/embed` endpoint. Do not add model downloads, cloud
  API calls, SDK clients, or secrets.
- Add `LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL`, defaulting to `bge-m3`.
- Set the default `LOCAL_AI_LAB_QDRANT_VECTOR_SIZE` expectation to `1024`, which
  matches BGE-M3.
- Make doctor checks verify the configured Ollama embedding model only when the
  Ollama embedding provider is selected.

## Consequences

- Semantic retrieval can be enabled locally once the embedding model exists in
  Ollama.
- Existing Qdrant collections created with 384-dimensional deterministic
  vectors must be dropped and recreated before using BGE-M3. Qdrant collection
  vector size is fixed at creation time, so mixing embedding dimensions or
  models would corrupt retrieval quality.
- Offline tests remain deterministic because the default provider does not call
  Ollama.
- Any future embedding provider must preserve typed errors, sanitized endpoint
  messages, and explicit vector-size handling.

## Reindex Requirement

When changing `LOCAL_AI_LAB_EMBEDDING_PROVIDER`,
`LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL`, or
`LOCAL_AI_LAB_QDRANT_VECTOR_SIZE`, recreate the Qdrant collection and reingest
documents. Until a dedicated `reindex` command exists, use the documented manual
sequence in `docs/rag.md`.
