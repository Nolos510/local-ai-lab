# Model Registry

Local registry area for model candidates, reviewed models, and future dashboard
or benchmark import notes.

For GitHub repositories, workflow tools, agent frameworks, and other non-model
project opportunities, use `data/project_registry` instead. Those records feed
the dashboard project radar and must not become model eval scores.

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

Candidate rows may include model-page and runtime-availability links for
Hugging Face, GitHub, LM Studio, Ollama, llama.cpp/GGUF, MLX, or other explicit
sources. These links are metadata for review and should not be treated as
download or install instructions unless the user separately approves an install
task.

## Local-First Boundary

This directory may contain local user notes. Treat unreviewed candidate records,
private benchmark notes, and local file references as local state unless the user
explicitly says they are safe to commit.
