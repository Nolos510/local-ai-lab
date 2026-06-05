# ADR 0001: Local-first Apple Silicon architecture with native model runtimes

## Status

Accepted

## Context

`local-ai-lab` targets an Apple Silicon Mac Studio with 256 GB unified memory, large local storage, and privacy-first local workflows. The v0 milestone is a local RAG backbone and provider harness:

```text
CLI / FastAPI
  -> ingestion
  -> chunking
  -> Qdrant retrieval
  -> prompt assembly
  -> local model provider
  -> answer + citations
```

The project needs a setup that is reproducible and simple while preserving Apple-native model runtime performance.

## Decision

- Use Docker for infrastructure services such as Qdrant and Open WebUI.
- Keep Ollama, LM Studio, MLX, MLX-LM, and llama.cpp native on macOS for v0.
- Keep FastAPI and CLI native via `uv` for v0.
- Use Qdrant as the v0 vector database.
- Treat Open WebUI as optional and parallel, not a dependency of the FastAPI RAG harness.

## Consequences

- Local model runtimes can use their normal Apple Silicon acceleration paths.
- Qdrant and Open WebUI remain easy to start, stop, and replace.
- The FastAPI/CLI harness stays lightweight and testable.
- Contributors must document any future change to runtime boundaries in an ADR.
- Full cloud portability is deferred until the local loop is useful and measured.

## Alternatives Considered

### All-in-Docker

Rejected for v0 because containerizing model runtimes would add complexity and may interfere with the native macOS workflows used by Ollama, LM Studio, MLX/MLX-LM, and llama.cpp.

### Qdrant-only

Rejected because Open WebUI is useful as an optional local chat surface. It should be available without becoming a dependency of the RAG harness.

### Docs-only Scaffold

Rejected because v0 should prove a thin runnable path, not only describe one. The repo should support ingestion, retrieval, prompt assembly, and provider wiring.

### Conda/Mamba Default Environment

Rejected because `uv` is lighter, lockable, and better aligned with a clean Python application repo. Conda/Mamba can be documented later for isolated ML experiments if needed.

## Follow-up Work

- Add a real local embedding provider when the deterministic provider is no longer enough.
- Add smoke/integration docs for Ollama and LM Studio.
- Add vllm-metal research only after the v0 harness is stable.
- Document any future cloud deployment profile in a separate ADR before implementation.
