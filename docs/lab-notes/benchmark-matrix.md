# Benchmark Matrix

Status: active

`ai-lab bench matrix` turns the local candidate registry into a read-only
benchmark planning table. It is intended for sprint planning and operator
handoff before creating benchmark artifacts.

## Usage

```bash
uv run ai-lab bench matrix
uv run ai-lab bench matrix --limit 5
uv run ai-lab bench matrix --status all --json
uv run ai-lab bench matrix --runner lmstudio-cli
```

## Behavior

- Reads `data/model_registry/candidates.csv`.
- Includes `ready_for_eval` candidates by default.
- Supports `--status`, `--runner`, `--limit`, and `--json`.
- Prints candidate id, model name, runner, local model id, benchmark run id,
  security state, download gate, readiness, blocked reasons, and preflight
  notes.
- Marks rows as `blocked` when exact local runtime metadata is missing or when
  security/download gates are not acceptable.

## Safety Boundary

The command does not initialize benchmark runs, call endpoints, inspect private
model folders, run prompts, download models, or create scores. It only reads the
repo-local candidate CSV.
