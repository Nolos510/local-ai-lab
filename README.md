# local-ai-lab / AI Lab OS

`local-ai-lab` is a local-first Apple Silicon AI engineering lab for private
local inference, local RAG, model/provider experimentation, evaluation,
benchmarking, and decision tracking.

AI Lab OS is the product loop inside the repo: approve a radar candidate, run a
local benchmark, capture responses, score and confirm results, import them into
the dashboard, compare models, and make a keep/watchlist/retest/skip decision.

The target machine is an Apple Silicon Mac Studio with 256 GB unified memory,
large local storage, and a local-first operating model.

## Start Here

New operators should start with [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md).
It provides a five-minute no-model path, the full local RAG and benchmark paths,
and the dashboard `--enable-*` action flags with their safety boundaries.

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

## Repository Map

```text
apps/model-dashboard/          Local model performance dashboard
src/local_ai_lab/              Local RAG/provider app
automations/ai-lab-radar/      Radar inputs, reports, and guardrails
evals/local-llm-benchmark/     Personal local LLM benchmark suite
evals/rag-retrieval/           Offline RAG retrieval quality fixtures and scorer
data/model_registry/           Approved model candidate registry
data/project_registry/         GitHub/project opportunity registry
data/eval_results/             Benchmark artifacts and dashboard CSV exports
skills/                        Reusable AI workflow skills
docs/                          Architecture, roadmap, lab notes, evidence
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

Local RAG smoke checks requiring Qdrant and indexed docs, but not a real model.
The smoke path uses an isolated Qdrant collection so it does not mutate an
existing personal RAG index:

```bash
docker compose up -d qdrant
curl -fsS -X DELETE http://localhost:6333/collections/local_ai_lab_quickstart_smoke || true
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab doctor
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke uv run local-ai-lab ingest --path data/sample_docs
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
```

If `docker compose up -d qdrant` reports that `local-ai-lab-qdrant` is already
in use, another checkout or previous run already owns the fixed local container
name. Do not remove an unknown container just to continue onboarding. First
verify the existing loopback service:

```bash
curl -fsS http://localhost:6333/collections
```

Continue the mock smoke path only when Qdrant is reachable. If ingest reports a
Qdrant vector dimension mismatch, the target collection was created with a
different embedding vector size. Use the quickstart smoke collection above, or
delete/recreate only the collection you intentionally want to rebuild.

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

If the configured Ollama model is not installed, `doctor` prints a concrete
replacement such as `LOCAL_AI_LAB_OLLAMA_MODEL=<installed-model>` from local
inventory when one is available. If no Ollama models are installed, it prints
the exact `ollama pull <configured-model>` command for the configured model.

The mock provider means "no real LLM call." It does not remove the Qdrant,
retrieval, settings, embedding, or indexed-document dependencies from the ask
path. Live local-model checks may fail if Ollama, LM Studio, Qdrant, or the
configured local model is missing; document the exact reason instead of treating
it as passed.

The `/ask` response intentionally returns an answer plus citation identifiers
only. It does not include raw retrieved chunks, chunk previews, or private source
paths by default; see `docs/adr/0003-privacy-narrow-ask-response.md`.

Offline retrieval quality checks live under `evals/rag-retrieval/` and compute
`recall@k` plus `MRR` against a tiny labeled fixture set:

```bash
python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/fixtures/labels.json \
  --results evals/rag-retrieval/fixtures/deterministic-results.jsonl \
  --k 2
```

This scorer is local and stdlib-only. It does not call Qdrant, Ollama, model
providers, cloud APIs, or network services.

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
- `/reports` - dashboard report view

The dashboard MVP uses local SQLite/CSV artifacts. It does not download models,
call cloud APIs, or require secrets.

## AI Lab OS CLI

The unified local workflow CLI is available as `ai-lab`. These read-only
commands inspect repo-local state and sanitized local runtime context:

```bash
uv run ai-lab status
uv run ai-lab hardware snapshot
uv run ai-lab radar list --status ready_for_eval --limit 5
uv run ai-lab bench matrix --limit 5
```

`ai-lab status` and `ai-lab radar list` read local CSV/SQLite/artifact state.
`ai-lab bench matrix` reads the candidate registry and prints an auditable
benchmark queue without running models, inspecting private model folders, or
initializing artifacts.

Discover graduation is derived live from imported dashboard runs: a radar
candidate leaves the default Discover view after its linked run has a confirmed
score or a logged decision, while the **Evaluated** filter keeps it reachable.
Public upstream metadata checks are a separate, explicit opt-in action:

```bash
uv run ai-lab radar check-updates --lookup
```

Without `--lookup`, `radar check-updates` performs no network request and does
not read or write upstream state. With the flag, it reads public Hugging Face or
GitHub revision/date metadata only—no tokens, model APIs, or downloads—and
writes the ignored local state file
`data/dashboard/radar_upstream_state.json`. The dashboard itself never performs
these lookups; it only reads that local file to re-surface evaluated candidates
whose upstream revision changed.

Action commands dispatch to the existing benchmark harness and dashboard
entrypoints. They do not download models or call model/cloud APIs implicitly.
Use the repeatable `/tmp` smoke sequence below for a pasteable prepared-artifact
import path.

`ai-lab bench execute` is the sanctioned local execution wrapper. It refuses to
run unless the operator supplies an explicit candidate, exact local model id,
runner, run id, and approval flag. Without approval it stops before any harness,
subprocess, endpoint, import, or score export occurs. Live model execution should
be run only after confirming the exact local model id and runtime.

`ai-lab bench queue` applies that same execution flow sequentially to two or
more `ready_for_eval` candidates. Repeat `--candidate` to choose an exact
subset, or omit it to select every ready candidate. Before any run, the command
prints the complete candidate/model-id/runner/run-id batch and requires one
`--i-approve-local-run` flag scoped only to that enumeration. A missing or
unsupported runner, missing exact local model id, invalid run id, or missing
required local endpoint blocks the entire batch. Individual run failures do not
stop later candidates; the final table reports status and any captured latency
and tokens/sec.

`ai-lab hardware snapshot` prints sanitized local hardware/runtime context as
JSON. Use `--out docs/lab-notes/<name>.json` to write a repo-local copy for
benchmark evidence. It does not include usernames, home directories,
environment variables, model inventory, prompts, documents, or secrets.

For a repeatable no-model lab-loop smoke run that writes only to `/tmp`, use:

```bash
rm -rf /tmp/ai-lab-quickstart-eval /tmp/ai-lab-quickstart-dashboard.sqlite /tmp/ai-lab-quickstart-dashboard-report.md
uv run ai-lab radar list --status ready_for_eval --limit 5
uv run ai-lab bench matrix --limit 5
uv run ai-lab bench run --candidate 20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit --run-id quickstart-qwen3-coder-prep --output-root /tmp/ai-lab-quickstart-eval
uv run ai-lab import --run quickstart-qwen3-coder-prep --eval-results /tmp/ai-lab-quickstart-eval --db /tmp/ai-lab-quickstart-dashboard.sqlite
uv run ai-lab report --db /tmp/ai-lab-quickstart-dashboard.sqlite --out /tmp/ai-lab-quickstart-dashboard-report.md
uv run ai-lab status --eval-results /tmp/ai-lab-quickstart-eval --db /tmp/ai-lab-quickstart-dashboard.sqlite
uv run ai-lab dashboard --db /tmp/ai-lab-quickstart-dashboard.sqlite --port 8767
```

This prepares a benchmark artifact and imports dashboard-compatible model/run
metadata only. It does not execute a model, capture raw benchmark responses,
create scores, or create decisions. The expected status after import is one
artifact, one model row, one run row, zero score rows, and zero decision rows.
Stop the dashboard with `Ctrl-C` when finished.

## Benchmark Harness

The local benchmark harness lives under `evals/local-llm-benchmark/`.

Useful checks:

```bash
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 evals/local-llm-benchmark/harness.py list-prompts
```

Benchmark runs should preserve raw responses and evidence notes before any
dashboard import. Draft local-judge scores must remain separate from confirmed
human-approved `scores.json` files.

## Radar And Project Discovery

Radar has two lanes:

- **Local Radar:** repo-local/user-approved source packets only.
- **External Radar:** on-demand public metadata scan, metadata only.

External Radar must not download models, run models, call model APIs, add API
clients, or register candidates without explicit user approval.

GitHub project opportunities live in `data/project_registry` and are displayed
in the dashboard separately from model candidates and eval scores.

## Privacy-First Assumptions

- No hidden cloud calls.
- No secrets committed.
- `.env.example` contains safe placeholder values only.
- Logs should not dump user documents, prompts, retrieved chunks, API keys, or
  private paths by default.
- API responses should not expose raw retrieved chunks, chunk previews, or
  private source paths unless a future explicit diagnostic workflow is approved.
- Telemetry must be opt-in or disabled by default.
- Local-first behavior is the default unless an ADR explicitly changes that
  direction.

## Roadmap

See `ROADMAP.md` for the canonical staged plan. `docs/roadmap.md` is a
compatibility pointer.

## Portfolio And Learning Pack

The v1-facing portfolio package lives in:

- `docs/portfolio-case-study.md`
- `docs/resume-bullets.md`
- `docs/learning-roadmap.md`
- `docs/architecture.md`
- `docs/lab-notes/v1-second-benchmark-queue.md`

Screenshots are stored under `docs/assets/screenshots/`.
