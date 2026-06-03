# AI Lab Radar Inputs

This directory stores user-approved local source packets for AI Lab Radar.
Packets are the only source material the radar should use when creating
candidate records or concise radar reports.

## What Belongs Here

Add small Markdown packets that are explicitly approved for radar review and
safe to commit. Good packet material includes:

- Copied model card excerpts.
- Copied release notes.
- User-provided benchmark snippets.
- Links supplied by the user for reference only.
- Local notes that the user has marked safe for candidate review.

Do not place private drafts, secrets, credentials, raw private benchmark output,
or unapproved personal notes in this directory.

## Source Packet Rules

- Mark each packet as approved before using it.
- Preserve source claims as claims; do not convert them into eval scores.
- Record unknown license, runtime, context window, hardware, and source dates as
  unknown instead of inferring them.
- Do not fetch links, crawl pages, download models, call cloud APIs, or use
  secrets from this automation.
- Recommend only `watchlist`, `ready_for_eval`, `skip`, or
  `needs_more_info`.
- For `ready_for_eval`, point to `evals/local-llm-benchmark/SPEC.md` and
  `skills/local-llm-eval`; do not run or download the model from radar.

## Suggested Packet Names

Use dated, source-specific filenames:

```text
YYYY-MM-DD-approved-source-packet.md
YYYY-MM-DD-<topic>-approved-source-packet.md
```

Start from `source-packet-template.md` when adding a new packet.
