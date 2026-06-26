# v1 Validation Evidence

Date: 2026-06-25

## Branch State

`main` is the local working branch. The dashboard IA work from
`codex/dashboard-ia` was fast-forwarded into `main` through commit `7d90256`.

The final v1 release push and tag are completed only after the full validation
gate is green and `origin` is checked for an existing `v1.0.0` tag.

## Candidate Approval State

The v1 second benchmark candidate is:

```text
20260605-dolphin-mistral-24b-venice-edition
```

Approved local runtime scope:

- runner: `lmstudio-cli`
- exact local model id: `dolphin-mistral-24b-venice-edition`
- benchmark run id:
  `20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2`
- download approval: `not_needed_local`
- security state: `local_inventory_reviewed`

This approval covers benchmark execution for the exact already-installed local
LM Studio id only. It does not approve download, reinstall, update, alternate
artifact selection, or model-card code execution.

## Benchmark Evidence

Official second benchmark source:

```text
data/eval_results/20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2/
```

That raw benchmark directory remains local/ignored. The committed release
evidence is sanitized and records counts, hashes, scores, decision, and import
row counts without committing raw responses.

Raw-response validation:

```text
records: 12
errors: 0
runner: LM Studio CLI
model id: dolphin-mistral-24b-venice-edition
```

SHA256 evidence:

```text
metadata.json: 17310e30032595d7adeec1567dc37a3be42078c152b880efc1920a0f2d7e4edd
raw_responses.jsonl: 15dcffc34560552103aef25d441f7603f9730e940887e52be02d6763c113f616
evidence.md: 07aab3bf37b2717e7d455595392b758c06b1d318cde11bfd9cdefbbf0d3296a3
scores.json: a0240147b1de0e7f9802427d4e5cc788107c621d0881f93cac161bb96a6c170d
decision.json: 2b82468361f7820409eb2a902fa603666dca968e199d18b3d3d86224b14ee974
dashboard-import/models.csv: b1331423adf74fd57cde6dcb4e1f6b75cb89c41f431574ca7f1857dc097a7fec
dashboard-import/model_runs.csv: 9b036f245f054b5865e3e210f0029a9d41d65a2ce99a70bf4db3cd76fc043a2c
dashboard-import/eval_scores.csv: 72bcc45222d9490f59f78a6faa00d373c7c1f8fc1801a35b0297218e12bb9039
dashboard-import/decisions.csv: 53cfb782f2d31494bc902bb5fa42558fac069efcad5031bdd230eedc3fe88f73
```

Confirmed score summary:

```text
total_score: 65.45
final_label: WATCHLIST
score_status: confirmed
decision: watchlist
keep_installed: 0
tokens_per_sec: 28.14
total_latency_seconds: 121.85
ram_usage_gb: 253.18
```

The earlier Dolphin run
`20260625-dolphin-mistral-24b-venice-edition-dashboard-test` is retained only as
repeatability context. v1 does not average runs or invent aggregate official
scores.

## Draft Scoring

Local-judge draft scoring was skipped for the live Dolphin run. The separate
loopback LM Studio endpoint returned `401 Unauthorized`, and no separate judge
token was provided.

The assisted-scoring feature remains implemented and test-covered, but this
release does not fake a `draft-scores.json`.

## Dashboard Import Evidence

Confirmed Dolphin r2 CSVs imported into both the local dashboard DB and a temp
validation DB.

Temp import command:

```bash
python3 apps/model-dashboard/run_dashboard.py import-csv \
  --db /private/tmp/dolphin-v1-dashboard.sqlite \
  --models data/eval_results/20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2/dashboard-import/models.csv \
  --runs data/eval_results/20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2/dashboard-import/model_runs.csv \
  --scores data/eval_results/20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2/dashboard-import/eval_scores.csv \
  --decisions data/eval_results/20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2/dashboard-import/decisions.csv
```

Import result:

```text
Imported rows: {'models': 1, 'model_runs': 1, 'eval_scores': 1, 'decisions': 1}
```

Temp report path:

```text
/private/tmp/dolphin-v1-dashboard-report.md
```

Dashboard route verification against the local dashboard DB succeeded:

```text
/ -> Dolphin-Mistral-24B-Venice-Edition
/radar -> 20260605-dolphin-mistral-24b-venice-edition
/specialty -> Dolphin-Mistral-24B-Venice-Edition
/runs -> 20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2
/compare -> Dolphin-Mistral-24B-Venice-Edition
/lab -> 20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2
/artifacts/20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2 -> watchlist
/models/10 -> Dolphin-Mistral-24B-Venice-Edition
```

## Final Gate Results

Final release validation commands:

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Result:

```text
python3 -m unittest discover -s apps/model-dashboard/tests
122 tests passed.

python3 -m unittest discover -s evals/local-llm-benchmark/tests
15 tests passed.

python3 scripts/model_dashboard_smoke.py
Dashboard smoke passed.

uv run pytest -q
239 tests passed, 58 subtests passed, 1 Starlette/httpx deprecation warning.

uv run ruff check .
All checks passed.
```

This gate was run after the Dolphin registry/security evidence updates and
before pushing `main` plus the release tag.
