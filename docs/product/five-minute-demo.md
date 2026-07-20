# Five-Minute Local Demo

This path demonstrates the dashboard's evaluation and portfolio workflow with
bundled fixture records. It does not contact a model server, start Docker, or
modify the normal dashboard database.

## Offline Fixture Path

From the repository root:

```bash
uv sync
DEMO_DIR="$(mktemp -d)"
python3 apps/model-dashboard/run_dashboard.py init-db \
  --db "$DEMO_DIR/model_dashboard.sqlite" \
  --reset \
  --with-fixtures
python3 apps/model-dashboard/run_dashboard.py serve \
  --db "$DEMO_DIR/model_dashboard.sqlite" \
  --host 127.0.0.1 \
  --port 8766
```

Open `http://127.0.0.1:8766/demo` to inspect the bundled examples, then use
Home, Benchmark, Compare, My Models, and Export Report. Fixture rows are visibly
marked and remain excluded from real-data recommendations.

Generate a local report from the same disposable database:

```bash
python3 apps/model-dashboard/run_dashboard.py report \
  --db "$DEMO_DIR/model_dashboard.sqlite" \
  --out "$DEMO_DIR/model-report.md" \
  --include-demo
```

Stop the server with `Ctrl-C`. The command prints the temporary directory so it
can be inspected or removed later.

## Full Local-Runtime Path

The trusted live path has more prerequisites because it uses real local
evidence:

```bash
docker compose up -d qdrant
lms server start --port 1234 --bind 127.0.0.1
LOCAL_AI_LAB_LLM_PROVIDER=lm_studio \
LOCAL_AI_LAB_LM_STUDIO_MODEL="paste-model-id-here" \
uv run local-ai-lab doctor
uv run local-ai-lab ingest --path data/sample_docs
```

Confirm the exact judge and reviewer IDs first:

```bash
curl -s http://127.0.0.1:1234/v1/models | uv run python -m json.tool
```

Then start the operational dashboard with two different loaded local models:

```bash
python3 apps/model-dashboard/run_dashboard.py serve \
  --host 127.0.0.1 \
  --port 8765 \
  --enable-run-tests \
  --enable-import-actions \
  --enable-delete-actions \
  --enable-score-actions \
  --judge-endpoint http://127.0.0.1:1234/v1 \
  --judge-model "paste-primary-model-id-here" \
  --reviewer-endpoint http://127.0.0.1:1234/v1 \
  --reviewer-model "paste-different-reviewer-model-id-here"
```

Do not include angle brackets in model IDs. The Local Readiness panel must show
the required checks as ready before starting benchmark or scoring work. A model
review remains a draft until the human owner confirms, edits, rejects, or
retires it.

## Demo Truth Boundary

- Fixture scores demonstrate navigation and report shape, not model quality.
- The offline path never proves runtime compatibility or Apple Silicon speed.
- Real recommendations require captured artifacts, independent review, explicit
  confirmation, and complete performance evidence.
