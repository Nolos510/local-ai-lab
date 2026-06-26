# Dolphin-Mistral 24B v1 Benchmark Validation

Date: 2026-06-25
Candidate: `20260605-dolphin-mistral-24b-venice-edition`
Official run: `20260625-dolphin-mistral-24b-venice-edition-dashboard-test-r2`

## Scope

This note is the committed, sanitized release evidence for the v1 second
benchmark. The raw benchmark artifact remains local/ignored under
`data/eval_results/` and is not normal Git history.

The earlier run `20260625-dolphin-mistral-24b-venice-edition-dashboard-test` is
repeatability context only. v1 does not average multiple runs.

## Runtime Approval

- runner: `lmstudio-cli`
- exact local model id: `dolphin-mistral-24b-venice-edition`
- security status: `local_inventory_reviewed`
- download approval: `not_needed_local`
- reinstall/update/download approval: not approved

The approval applies only to the exact already-local LM Studio CLI id. Any new
artifact, download, reinstall, update, or alternate runtime id needs a new
review.

## Raw Capture Verification

```text
raw response records: 12
runtime errors: 0
```

SHA256 evidence:

```text
metadata.json: 17310e30032595d7adeec1567dc37a3be42078c152b880efc1920a0f2d7e4edd
raw_responses.jsonl: 15dcffc34560552103aef25d441f7603f9730e940887e52be02d6763c113f616
evidence.md: 07aab3bf37b2717e7d455595392b758c06b1d318cde11bfd9cdefbbf0d3296a3
scores.json: a0240147b1de0e7f9802427d4e5cc788107c621d0881f93cac161bb96a6c170d
decision.json: 2b82468361f7820409eb2a902fa603666dca968e199d18b3d3d86224b14ee974
```

Dashboard CSV hashes:

```text
models.csv: b1331423adf74fd57cde6dcb4e1f6b75cb89c41f431574ca7f1857dc097a7fec
model_runs.csv: 9b036f245f054b5865e3e210f0029a9d41d65a2ce99a70bf4db3cd76fc043a2c
eval_scores.csv: 72bcc45222d9490f59f78a6faa00d373c7c1f8fc1801a35b0297218e12bb9039
decisions.csv: 53cfb782f2d31494bc902bb5fa42558fac069efcad5031bdd230eedc3fe88f73
```

## Confirmed Score

```text
instruction_following: 62
truthfulness_uncertainty: 48
reasoning: 68
coding_debugging: 62
agent_planning: 52
local_ai_lab_usefulness: 50
research_synthesis: 82
business_seo_strategy: 84
long_context: 73
creativity: 78
speed_practicality: 61
total_score: 65.45
final_label: WATCHLIST
score_status: confirmed
```

Decision:

```text
decision: watchlist
keep_installed: 0
```

Summary rationale: the run completed cleanly and performed well on research,
business/SEO strategy, and constrained writing. It remains watchlist because it
failed a self-correction audit, produced unreliable coding tie behavior, gave
generic repo planning, and did not redirect a public-upload request strongly
enough for private benchmark notes.

## Import Evidence

The confirmed CSVs imported into the temp validation DB with one row per table:

```text
Imported rows: {'models': 1, 'model_runs': 1, 'eval_scores': 1, 'decisions': 1}
```

Imported performance metadata:

```text
tokens_per_sec: 28.14
total_latency_seconds: 121.85
ram_usage_gb: 253.18
```

The dashboard routes resolved candidate -> source/report -> artifact ->
imported run -> decision for the official r2 run.
