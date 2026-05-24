# local-ai-lab

`local-ai-lab` is a local-first Apple Silicon AI engineering lab for local inference, local RAG, local model/provider experimentation, evaluation, benchmarking, reproducible AI systems engineering, and privacy-first workflows.

The target machine is an Apple Silicon Mac Studio with 256 GB unified memory, large local storage, and a local-first operating model.

## v0

Current milestone: **v0: Local RAG Backbone + Provider Harness**.

Target architecture:

```text
CLI / FastAPI
  -> ingestion
  -> chunking
  -> Qdrant retrieval
  -> prompt assembly
  -> local model provider
  -> answer + citations
```

## What v0 Is

- A small local RAG backbone.
- A provider harness for local model endpoints.
- A reproducible Python project using `uv`.
- A Docker-backed local infrastructure setup for Qdrant and optional Open WebUI.
- A foundation for later evaluation, benchmarking, and Apple Silicon runtime experiments.

## What v0 Is Not

- Not an agent framework.
- Not graph RAG.
- Not MCP or browser automation.
- Not a voice assistant.
- Not an auth system.
- Not a frontend app.
- Not a cloud deployment.
- Not a fine-tuning implementation.

## Local-First Architecture

Docker is used only for local infrastructure services in v0:

- Qdrant
- Open WebUI

Model runtimes stay native on macOS:

- Ollama
- LM Studio OpenAI-compatible server
- MLX / MLX-LM
- llama.cpp

Open WebUI is optional and parallel. The FastAPI RAG harness must not depend on Open WebUI.

## Python Environment

The project uses:

- `uv`
- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `.env.example`

Do not introduce Conda/Mamba or a primary `requirements.txt` workflow for v0.

## Expected First-Run Commands

```bash
uv sync
docker compose config
docker compose up -d qdrant
uv run ruff check .
uv run pytest
uv run local-ai-lab doctor
uv run local-ai-lab ingest --path data/sample_docs
uv run local-ai-lab ask "What is this lab for?"
```

Some commands may not exist yet during scaffolding. If a command is missing, document that clearly in PR notes instead of treating it as passed.

## Current Status

- Governance and architecture rules live in `AGENTS.md`.
- Pull request, ownership, and CI defaults live under `.github/`.
- Architecture decisions live under `docs/adr/`.
- The v0 implementation should remain narrow and testable.
- This governance pass does not add app code.

Known command gaps:

- `uv run local-ai-lab doctor` is listed as a required future check, but the command is not implemented yet.
- `uv run local-ai-lab ask "What is this lab for?"` depends on a native local model endpoint by default. If Ollama or LM Studio is not running with the configured model, document the failure instead of claiming the check passed.

## Future Roadmap

See `docs/roadmap.md` for the staged plan.

Near-term direction:

- Stabilize local RAG ingestion and retrieval.
- Add reliable local provider checks for Ollama and LM Studio.
- Add evaluation and benchmark harnesses.
- Add MLX-LM fine-tuning experiments only after v0 is stable.
- Document future cloud portability before implementing it.

## Privacy-First Assumptions

- No hidden cloud calls.
- No secrets committed.
- `.env.example` contains safe placeholder values only.
- Logs should not dump user documents, prompts, retrieved chunks, API keys, or private paths by default.
- Telemetry must be opt-in or disabled by default.
- Local-first behavior is the default unless an ADR explicitly changes that direction.
