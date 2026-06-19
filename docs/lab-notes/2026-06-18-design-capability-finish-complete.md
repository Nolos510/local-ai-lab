# Design Capability Finish Complete

Date: 2026-06-18

## Scope

This note closes the design/capability finish sprint after F1-F5 landed:

- F1: disabled-by-default, recoverable model removal from Installed Models.
- F2: Midnight Neon chart polish and collapsed-sidebar labels.
- F3: behavior-preserving dashboard server modularization.
- F4: imported benchmark performance charts for tokens/sec, TTFT, and total
  latency.
- F5: portfolio, resume, and roadmap refresh.

## Current Product State

The dashboard now presents a clearer local lab workflow:

```text
candidate -> security gate -> approved benchmark execution -> artifact
-> dashboard import -> compare/perf review -> decision
```

Key user-facing improvements:

- Real dashboard views stay separated from demo fixture data.
- Inventory distinguishes runtime-visible models from filesystem-only folders.
- Model removal is opt-in, token-gated, two-step confirmed, and path-contained.
- Benchmark execution through `ai-lab` requires explicit model id, runner, run
  id, and approval before a local model call is allowed.
- Compare and Capability views show performance charts when imported artifacts
  include `tokens_per_sec`, `ttft_seconds`, or `total_latency_seconds`; otherwise
  they show explicit empty states.

## Evidence

Validated after this documentation refresh:

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Observed results:

- Dashboard tests: 75 passed.
- Benchmark harness tests: 8 passed.
- Dashboard smoke: passed.
- Repo pytest: 149 passed.
- Ruff: passed.

## Truthful Limits

- A second unique confirmed model benchmark is still open.
- Performance charts are implemented, but live perf comparison depends on
  approved local benchmark artifacts importing perf metadata.
- No model was downloaded or executed as part of F4/F5.
- No new runtime dependencies, cloud SDKs, secrets, telemetry, or external
  dashboard assets were added.

## Next Recommended Step

Run one approved second-model benchmark after the exact local runtime id is
visible, import its CSVs, and capture updated screenshots for the portfolio
pack.
