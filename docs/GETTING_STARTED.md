# Getting Started

This guide is the fastest path from a fresh checkout to a working local AI Lab
OS loop. It separates no-model smoke checks from full local model execution so
new operators do not accidentally turn candidate metadata into benchmark
evidence.

In this document, "offline" means no cloud API calls, no model downloads, and no
local model execution. A fresh Python environment may still need `uv` to install
packages from the lockfile unless those packages are already cached.

## Prerequisites

- macOS on Apple Silicon.
- `uv` for the Python project workflow.
- Docker Desktop or another Docker Compose-compatible local Docker engine for
  Qdrant.
- Optional local model runtime for live checks: Ollama, LM Studio, MLX/MLX-LM,
  or llama.cpp.

No API keys are required for the no-model path.

## Five-Minute No-Model Path

Run this from the repository root. It verifies package setup, local Compose
configuration, candidate registry reads, benchmark planning, prepared artifact
creation, dashboard CSV import, report generation, and dashboard serving. It
does not run a model, call a model endpoint, download a model, create scores, or
create decisions.

```bash
uv sync
docker compose config
uv run ai-lab status
uv run ai-lab radar list --status ready_for_eval --limit 5
uv run ai-lab bench matrix --limit 5
rm -rf /tmp/ai-lab-quickstart-eval /tmp/ai-lab-quickstart-dashboard.sqlite /tmp/ai-lab-quickstart-dashboard-report.md
uv run ai-lab bench run --candidate 20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit --run-id quickstart-qwen3-coder-prep --output-root /tmp/ai-lab-quickstart-eval
uv run ai-lab import --run quickstart-qwen3-coder-prep --eval-results /tmp/ai-lab-quickstart-eval --db /tmp/ai-lab-quickstart-dashboard.sqlite
uv run ai-lab report --db /tmp/ai-lab-quickstart-dashboard.sqlite --out /tmp/ai-lab-quickstart-dashboard-report.md
uv run ai-lab status --eval-results /tmp/ai-lab-quickstart-eval --db /tmp/ai-lab-quickstart-dashboard.sqlite
uv run ai-lab dashboard --db /tmp/ai-lab-quickstart-dashboard.sqlite --port 8767
```

Open `http://127.0.0.1:8767/lab`, then stop the server with `Ctrl-C` when
finished.

Expected imported state after the `/tmp` import:

```text
Benchmark artifacts: 1
Dashboard rows: models=1, runs=1, scores=0, decisions=0
```

Those rows are prepared metadata only. They are useful for onboarding and UI
validation, but they are not scored benchmark evidence.

## No-Model RAG Smoke

The RAG smoke path still requires Qdrant because it verifies indexing,
retrieval, prompt assembly, and citations. It uses deterministic embeddings and
the mock chat provider, so it does not call Ollama, LM Studio, or any other LLM.

Use an isolated smoke collection so sample-doc ingestion does not overwrite or
conflict with an existing personal collection:

```bash
docker compose up -d qdrant
curl -fsS -X DELETE http://localhost:6333/collections/local_ai_lab_quickstart_smoke || true
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab doctor
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke uv run local-ai-lab ingest --path data/sample_docs
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
```

If `docker compose up -d qdrant` reports that `local-ai-lab-qdrant` is already
in use, do not remove an unknown container. Verify the existing loopback service
first:

```bash
curl -fsS http://localhost:6333/collections
```

If ingest reports a vector dimension mismatch, the target Qdrant collection was
created with a different vector size. Use a new collection name for smoke work,
or delete only the collection you intentionally want to rebuild.

## Full Local RAG Path

After the no-model smoke passes, run a real local model only after the local
runtime and model identity are explicit.

For the default Ollama path:

```bash
docker compose up -d qdrant
ollama list
LOCAL_AI_LAB_OLLAMA_MODEL=<installed-ollama-model> uv run local-ai-lab doctor
LOCAL_AI_LAB_OLLAMA_MODEL=<installed-ollama-model> uv run local-ai-lab ask "What is this lab for?"
```

If no suitable Ollama model is installed, `doctor` prints the configured pull
command. Do not treat a missing local model as a passed live check.

For LM Studio or another loopback OpenAI-compatible local server:

```bash
LOCAL_AI_LAB_LLM_PROVIDER=lm_studio \
LOCAL_AI_LAB_LM_STUDIO_BASE_URL=http://localhost:1234/v1 \
LOCAL_AI_LAB_LM_STUDIO_MODEL=<exact-local-model-id> \
uv run local-ai-lab doctor

LOCAL_AI_LAB_LLM_PROVIDER=lm_studio \
LOCAL_AI_LAB_LM_STUDIO_BASE_URL=http://localhost:1234/v1 \
LOCAL_AI_LAB_LM_STUDIO_MODEL=<exact-local-model-id> \
uv run local-ai-lab ask "What is this lab for?"
```

The service URL must be localhost or a loopback IP. The `/ask` response returns
answer text and citation identifiers only; it does not expose raw retrieved
chunks or private source paths by default.

## Full Local Benchmark Path

Benchmark evidence starts with the matrix and an explicit local model identity.
Radar candidates are not scores.

1. Review the queue:

```bash
uv run ai-lab radar list --status ready_for_eval
uv run ai-lab bench matrix --limit 10
```

2. Prepare an artifact without running a model:

```bash
uv run ai-lab bench run --candidate <candidate_id> --run-id <benchmark_run_id>
```

3. Execute only after confirming the exact local model id, runner, and safety
   gate:

```bash
uv run ai-lab bench execute \
  --candidate <candidate_id> \
  --model-id <exact_local_model_id> \
  --runner lmstudio-cli \
  --run-id <benchmark_run_id> \
  --i-approve-local-run
```

For a loopback OpenAI-compatible local endpoint, add the endpoint and use the
matching runner:

```bash
uv run ai-lab bench execute \
  --candidate <candidate_id> \
  --model-id <exact_local_model_id> \
  --runner openai-compatible \
  --endpoint http://127.0.0.1:1234/v1 \
  --run-id <benchmark_run_id> \
  --i-approve-local-run
```

4. Import only benchmark artifacts that have the expected
   `dashboard-import/*.csv` files:

```bash
uv run ai-lab import --run <benchmark_run_id>
uv run ai-lab report
```

Confirmed scores and decisions must come from reviewed benchmark evidence, not
from candidate metadata, runtime inventory, or demo fixture rows.

## Dashboard Operating Surface

The dashboard is local-first and read-only by default. It reads local CSV,
SQLite, JSON, and artifact files. It does not download models, call cloud APIs,
or require secrets.

Start the normal local dashboard:

```bash
uv run ai-lab dashboard --port 8765
```

Use `--demo` only when you want bundled fixture rows for UI review:

```bash
uv run ai-lab dashboard --demo --port 8765
```

Normal dashboard pages hide bundled demo rows from real rankings and comparisons
so they are not mistaken for benchmark evidence.

Action flags are disabled unless explicitly supplied:

| Flag | Available through | What it enables | Safety posture |
| --- | --- | --- | --- |
| `--enable-run-tests` | `uv run ai-lab dashboard`, `python3 apps/model-dashboard/run_dashboard.py serve` | Local run-test buttons for candidates that already have exact `local_runner` and `local_model_id` metadata. | Creates/captures benchmark artifacts only. It does not download models, create scores, import CSVs, or make decisions. |
| `--enable-import-actions` | `uv run ai-lab dashboard`, `python3 apps/model-dashboard/run_dashboard.py serve` | Local artifact import buttons for existing `dashboard-import/*.csv` files. | Writes to the selected local SQLite DB only from existing artifact CSV files. |
| `--enable-delete-actions` | `uv run ai-lab dashboard`, `python3 apps/model-dashboard/run_dashboard.py serve` | Two-step local model removal actions for detected inventory rows. | Disabled by default; use only after reviewing the exact detected runtime entry and local removal behavior. |

The direct dashboard script also exposes timeout tuning:

```bash
python3 apps/model-dashboard/run_dashboard.py serve \
  --run-test-timeout 3600 \
  --inventory-timeout 5
```

Inventory refresh is manual and checks local runtimes with short timeouts:

- `lms ls --json`
- `lms ps --json`
- `ollama list`

Inventory is runtime state, not benchmark evidence. A model being installed or
loaded does not mean it has been scored, imported, or approved for a keep/watch
decision.

## Validation Gate

Run these before committing onboarding, dashboard, benchmark, or release docs:

```bash
uv sync
docker compose config
uv run ruff check .
uv run pytest
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
```

Do not claim a live local-model check passed unless `uv run local-ai-lab doctor`
and the relevant `ask` or benchmark command actually ran against the intended
local model.

