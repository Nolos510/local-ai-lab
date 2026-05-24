# local-ai-lab

`local-ai-lab` is a minimal Apple Silicon local AI engineering lab. It is built for a Mac Studio-style workflow where infrastructure services run in Docker, while model runtimes stay native on macOS.

The v0 path is intentionally thin:

```text
User / CLI uv commands
  -> FastAPI RAG harness native via uv
  -> Qdrant Docker service for vector search
  -> Ollama or LM Studio native macOS endpoint
  -> Answer with citations
```

## What v0 Includes

- FastAPI `/ask` endpoint
- CLI commands for ingestion and question answering
- Markdown/text ingestion
- Basic chunking with source metadata
- Deterministic local embedding provider for reproducible tests and smoke runs
- Qdrant vector indexing and retrieval
- Ollama chat provider
- LM Studio/OpenAI-compatible chat provider
- Docker Compose for Qdrant and Open WebUI
- Starter docs, roadmaps, TODOs, and test coverage

## Requirements

- macOS on Apple Silicon
- [`uv`](https://docs.astral.sh/uv/)
- Docker Desktop or a compatible Docker runtime
- One native local model runtime:
  - Ollama at `http://localhost:11434`, or
  - LM Studio local server at `http://localhost:1234/v1`

## Quick Start

```bash
cd local-ai-lab
cp .env.example .env
uv sync
docker compose up -d qdrant open-webui
```

Start a local model runtime natively:

```bash
# Ollama example
ollama pull qwen3:14b
ollama serve
```

Or start LM Studio's OpenAI-compatible local server and set:

```bash
LOCAL_AI_LAB_LLM_PROVIDER=lm_studio
```

Ingest the sample docs:

```bash
uv run local-ai-lab ingest --path data/sample_docs
```

Ask a question:

```bash
uv run local-ai-lab ask "What is this lab for?"
```

Run the API:

```bash
uv run uvicorn local_ai_lab.api.app:create_app --factory --reload
```

Then call:

```bash
curl -s http://127.0.0.1:8000/ask \
  -H 'content-type: application/json' \
  -d '{"question":"What is this lab for?"}'
```

Open WebUI will be available at [http://localhost:8080](http://localhost:8080).

## Offline Smoke Mode

The app includes a `mock` LLM provider so the retrieval path can be exercised without a local model running:

```bash
LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
```

The mock provider is not a model. It is only a deterministic development aid.

## Verification

```bash
uv sync
docker compose config
uv run ruff check .
uv run pytest
```

## Repository Map

```text
src/local_ai_lab/
  api/            FastAPI app and schemas
  cli/            uv command entrypoint
  config/         settings and environment loading
  embeddings/     embedding provider interfaces
  ingestion/      document loading and chunking
  llms/           Ollama, LM Studio, and mock chat providers
  prompts/        RAG prompt assembly
  rag/            orchestration service
  vectorstores/   Qdrant client wrapper

data/             local corpora and generated data
models/           base models, quantized models, adapters, embedders, rerankers
experiments/      dated experiment runs
reports/          benchmark, eval, and postmortem outputs
docs/             architecture and roadmap notes
```

## Design Principles

- Privacy first: local data stays local by default.
- Reproducible: uv, explicit environment variables, and source metadata.
- Small surface area: v0 avoids agents, graph RAG, voice, MCP, and fine-tuning implementation.
- Native where it matters: MLX, Ollama, LM Studio, and llama.cpp are macOS-native workflows.
- Portable later: API boundaries keep future Docker and cloud deployment plausible.
