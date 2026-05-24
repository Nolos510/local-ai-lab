# Architecture

`local-ai-lab` is a local-first Apple Silicon AI engineering lab. The architecture optimizes for private local workflows, reproducible experiments, and clean future portability.

## Hardware Target

- Apple Silicon Mac Studio.
- 256 GB unified memory.
- Large local storage.
- Local-first and privacy-first workflows.

## v0 Target

v0 is the Local RAG Backbone + Provider Harness.

```text
CLI / FastAPI
  -> ingestion
  -> chunking
  -> Qdrant retrieval
  -> prompt assembly
  -> local model provider
  -> answer + citations
```

## Runtime Boundaries

Docker is used for infrastructure services only:

- Qdrant
- Open WebUI

Native macOS model runtimes:

- Ollama
- LM Studio OpenAI-compatible server
- MLX / MLX-LM
- llama.cpp

Open WebUI is optional and parallel. The FastAPI RAG harness must not depend on Open WebUI.

## Python Boundary

The Python application uses:

- `uv`
- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `.env.example`

The CLI and FastAPI harness stay native through `uv` for v0.

## v0 Constraints

- Keep abstractions simple and testable.
- Avoid framework sprawl.
- Do not add agents, graph RAG, MCP, browser automation, voice, auth, frontend apps, cloud deployment, or fine-tuning implementation yet.
- Document future cloud portability before implementing it.

## Architecture Governance

- `AGENTS.md` is the operating agreement for all agents.
- ADRs in `docs/adr/` record architecture decisions.
- Architecture direction must not change without a new ADR.
