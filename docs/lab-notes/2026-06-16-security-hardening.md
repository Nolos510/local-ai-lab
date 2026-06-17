# Security Hardening Sweep

Date: 2026-06-16

This sweep tightened local-first boundaries after a repository security review.

Changes:

- Dashboard and compose services now default to loopback-only binds.
- Open WebUI auth defaults to enabled, with an explicit `OPEN_WEBUI_AUTH`
  override in `.env.example`.
- Compose image defaults are pinned to reviewed release tags instead of mutable
  `latest` or `main` tags.
- Runtime service URLs for Qdrant, Ollama, and LM Studio must use localhost or a
  loopback IP.
- `/ask` limits `top_k` and no longer returns raw retrieved chunks, source
  paths, or chunk previews in API/JSON responses.
- Dashboard artifact IDs and benchmark run IDs are validated before building
  filesystem paths.
- Dashboard and benchmark CSV exports neutralize spreadsheet formula prefixes.
- Dashboard external links from local registries only render as clickable links
  for `http` and `https` schemes.
- Directory ingestion ignores symlinked files that resolve outside the selected
  corpus root.
- Dashboard responses include anti-framing headers.
- LM Studio capture logs neutralize terminal control bytes.
- New benchmark artifacts under `data/eval_results/` are ignored by git by
  default, while the directory placeholder remains tracked.

Validation commands are recorded in the associated commit and handoff.
