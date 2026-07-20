# AI Lab Radar Inputs

This directory stores AI Lab Radar source packets. Local Radar packets must be
user-approved before they produce candidate records or concise radar reports.
External Radar packets are different: they are on-demand public metadata scans
and remain unapproved until the user explicitly approves them.

## What Belongs Here

For Local Radar, add small Markdown packets that are explicitly approved for
radar review and safe to commit. Good packet material includes:

- Copied model card excerpts.
- Copied release notes.
- User-provided benchmark snippets.
- Links supplied by the user for reference only.
- Local notes that the user has marked safe for candidate review.

Do not place private drafts, secrets, credentials, raw private benchmark output,
or unapproved personal notes in this directory.

External Radar packets may include public model-card, GitHub release/readme, or
official project-page metadata, but they must be marked:

```text
Approved for radar review: no
Safe to commit: no
```

Do not register candidates from an external packet until the user approves the
specific candidates.

## Source Packet Rules

- Mark each packet as approved before using it.
- Preserve source claims as claims; do not convert them into eval scores.
- Record unknown license, runtime, context window, hardware, and source dates as
  unknown instead of inferring them.
- For external daily packets, record `first_seen`, `last_seen`, `change_status`,
  and `change_summary`; omit unchanged repeat items.
- For model candidates, include artifact size, disk, memory, compatible local
  runtimes, and the specific benchmark gap.
- For project opportunities, include the complete dated cost/freshness fields
  and one-week MVP action card required by `external-radar-runbook.md`.
- Explain every project in plain language: what it is, the problem it solves,
  who uses it, common uses, how it works, the AI Lab demo, and limitations.
- Do not fetch links, crawl pages, download models, call cloud APIs, or use
  secrets from this automation.
- Recommend only `watchlist`, `ready_for_eval`, `skip`, or
  `needs_more_info`.
- For `ready_for_eval`, point to `evals/local-llm-benchmark/SPEC.md` and
  `skills/local-llm-eval`; do not run or download the model from radar.
- External Radar is metadata-only: no model downloads, model execution, API
  keys, secrets, crawler code, package downloads, API clients, or install
  instructions.
- Keep external candidate records out of `data/model_registry/candidates.csv`
  until explicit approval.

## Suggested Packet Names

Use dated, source-specific filenames:

```text
YYYY-MM-DD-approved-source-packet.md
YYYY-MM-DD-<topic>-approved-source-packet.md
YYYY-MM-DD-external-curated-model-scan.md
YYYY-MM-DD-daily-external-radar.md
```

Start from `source-packet-template.md` when adding a new packet.
