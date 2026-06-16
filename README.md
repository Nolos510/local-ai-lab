# local-ai-lab / AI Lab OS

`local-ai-lab` is a local-first Apple Silicon AI engineering lab for private
local inference, local RAG, model/provider experimentation, evaluation,
benchmarking, and decision tracking.

AI Lab OS is the product loop inside the repo: approve a radar candidate, run a
local benchmark, capture responses, score and confirm results, import them into
the dashboard, compare models, and make a keep/watchlist/retest/skip decision.

The target machine is an Apple Silicon Mac Studio with 256 GB unified memory,
large local storage, and a local-first operating model.

## Current Product Lines

### Local RAG Backbone + Provider Harness

```text
CLI / FastAPI
  -> ingestion
  -> chunking
  -> Qdrant retrieval
  -> prompt assembly
  -> local model provider
  -> answer + citations
```

This lane provides the local app scaffold, provider abstractions, CLI, FastAPI
entry point, deterministic test providers, Qdrant integration, and doctor
checks.

### AI Lab OS Dashboard Loop

```text
radar candidate
  -> benchmark artifact
  -> raw responses
  -> draft/confirmed scores
  -> dashboard import
  -> compare models
  -> decision
```

This lane provides the local model dashboard, candidate registry, project
radar, benchmark harness, scoring artifacts, and lab workflow views.

Open WebUI remains the optional local chat UI. LM Studio and Ollama remain
native macOS model runtimes.

## Repository Map

```text
src/local_ai_lab/              Local RAG/provider/API core
apps/model-dashboard/          AI Lab OS dashboard
automations/ai-lab-radar/      Radar inputs, reports, and guardrails
evals/local-llm-benchmark/     Repeatable local LLM benchmark suite
data/model_registry/           Approved model candidate registry
data/project_registry/         GitHub/project opportunity registry
data/eval_results/             Sanitized benchmark artifacts and CSV imports
docs/                          Architecture, roadmap, lab notes, evidence
reports/                       Benchmark/eval/postmortem outputs
infra/                         Qdrant/Open WebUI compose assets
tests/                         Local RAG/provider app tests
scripts/                       Smoke checks and utility scripts
```

## Local-First Architecture

Docker is used only for local infrastructure services in v0:

- Qdrant
- optional Open WebUI

Model runtimes stay native on macOS:

- Ollama
- LM Studio OpenAI-compatible server
- MLX / MLX-LM
- llama.cpp

Open WebUI is optional and parallel. The FastAPI RAG harness must not depend on
Open WebUI.

## Python Environment

The default project workflow uses:

- `uv`
- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `.env.example`

Do not introduce Conda/Mamba or a primary `requirements.txt` workflow.

For dashboard-only work, the dashboard still runs with Python stdlib modules;
developer validation can use `python3 -m unittest` and the smoke script without
starting Qdrant or a model runtime.

## RAG App Quick Start

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

Semantic local embeddings can be enabled through Ollama after installing the
configured embedding model:

```bash
ollama pull bge-m3
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3 \
LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \
uv run local-ai-lab doctor
```

Qdrant collection vector size is fixed at creation time. Changing embedding
provider, model, or vector size requires recreating the collection and
reingesting documents; see `docs/rag.md`.

Live local-model checks:

```bash
uv run local-ai-lab doctor
uv run local-ai-lab ask "What is this lab for?"
```

The mock provider means "no real LLM call." It does not remove the Qdrant,
retrieval, settings, embedding, or indexed-document dependencies from the ask
path. Live local-model checks may fail if Ollama, LM Studio, Qdrant, or the
configured local model is missing; document the exact reason instead of treating
it as passed.

## LM Studio Setup

LM Studio may run MLX models under the hood, but this app talks to it through
the OpenAI-compatible HTTP API.

1. Start LM Studio.
2. Load the Qwen Coder model, or any other desired local model.
3. Start the LM Studio local server.
4. Confirm the model endpoint:

```bash
curl -s http://localhost:1234/v1/models | uv run python -m json.tool
```

`python3 -m json.tool` also works on macOS if you are not running through
`uv`.

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

## Dashboard Quick Start

From the repository root:

```bash
python3 scripts/model_dashboard_smoke.py
python3 apps/model-dashboard/run_dashboard.py serve --demo
```

Then open:

```text
http://127.0.0.1:8765/lab
```

Useful dashboard pages:

- `/lab` - workflow cockpit
- `/radar` - model candidates
- `/projects` - GitHub project opportunities
- `/compare` - model comparison
- `/cookbook` - Apple Silicon model fit and runtime-readiness guidance
- `/reports` - dashboard report view

The dashboard MVP uses local SQLite/CSV artifacts. It does not download models,
call cloud APIs, or require secrets.

## Benchmark Harness

The local benchmark harness lives under `evals/local-llm-benchmark/`.

Useful checks:

```bash
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 evals/local-llm-benchmark/harness.py list-prompts
```

Benchmark runs should preserve raw responses and evidence notes before any
dashboard import. Draft local-judge scores must remain separate from confirmed
human-approved `scores.json` files. Raw prompts, raw responses, private paths,
machine metadata, and local logs must be reviewed before committing.

## Radar And Project Discovery

Radar has two lanes:

- **Local Radar:** repo-local/user-approved source packets only.
- **External Radar:** on-demand public metadata scan, metadata only.

External Radar must not download models, run models, call model APIs, add API
clients, or register candidates without explicit user approval.

GitHub project opportunities live in `data/project_registry` and are displayed
in the dashboard separately from model candidates and eval scores.

## Odysseus-Inspired Roadmap

Odysseus is used as product inspiration only. No Odysseus source code is copied
into this repository. The extracted ideas are tracked in:

- `docs/product/odysseus-idea-extraction.md`
- `docs/product/ai-lab-os-build-plan.md`
- `docs/adr/0003-ai-lab-os-consolidation.md`

Near-term focus remains the local RAG/provider harness, dashboard/eval loop,
runtime readiness, and privacy-first artifact hygiene. Agent, research,
documents, email/calendar/tasks, memory, and MCP lanes require later ADRs before
implementation.

## Troubleshooting

### Provider Errors

If `uv run local-ai-lab ask "What is this lab for?"` fails at the
model-provider step, start with:

```bash
uv run local-ai-lab doctor
```

For Ollama, confirm the configured model is installed. The default configured
model is `qwen3:14b`; replace it if `LOCAL_AI_LAB_OLLAMA_MODEL` is set
differently.

```bash
ollama list
ollama pull qwen3:14b
```

For LM Studio/OpenAI-compatible mode, confirm the local server is running and
that `LOCAL_AI_LAB_LLM_PROVIDER` is set to the intended provider (`ollama`,
`lm_studio`, `openai_compatible`, or `mock`). Use
`LOCAL_AI_LAB_LLM_PROVIDER=mock` for smoke checks that should avoid real model
calls; it still requires Qdrant, retrieval, and indexed docs.

### zsh Parse Error Near Newline

Problem: `zsh: parse error near '\n'`

Cause: an angle-bracket placeholder was pasted into the shell. zsh treats angle
brackets as redirection syntax.

Fix: use the actual LM Studio model ID and do not include angle bracket
characters.

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

Cause: the default provider is Ollama, and the configured model is not
installed locally.

Fix: either pull the Ollama model:

```bash
ollama pull qwen3:14b
```

Or switch `.env` to LM Studio:

```bash
LOCAL_AI_LAB_LLM_PROVIDER=lm_studio
```

## Privacy-First Assumptions

- No hidden cloud calls.
- No secrets committed.
- `.env.example` contains safe placeholder values only.
- Logs should not dump user documents, prompts, retrieved chunks, API keys, or
  private paths by default.
- Telemetry must be opt-in or disabled by default.
- Local-first behavior is the default unless an ADR explicitly changes that
  direction.
- Benchmark artifacts and dashboard exports are private until sanitized for
  GitHub.

## Roadmap

See `ROADMAP.md`, `docs/roadmap.md`, and `docs/product/ai-lab-os-build-plan.md`
for the staged plan.

## Portfolio And Learning Pack

The v1-facing portfolio package lives in:

- `docs/portfolio-case-study.md`
- `docs/resume-bullets.md`
- `docs/learning-roadmap.md`
- `docs/architecture-v1.md`
- `docs/lab-notes/v1-second-benchmark-queue.md`

Screenshots are stored under `docs/assets/screenshots/`.
