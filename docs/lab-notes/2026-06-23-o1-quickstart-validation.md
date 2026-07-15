# O1 Quickstart Validation

Date: 2026-06-23

Branch/worktree: `codex/onboarding-v1` at
`~/Desktop/ai-lab-os-onboarding-v1`

## Scope

O1 verified the documented new-user quickstart surfaces without changing app or
runtime logic:

- RAG path: `uv sync`, `docker compose config`, `doctor`, sample-doc ingest,
  and mock-provider ask.
- AI Lab OS loop: radar list, benchmark matrix, prepared benchmark artifact,
  dashboard import, report generation, and dashboard serving.

## RAG Path Evidence

Passed:

```text
uv sync
```

Result: created `.venv`, built `local-ai-lab==0.1.0`, and installed 39
packages.

Passed:

```text
docker compose config
```

Result: rendered local Qdrant and Open WebUI services with loopback port binds.

Default live-model doctor was run and did not pass on this machine:

```text
uv run local-ai-lab doctor
```

Observed result:

```text
Qdrant: PASS reachable at http://localhost:6333
Ollama endpoint: PASS reachable at http://localhost:11434
Ollama model: FAIL configured model 'qwen3:14b' is not available locally
```

This is a live local-model prerequisite failure, not a mock smoke-path failure.

The normal Qdrant start command was run:

```text
docker compose up -d qdrant
```

Observed result: failed because a fixed-name `local-ai-lab-qdrant` container was
already running from another local context. The existing container was left
untouched.

Verification of the existing local service:

```text
docker ps --filter name=local-ai-lab-qdrant --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
curl -fsS http://localhost:6333/collections
```

Observed result: the existing container was healthy and Qdrant returned a JSON
collections response.

The original default collection ingest was run:

```text
uv run local-ai-lab ingest --path data/sample_docs
```

Observed result: failed with a Qdrant vector dimension mismatch because the
existing `local_ai_lab_chunks` collection expected 384-dimensional vectors while
the current deterministic default produced 1024-dimensional vectors.

The corrected isolated smoke collection path passed:

```text
curl -fsS -X DELETE http://localhost:6333/collections/local_ai_lab_quickstart_smoke || true
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab doctor
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke uv run local-ai-lab ingest --path data/sample_docs
LOCAL_AI_LAB_QDRANT_COLLECTION=local_ai_lab_quickstart_smoke LOCAL_AI_LAB_LLM_PROVIDER=mock uv run local-ai-lab ask "What is this lab for?"
```

Observed result:

```text
Ingested 1 document(s) into 2 chunk(s).
Mock local answer. A real answer requires Ollama or LM Studio.
Citations:
- README.md#chunk_0 ...
- README.md#chunk_1 ...
```

The mock provider did not call a real LLM. Qdrant, deterministic embeddings,
retrieval, prompt assembly, and citation formatting were still exercised.

## AI Lab OS Loop Evidence

The repeatable metadata-only lab loop passed:

```text
rm -rf /tmp/ai-lab-quickstart-eval /tmp/ai-lab-quickstart-dashboard.sqlite /tmp/ai-lab-quickstart-dashboard-report.md
uv run ai-lab radar list --status ready_for_eval --limit 5
uv run ai-lab bench matrix --limit 5
uv run ai-lab bench run --candidate 20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit --run-id quickstart-qwen3-coder-prep --output-root /tmp/ai-lab-quickstart-eval
uv run ai-lab import --run quickstart-qwen3-coder-prep --eval-results /tmp/ai-lab-quickstart-eval --db /tmp/ai-lab-quickstart-dashboard.sqlite
uv run ai-lab report --db /tmp/ai-lab-quickstart-dashboard.sqlite --out /tmp/ai-lab-quickstart-dashboard-report.md
uv run ai-lab status --eval-results /tmp/ai-lab-quickstart-eval --db /tmp/ai-lab-quickstart-dashboard.sqlite
```

Observed result:

```text
Benchmark artifacts: 1
Dashboard rows: models=1, runs=1, scores=0, decisions=0
```

The dashboard was also launched and probed with the temporary DB:

```text
uv run ai-lab dashboard --db /tmp/ai-lab-quickstart-dashboard.sqlite --port 8767
```

Observed result: `/lab` and `/capability` responded on
`http://127.0.0.1:8767`.

This lab-loop smoke did not execute a benchmark model, capture raw model
responses, create scores, or create decisions. It proves only the local
metadata/import/dashboard operating surface.

