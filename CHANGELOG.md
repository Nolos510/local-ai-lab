# Changelog

## v1.1.0 - 2026-07-14

Release evidence: approved 2-model benchmark batch executed 2026-07-14 via
`ai-lab bench queue` and imported into the dashboard —
Qwen3-Coder-30B-A3B (lmstudio-cli, `20260714-qwen3-coder-30b-a3b-lmstudio-cli-r3`):
75.38 tok/s, 54.99 s total latency, 194.7 GB peak RAM; Dolphin-Mistral-24B
Venice (`20260714-dolphin-mistral-24b-venice-edition-r3`): 33.94 tok/s,
108.78 s, 193.3 GB. Full validation gate green at release (pytest 275 passed,
dashboard/harness unittest OK, smoke OK, ruff clean).

This candidate turns more of the repo's existing local evidence into direct,
auditable answers. It does not create a `v1.1.0` tag and does not expand the
project beyond its local-first runtime boundaries.

### Answers Sprint

- Added a dependency-free Fit Advisor to Home, Discover, and My Models. It
  labels model-memory results as estimates, returns `unknown` when parameter or
  quantization metadata is missing, and shows observed tokens/sec only when an
  imported benchmark run provides it. The estimate uses parameter count and
  quantization bits with a 10% weight allowance, an 8 GB context/runtime
  allowance, and a 16 GB system reserve.
- Added Home and Benchmark task-leader panels for Coding, Reasoning & agents,
  Research & writing, Long context, and Fast & practical. Leaders use confirmed
  eval rows only, keep exact ties visible, ignore draft scores, and expose an
  honest single-model state. The repository currently has confirmed scored
  evidence for only two unique models, so these leaders are not broad market
  recommendations.
- Added `ai-lab bench queue` for an explicitly enumerated batch of at least two
  `ready_for_eval` candidates. The command prints every candidate, exact local
  model id, runner, and run id before one batch-scoped approval; refuses the
  entire batch when required metadata is invalid or missing; continues after an
  individual run failure; and prints a final status/runtime summary.

### Dashboard Experience

- Restructured the dashboard from 11 primary navigation destinations to four
  workflow surfaces: Home, Discover, My Models, and Benchmark. Existing detail
  routes remain reachable, while reports are presented as an export action.
- Polished the dependency-light Midnight Neon interface across the consolidated
  views, including responsive layout, clearer section rhythm, local inventory
  matching, table/chart overflow handling, metric explainers, offline icons,
  and inline-only client behavior with no external dashboard assets.

### Retrieval, Benchmarking, And Experiment Scaffolds

- Recorded the RAG v2 real-corpus retrieval run using local BGE-M3 embeddings:
  `recall@5 = 1.0` and `MRR = 1.0`. This result covers only four queries in the
  tiny repo-docs v0.1 corpus; it verifies the local eval path but is not evidence
  of general retrieval quality.
- Added v3 benchmark `runtime-metrics.json` artifacts and sanitized Markdown
  report rendering for captured prompt/error counts, latency, tokens, observed
  RAM high-water, and macOS memory/swap counters when available. Missing
  measurements remain null rather than inferred.
- Added the v4 offline MLX-LM LoRA experiment scaffold: dataset manifest and
  adapter registry conventions, command and before/after eval templates, and a
  stdlib metadata validator. No fine-tuning, model download, install, or private
  dataset processing was performed.

### Confirmed Benchmark Evidence Baseline

- The v1.1 candidate's task-leader views build on the second unique confirmed
  benchmark model recorded on 2026-06-25:
  Dolphin-Mistral-24B-Venice-Edition, exact local LM Studio CLI id
  `dolphin-mistral-24b-venice-edition`. The official 12-prompt run completed
  without runtime errors and was confirmed at `65.45` with a `WATCHLIST`
  label. Together with Qwen3 Coder, this brings the locally evidenced comparison
  set to two unique scored models.

## v1.0.0 - 2026-06-25

AI Lab OS v1.0.0 is the tagged local-first product-loop release. The annotated
tag points to commit `73732a5`, which includes the Qwen3 Coder baseline and the
2026-06-25 Dolphin-Mistral 24B validation evidence, plus the local loop around
radar candidates, benchmark artifacts, dashboard import, and operator decisions.

### Shipped

- Local RAG/provider backbone with CLI and FastAPI entry points, deterministic
  test providers, Qdrant retrieval, prompt assembly, local provider boundaries,
  and privacy-narrow answer/citation responses.
- Local model dashboard with SQLite/CSV import/export, fixture isolation,
  lab/radar/projects/runs/models/compare/reports/capability/inventory views,
  inline SVG charts, offline icons, and stdlib smoke coverage.
- Unified `ai-lab` CLI for local status, sanitized hardware snapshots, radar
  listing, read-only benchmark matrix planning, benchmark artifact prep,
  dashboard import/report, and dashboard launch.
- Approval-gated benchmark execution through `ai-lab bench execute`, requiring
  explicit candidate id, exact local model id, runner, run id, and approval flag
  before any local subprocess, model endpoint call, import, or score export.
- Onboarding docs for a five-minute no-model path, full local RAG path,
  metadata-only lab-loop smoke path, and dashboard action flag safety posture.
- Security/privacy posture: no hidden cloud calls, no model downloads from
  radar or dashboard planning, no secrets, loopback-only local service URLs,
  candidate records kept separate from eval scores, raw retrieved chunks not
  returned by default, dashboard action buttons disabled unless explicitly
  enabled.
- A second unique confirmed benchmark for Dolphin-Mistral-24B-Venice-Edition,
  captured through exact local LM Studio CLI identity, imported into the
  dashboard, and retained as a watchlist result.

### Validation Evidence

The following local O3 gate was run on `codex/onboarding-v1` after bumping the
project version to `1.0.0`. It is release-prep evidence from before the final
Dolphin benchmark commit; final tag-state evidence is recorded in
`docs/lab-notes/v1-validation-evidence.md`.

```text
$ uv sync
Resolved 41 packages in 3ms
Checked 39 packages in 1ms

$ docker compose config
name: ai-lab-os-onboarding-v1
services:
  open-webui:
    container_name: local-ai-lab-open-webui
    depends_on:
      qdrant:
        condition: service_started
        required: true
    environment:
      OLLAMA_BASE_URL: http://host.docker.internal:11434
      OPENAI_API_BASE_URL: http://host.docker.internal:1234/v1
      WEBUI_AUTH: "true"
    image: ghcr.io/open-webui/open-webui:v0.9.6
    networks:
      default: null
    ports:
      - mode: ingress
        host_ip: 127.0.0.1
        target: 8080
        published: "8080"
        protocol: tcp
    volumes:
      - type: volume
        source: open_webui_data
        target: /app/backend/data
        volume: {}
  qdrant:
    container_name: local-ai-lab-qdrant
    healthcheck:
      test:
        - CMD
        - bash
        - -lc
        - timeout 3 bash -c '</dev/tcp/127.0.0.1/6333'
      timeout: 5s
      interval: 10s
      retries: 12
    image: qdrant/qdrant:v1.18.2
    networks:
      default: null
    ports:
      - mode: ingress
        host_ip: 127.0.0.1
        target: 6333
        published: "6333"
        protocol: tcp
      - mode: ingress
        host_ip: 127.0.0.1
        target: 6334
        published: "6334"
        protocol: tcp
    volumes:
      - type: volume
        source: qdrant_storage
        target: /qdrant/storage
        volume: {}
networks:
  default:
    name: ai-lab-os-onboarding-v1_default
volumes:
  open_webui_data:
    name: ai-lab-os-onboarding-v1_open_webui_data
  qdrant_storage:
    name: ai-lab-os-onboarding-v1_qdrant_storage

$ uv run ruff check .
All checks passed!

$ uv run pytest
============================= test session starts ==============================
platform darwin -- Python 3.12.13, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/nolos/Desktop/ai-lab-os-onboarding-v1
configfile: pyproject.toml
testpaths: tests, apps/model-dashboard/tests, evals/local-llm-benchmark/tests
plugins: anyio-4.13.0
collected 177 items

tests/test_api.py ...                                                    [  1%]
tests/test_bench_matrix.py ....                                          [  3%]
tests/test_chunking.py ..                                                [  5%]
tests/test_cli.py ...                                                    [  6%]
tests/test_doctor.py .........                                           [ 11%]
tests/test_documents.py ..                                               [ 12%]
tests/test_embeddings.py .......                                         [ 16%]
tests/test_hardware_profile.py .....                                     [ 19%]
tests/test_lab_cli.py ............                                       [ 26%]
tests/test_llm_factory.py .                                              [ 27%]
tests/test_ollama_provider.py .....                                      [ 29%]
tests/test_openai_compatible_provider.py .......                         [ 33%]
tests/test_prompts.py .                                                  [ 34%]
tests/test_provider_errors.py ..                                         [ 35%]
tests/test_quant_advisor.py ........                                     [ 40%]
tests/test_rag_service.py .                                              [ 40%]
tests/test_settings.py ...                                               [ 42%]
tests/test_vectorstore_factory.py ..                                     [ 43%]
apps/model-dashboard/tests/test_charts.py .....                          [ 46%]
apps/model-dashboard/tests/test_csv_io.py ......                         [ 49%]
apps/model-dashboard/tests/test_http_server.py .............             [ 57%]
apps/model-dashboard/tests/test_icons.py ....                            [ 59%]
apps/model-dashboard/tests/test_model_dashboard.py ..................... [ 71%]
..................................                                       [ 90%]
apps/model-dashboard/tests/test_reports.py ...                           [ 92%]
apps/model-dashboard/tests/test_schema.py ...                            [ 93%]
apps/model-dashboard/tests/test_scoring.py ...                           [ 95%]
evals/local-llm-benchmark/tests/test_harness.py ........                 [100%]

============================= 177 passed in 8.89s ==============================

$ python3 -m unittest discover -s apps/model-dashboard/tests
............................................................................................
----------------------------------------------------------------------
Ran 92 tests in 6.315s

OK

$ python3 -m unittest discover -s evals/local-llm-benchmark/tests
........
----------------------------------------------------------------------
Ran 8 tests in 2.298s

OK

$ python3 scripts/model_dashboard_smoke.py
Smoke artifacts: /private/var/folders/1j/jfcr7sxx3ds66jm2mnn8f66m0000gn/T/model-dashboard-smoke-52fw8du6

==> Run dashboard tests
$ /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m unittest discover -s /Users/nolos/Desktop/ai-lab-os-onboarding-v1/apps/model-dashboard/tests
............................................................................................
----------------------------------------------------------------------
Ran 92 tests in 6.316s

OK

==> Initialize fixture database
$ /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/nolos/Desktop/ai-lab-os-onboarding-v1/apps/model-dashboard/run_dashboard.py init-db --db /private/var/folders/1j/jfcr7sxx3ds66jm2mnn8f66m0000gn/T/model-dashboard-smoke-52fw8du6/model_dashboard.sqlite --reset --with-fixtures
Imported fixtures: {'models': 4, 'model_runs': 4, 'eval_scores': 4, 'decisions': 4}
Database ready: /private/var/folders/1j/jfcr7sxx3ds66jm2mnn8f66m0000gn/T/model-dashboard-smoke-52fw8du6/model_dashboard.sqlite

==> Generate fixture report
$ /Applications/Xcode.app/Contents/Developer/usr/bin/python3 /Users/nolos/Desktop/ai-lab-os-onboarding-v1/apps/model-dashboard/run_dashboard.py report --db /private/var/folders/1j/jfcr7sxx3ds66jm2mnn8f66m0000gn/T/model-dashboard-smoke-52fw8du6/model_dashboard.sqlite --out /private/var/folders/1j/jfcr7sxx3ds66jm2mnn8f66m0000gn/T/model-dashboard-smoke-52fw8du6/fixture-model-report.md
Report written: /private/var/folders/1j/jfcr7sxx3ds66jm2mnn8f66m0000gn/T/model-dashboard-smoke-52fw8du6/fixture-model-report.md

Dashboard smoke passed.
Database: /private/var/folders/1j/jfcr7sxx3ds66jm2mnn8f66m0000gn/T/model-dashboard-smoke-52fw8du6/model_dashboard.sqlite
Report: /private/var/folders/1j/jfcr7sxx3ds66jm2mnn8f66m0000gn/T/model-dashboard-smoke-52fw8du6/fixture-model-report.md
```

### CI Evidence

GitHub Actions CI is green on the latest remote `main` available at release
prep time:

```text
run: 27936088278
workflow: CI
event: push
branch: main
head_sha: cee664c2abed0e39968b7f21e4e21bead662639c
title: cli: add quantization advisor
status: completed
conclusion: success
created_at: 2026-06-22T07:16:13Z
completed_at: 2026-06-22T07:16:58Z
url: https://github.com/Nolos510/local-ai-lab/actions/runs/27936088278
job: Lint and test, conclusion=success
```

The local `codex/onboarding-v1` branch was not pushed, by instruction, so branch
CI for these O1-O3 release-prep commits has not run yet. The local validation
gate above is the release-prep evidence for this branch until the user approves
a push or PR.

### Known Limits

- v1.0.0 contains confirmed evidence for only two unique models; it does not
  support broad model-market conclusions.
- Live performance claims are limited to the committed Qwen3 Coder and
  Dolphin-Mistral 24B benchmark evidence.
- The default live `local-ai-lab doctor` path still requires an installed local
  model matching the configured provider/model.
- The annotated `v1.0.0` tag exists locally at commit `73732a5`; repository-local
  evidence does not establish whether that tag was pushed.
