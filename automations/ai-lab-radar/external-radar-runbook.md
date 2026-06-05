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
5. Leave `data/model_registry` unchanged until approval.
6. After approval, normalize only approved candidates into the registry.

## Validation

Run these checks before handing the packet back to the user:

```bash
git diff -- automations/ai-lab-radar docs data/model_registry
rg -n "download|snapshot_download|from_pretrained|api_key|token|openai|anthropic|huggingface_hub|requests|httpx" automations/ai-lab-radar docs data/model_registry
python3 scripts/model_dashboard_smoke.py
```

Review any search hits. Guardrail text is expected; runtime code, dependency
adds, secrets, or download logic are not.
