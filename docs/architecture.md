# v0 Architecture

The v0 architecture is a thin vertical slice for a local AI application backend.

```text
Open WebUI Docker service
          |
          | HTTP
          v
User / CLI uv commands -> FastAPI RAG harness native via uv -> Ollama / LM Studio native macOS
                               |
                               | vector search
                               v
                       Qdrant Docker service
```

## Runtime Boundaries

- Docker: Qdrant and Open WebUI.
- Native macOS: FastAPI, CLI, uv, Ollama, LM Studio, MLX-LM, llama.cpp.
- Python package: ingestion, chunking, embeddings, retrieval, prompt assembly, and provider clients.

## v0 Request Flow

1. A user asks a question through the CLI or FastAPI.
2. The question is embedded with the configured embedding provider.
3. Qdrant retrieves the nearest chunks.
4. The prompt builder assembles the question plus retrieved context.
5. Ollama or LM Studio generates the answer.
6. The service returns the answer, citations, and retrieved chunk metadata.

## Non-Goals

- No multi-agent workflows.
- No graph RAG.
- No custom frontend.
- No voice pipeline.
- No MCP/browser automation.
- No real fine-tuning implementation in v0.
