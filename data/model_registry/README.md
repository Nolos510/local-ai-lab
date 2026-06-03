# Model Registry

Local registry area for model candidates, reviewed models, and future dashboard
or benchmark import notes.

## Intended Flow

```text
automations/ai-lab-radar
  -> candidate records
  -> evals/local-llm-benchmark
  -> data/eval_results
  -> apps/model-dashboard
```

## Candidate Records

Use `automations/ai-lab-radar/candidate-schema.md` before adding durable
candidate records. Radar candidates should capture why a model is interesting
without implying that it has been installed, downloaded, or benchmarked.

`candidates.csv` is the normalized local registry consumed by the dashboard
Radar Candidates page. It is candidate-only state: radar claims can link to
source packets, radar reports, and benchmark artifact directories, but they must
not create `eval_scores`, final labels, or dashboard decisions without a real
local benchmark result.

## Local-First Boundary

This directory may contain local user notes. Treat unreviewed candidate records,
private benchmark notes, and local file references as local state unless the user
explicitly says they are safe to commit.
