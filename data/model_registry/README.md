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

Candidate rows also carry a lightweight security gate:

- `security_review_status` says whether the candidate is unreviewed, needs
  review, locally reviewed, reviewed, or blocked.
- `download_approval` defaults to `not_approved` for external candidates. A
  promising model is still not approved to download or update until a specific
  artifact, license, provenance, and local runtime path are reviewed.
- `security_notes` and `isolation_notes` capture due diligence such as source
  trust, checksum/hash needs, file-format risk, custom-code risk, and the local
  runtime path to use.
- `security_review_path` links to a repo-local Markdown review artifact when a
  candidate needs formal provenance/license/artifact approval before use.

Rows may also include `local_runner`, `local_model_id`, and `default_endpoint`
for models that are already available in the local runtime inventory. These
fields power dashboard run-test buttons when the local server is launched with
run actions enabled. Leave them blank until the exact local runtime identifier
is verified; public model names are not enough.

## Quant Advice

Saved quantization advice belongs under `data/model_registry/quant_advice/` as
small JSON files produced by `uv run ai-lab quant advise`. These files are
candidate metadata only. They may rank possible GGUF quantizations such as
`Q8_0`, `Q6_K`, `Q5_K_M`, `Q4_K_M`, `Q4_K_XL`, or `UD-Q4_K_XL` for LM Studio,
Ollama, and llama.cpp planning, but they do not approve a download, install,
model run, or score.

The default advisor path is local-only and reads an explicit `--repo-id`,
approved source note, or registry candidate. Public Hugging Face metadata lookup
requires `--lookup-hf`; it uses stdlib HTTP only, no SDK, tokens, secrets,
model downloads, or cloud inference calls. Advice remains a hypothesis until a
specific local runtime model id is reviewed and a local benchmark artifact is
imported through the benchmark/dashboard loop.

## Local-First Boundary

This directory may contain local user notes. Treat unreviewed candidate records,
private benchmark notes, and local file references as local state unless the user
explicitly says they are safe to commit.
