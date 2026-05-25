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

Always-runnable local/code checks:

```bash
uv sync
docker compose config
uv run ruff check .
uv run pytest
```

Local RAG smoke checks requiring Qdrant and indexed docs, but not a real model:

```bash
docker compose up -d qdrant
uv run local-ai-lab ingest --path data/sample_docs
LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
```

Live local-model checks:

```bash
uv run local-ai-lab doctor
uv run local-ai-lab ask "What is this lab for?"
```

The mock provider means "no real LLM call." It does not mean "no Qdrant/retrieval dependency." The mock ask path still requires settings to load, deterministic embeddings to run, Qdrant to be reachable, and sample documents/chunks to be indexed.

Live local-model checks may fail if Ollama, LM Studio, or the configured local model is missing. Document those failures honestly instead of treating the commands as passed.

## Health Checks

Run the local v0 stack health check with:

```bash
uv run local-ai-lab doctor
```

The command validates package and settings loading, required data directories, `data/sample_docs`, `compose.yaml`, the configured embedding and vector-store providers, Qdrant reachability, and the selected model-provider endpoint. Provider checks for non-selected runtimes are reported as warnings and do not fail the command. Selected provider failures and Qdrant failures return a nonzero exit code.

If Ollama is selected, `doctor` also verifies that the configured Ollama model is available locally. It exits nonzero when Ollama is reachable but the configured model is missing; that means the runtime is up, but the local model inventory does not match configuration.

If LM Studio or another OpenAI-compatible provider is selected, `doctor` verifies both the `/models` endpoint and the configured `LOCAL_AI_LAB_LM_STUDIO_MODEL` value. It exits nonzero when the server is reachable but the configured model ID is not in the returned model list.

Local RAG smoke path without a real LLM call:

```bash
docker compose up -d qdrant
uv run local-ai-lab ingest --path data/sample_docs
LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
```

Real Ollama smoke path:

```bash
ollama pull qwen3:14b
docker compose up -d qdrant
uv run local-ai-lab doctor
uv run local-ai-lab ingest --path data/sample_docs
uv run local-ai-lab ask "What is this lab for?"
```

## LM Studio Setup

LM Studio may run MLX models under the hood, but this app talks to it through the OpenAI-compatible HTTP API.

1. Start LM Studio.
2. Load the Qwen Coder model, or any other desired local model.
3. Start the LM Studio local server.
4. Confirm the model endpoint:

```bash
curl -s http://localhost:1234/v1/models | uv run python -m json.tool
```

`python3 -m json.tool` also works on macOS if you are not running through `uv`.

5. Copy one of the returned `id` values.
6. Edit `.env`:

```bash
LOCAL_AI_LAB_LLM_PROVIDER=lm_studio
LOCAL_AI_LAB_LM_STUDIO_BASE_URL=http://localhost:1234/v1
LOCAL_AI_LAB_LM_STUDIO_MODEL="paste-model-id-here"
```

Do not include angle bracket characters in shell commands or `.env` values.

7. Run:

```bash
uv run local-ai-lab doctor
uv run local-ai-lab ask "What is this lab for?"
```

More runtime setup notes live in `docs/runtime-profiles.md`.

## Current Status

- Governance and architecture rules live in `AGENTS.md`.
- Pull request, ownership, and CI defaults live under `.github/`.
- Architecture decisions live under `docs/adr/`.
- The v0 implementation should remain narrow and testable.
- This governance branch does not introduce additional app code; it documents and constrains the v0 app scaffold that already exists in the repository.

Known command gaps:

- `uv run local-ai-lab ask "What is this lab for?"` depends on a native local model endpoint by default. If Ollama or LM Studio is not running with the configured model, document the failure instead of claiming the check passed.

## Troubleshooting

### Provider Errors

If `uv run local-ai-lab ask "What is this lab for?"` fails at the model-provider step, start with:

```bash
uv run local-ai-lab doctor
```

For Ollama, confirm the configured model is installed. The default configured model is `qwen3:14b`; replace it if `LOCAL_AI_LAB_OLLAMA_MODEL` is set differently.

```bash
ollama list
ollama pull qwen3:14b
```

For LM Studio/OpenAI-compatible mode, confirm the local server is running and that `LOCAL_AI_LAB_LLM_PROVIDER` is set to the intended provider (`ollama`, `lm_studio`, `openai_compatible`, or `mock`). Use `LOCAL_AI_LAB_LLM_PROVIDER=mock` for smoke checks that should avoid real model calls; it still requires Qdrant, retrieval, and indexed docs.

### zsh Parse Error Near Newline

Problem: `zsh: parse error near '\n'`

Cause: an angle-bracket placeholder was pasted into the shell. zsh treats angle brackets as redirection syntax.

Fix: use the actual LM Studio model ID and do not include angle bracket characters.

```bash
LOCAL_AI_LAB_LM_STUDIO_MODEL="paste-model-id-here"
```

### Python Command Not Found

Problem: `zsh: command not found: python`

Cause: macOS may not expose bare `python`.

Fix: use `uv run python` from this repo, or use `python3` on macOS.

```bash
curl -s http://localhost:1234/v1/models | uv run python -m json.tool
```

### Default Ollama Model Missing

Problem: `doctor` fails on Ollama model `qwen3:14b`.

Cause: the default provider is Ollama, and the configured model is not installed locally.

Fix: either pull the Ollama model:

```bash
ollama pull qwen3:14b
```

Or switch `.env` to LM Studio:

```bash
LOCAL_AI_LAB_LLM_PROVIDER=lm_studio
```

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
