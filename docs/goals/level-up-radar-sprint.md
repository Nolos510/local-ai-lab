# Goal — Level-Up Radar sprint (Skills · Plugins/MCP · Learning)

- **Branch:** `codex/level-up-radar`
- **Builder:** Codex `gpt-5.6-sol`, reasoning `xhigh`.
- **Thesis:** turn the lab's proven radar pattern inward — a "Level Up" section
  that tracks the skills, plugins/MCP servers, and learning that grow both the
  local lab AND the user's marketability. Same DNA as the model radar: a curated
  registry → a lane → why/safe review → a graduation lifecycle → opt-in GitHub/HF
  safety lookup (never auto-install anything). Seed registries are provided by
  the integrator; this sprint builds the rendering + lifecycle around them.

```text
GOAL: Execute loops L1 -> L3 in order in local-ai-lab. Read AGENTS.md first.

STANDING CONSTRAINTS (all loops):
- Dashboard stays stdlib-only; NO new default runtime deps; NO external assets
  or <script src>; NO network calls at render time. New interactions are plain
  links/forms or no-JS <details>.
- Render paths NEVER spawn subprocesses (delete-safety tests patch global
  subprocess.run and assert zero calls during renders).
- Reuse Midnight Neon tokens + the metric-tip pattern. Escape everything.
- HONESTY: the "safe?" / safety_status column is a REVIEW PROMPT, never an
  assertion — render exactly what the registry says (e.g. "needs_review"), never
  upgrade a safety rating. Missing values render as em dash. Do not fabricate
  entries, ratings, stars, or URLs; render only what the seed CSV contains.
- Preserve all existing behavior + keep every currently-passing test green
  (455 at sprint start). This is additive.
- Your sandbox cannot write .git: do NOT attempt git commit; end each loop with
  a report (files, tests, gate lines, live verification).
- Full validation gate green before ending each loop:
    python3 -m unittest discover -s apps/model-dashboard/tests
    python3 -m unittest discover -s evals/local-llm-benchmark/tests
    python3 scripts/model_dashboard_smoke.py
    uv run pytest -q
    uv run ruff check .

SHARED MODEL (build once in L1, reuse in L2/L3):
- Registries live at data/growth_registry/{skills,plugins,learning}.csv (seeded
  by the integrator; schemas below). Load them read-only with stdlib csv, the
  same defensive way _load_radar_candidates loads candidates.csv (missing file
  -> empty lane with an honest empty state; never crash).
- A new "Level Up" nav section (route /level-up) holds three lanes selected by a
  ?lane=skills|plugins|learning query param (default skills), rendered as a
  tab/segmented control that is keyboard-accessible (I3 a11y rules apply:
  focusable, aria-current on the active lane). Each lane is sortable (reuse U4)
  and can be filtered by status.
- Each lane splits "Using now" from "Consider adding" by a status column, mirrors
  the Discover review styling, and supports the graduation idea lightly: a
  status of done/adopted/using is visually distinct from candidate/watchlist.
- Add "Level Up" to NAV_ITEMS (this grows primary nav to 6 — acceptable; keep
  the Midnight Neon nav layout intact and responsive).

L1 — SKILLS LANE + SHARED INFRA
- Build the shared /level-up shell + lane switcher, then the Skills lane from
  data/growth_registry/skills.csv. Columns to surface: name, category, status,
  where_used, marketable_as, why_valuable, level_up_payoff, effort,
  safety_notes, source_url (as a plain <a> link, escaped), review_status.
- BONUS (only if clean): auto-detect installed Claude Code skills by listing
  the repo's .claude/skills/ directory names at request time WITHOUT a
  subprocess (pathlib only) and mark matching registry rows as detected/using;
  if a detected skill is not in the registry, show it in "Using now" with an
  "unlisted" note. If this cannot be done cleanly within the constraints, skip
  it and rely on the registry status column.
- Tests: lane renders seeded rows, empty-registry empty state, source_url is a
  safe escaped link, safety/review columns render verbatim (no upgrade),
  lane switcher aria-current, sorting works, no external assets, render
  subprocess-safety.

L2 — PLUGINS / MCP LANE + OPT-IN SAFETY LOOKUP
- Plugins lane from data/growth_registry/plugins.csv. Columns: name, kind
  (plugin|mcp-server), status, what_it_does, why_useful, local_first_fit,
  safety_status, source_url, review_status, upstream_state.
- Emphasize local_first_fit + safety_status prominently (this lane is about
  trust): render them verbatim; a metric-tip explains safety_status is a review
  prompt, not a verdict.
- OPT-IN network safety/freshness lookup, same sanctioned convention as
  `ai-lab radar check-updates --lookup`: a new `ai-lab growth check-plugins`
  command where network happens ONLY with an explicit --lookup flag (public
  GitHub API metadata for github.com source_urls: stars, pushed_at, archived,
  license; no tokens, no downloads, metadata only, per-row failures non-fatal),
  writing to a LOCAL gitignored data/growth_registry/plugins_upstream_state.json.
  Without --lookup, ZERO network. The dashboard never calls out at render time.
- Tests (fake HTTP, never real network): no-network-without-flag, metadata
  parse from a fixture, per-row failure non-fatal, dashboard render makes no
  network call, safety_status rendered verbatim.

L3 — LEARNING LANE
- Learning lane from data/growth_registry/learning.csv. Columns: title,
  platform, topic, format (cert|course|lesson|track), status
  (planned|in_progress|done|watchlist), why_valuable, marketability_payoff,
  effort_estimate, cost, source_url, review_status.
- Group/filter by topic and by status; make effort + cost + marketability_payoff
  scannable so the user can pick "what to learn next" at a glance. A simple
  progress read (counts of planned/in_progress/done) at the top of the lane.
- Tests: rows render, group/filter by topic + status, counts correct,
  source_url safe link, empty state, no external assets.

Per loop: implement, test, run the full gate, STOP with a concise report
(files, tests, gate lines, live verification). Never claim a command passed
unless it was run. Begin with L1.
```
