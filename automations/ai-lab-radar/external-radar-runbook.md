# External Radar Runbook

External Radar is an on-demand public metadata scan for finding local-testable
model candidates before they enter the approved local registry.

## Boundary

- Use curated public metadata sources only: official model cards, Hugging Face
  pages, GitHub release/readme pages, and official project docs.
- Record metadata only: model name, provider, family, parameter count, runtime
  hints, explicit license, explicit context length, source URL, source date,
  why interesting, and risks.
- Do not download models, run models, call model APIs, add API clients, use API
  keys, use secrets, write crawler code, or create install instructions.
- Do not edit `data/model_registry/candidates.csv` until the user approves the
  specific candidates.
- Do not convert source claims into dashboard scores or decisions.
- Do not treat popularity, stars, likes, downloads, or benchmark claims as a
  security review.
- Do not run model-card code, custom Python loaders, install scripts, notebooks,
  or repository code while preparing a recommendation.

## Workflow

1. Search the curated sources manually and keep the scan scope small enough to
   audit.
2. Write an unapproved packet under `automations/ai-lab-radar/inputs/` with:

   ```text
   Approved for radar review: no
   Safe to commit: no
   ```

3. Use `automations/ai-lab-radar/candidate-schema.md` to write a reviewer report
   under `automations/ai-lab-radar/reports/`.
4. Assign each candidate one disposition: `ready_for_eval`, `watchlist`, `skip`,
   or `needs_more_info`.
5. Assign each candidate conservative security fields:
   `security_review_status=needs_review`,
   `download_approval=not_approved`, license review state, provenance state,
   security notes, and isolation notes.
6. Leave `data/model_registry` unchanged until approval.
7. After approval, normalize only approved candidates into the registry.

## Security Screening Checklist

For each candidate, capture what is known and what remains unknown:

- Publisher/source: official page, mirror, quantizer, or user-local artifact.
- Artifact format: GGUF, MLX, Safetensors, Ollama, LM Studio, or custom.
- License: explicit license and any unresolved use restrictions.
- Runtime path: local runtime that loads weights without executing upstream code.
- Hash/release evidence: checksum, release metadata, or model-card file listing
  when available.
- Red flags: custom code requirement, pickled weights, install scripts,
  notebooks, unclear publisher chain, missing license, or mismatched local
  inventory name.

## Validation

Run these checks before handing the packet back to the user:

```bash
git diff -- automations/ai-lab-radar docs data/model_registry
rg -n "download|snapshot_download|from_pretrained|api_key|token|openai|anthropic|huggingface_hub|requests|httpx" automations/ai-lab-radar docs data/model_registry
python3 scripts/model_dashboard_smoke.py
```

Review any search hits. Guardrail text is expected; runtime code, dependency
adds, secrets, or download logic are not.
