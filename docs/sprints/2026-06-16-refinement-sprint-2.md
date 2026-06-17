# AI Lab OS Refinement Sprint 2 — 2026-06-16

Continuation of [Sprint 1](2026-06-16-refinement-sprint.md). Same operating model:
one **loop** at a time, validation gate green, commit, stop, report.

## Where we are (status)

Sprint 1 delivered 2 of 4 iterations, then stopped:

| Sprint 1 iteration | State |
|---|---|
| 1. Inline SVG charts | ✅ shipped (`3d171c4`), verified green |
| 2. Vendor icons offline | ✅ shipped (`538adf5`), verified green, no external assets |
| 3. CI gate | ❌ not done — **carried into Sprint 2** |
| 4. `ai-lab` CLI | ❌ not done — **carried into Sprint 2** |

**Security/privacy hardening shipped in commit `33d3554`.** Follow-up doc
freshness work should keep the ADR/API docs and sprint notes aligned with that
landed behavior before continuing to CI and CLI carryover work.

## Issues identified (this sprint addresses them)

1. **Security/privacy hardening landed.** Commit `33d3554` protects the pass in
   git history; doc freshness still matters for the breaking API shape.
2. **`ruff` is green locally.** The security pass no longer carries the old
   `UP032` lint failure.
3. **Breaking API change needs durable docs.** The ask response now
   drops `retrieved_chunks`, and `Citation`/`CitationResponse` drop `source_path`
   and `preview` (privacy-motivated, aligns with AGENTS.md §3 "no retrieved-chunk
   dumps"). Keep the ADR + docs current. (Iteration 1 follow-up)
4. **No CI gate.** The 61 dashboard + 8 eval tests still don't gate PRs; CI also
   doesn't run `ruff` over everything — which is exactly why issue #2 slipped in.
   (Iteration 2)
5. **No unified operating surface.** The loop is still driven by scattered
   commands. (Iteration 3)
6. **Repo hygiene drift.** Two roadmaps (`ROADMAP.md` vs `docs/roadmap.md`) are
   diverging; `docs/sprints/` and the Discord learning-assistant idea need to be
   tracked in an explicit docs location. (Iteration 4)

## Operating rules

Same as Sprint 1 — read [AGENTS.md](../../AGENTS.md). Stdlib-only for dashboard
and harness; no new runtime deps; no external network calls from the dashboard;
narrow, package-scoped changes; preserve passing tests.

### Validation gate (run all, every loop)

```bash
python3 -m unittest discover -s apps/model-dashboard/tests
python3 -m unittest discover -s evals/local-llm-benchmark/tests
python3 scripts/model_dashboard_smoke.py
uv run pytest -q
uv run ruff check .
```

Commit message convention as in Sprint 1. Scopes this sprint: `security`,
`privacy`, `ci`, `cli`, `docs`.

---

## Iteration 1 — Land the security/privacy hardening pass (SHIPPED)

**Objective.** Get the hardening work reviewed, lint-clean, verified,
documented, and committed — so it is safe in history and protected by the gate.

Status: shipped in commit `33d3554`.

**Do NOT rewrite the pass.** It is already coherent and well-tested. The job is
to finish, verify, and land it.

**What the pass contains (review against this list).**
- `evals/local-llm-benchmark/harness.py` — CSV formula-injection neutralization
  (`_safe_csv_cell`, `FORMULA_PREFIXES`), terminal-escape neutralization
  (`_neutralize_terminal`), path-traversal-safe `_run_dir`
  (`SAFE_RUN_ID_RE` + `relative_to` check), endpoint validation tightened to
  loopback-only (private-LAN IPs no longer allowed).
- `src/local_ai_lab/config/settings.py` — loopback-only validator for
  `qdrant_url` / `ollama_base_url` / `lm_studio_base_url`; `top_k` upper bound 20.
- `src/local_ai_lab/ingestion/documents.py` — `_is_within_root` symlink/traversal
  guard on directory ingestion.
- `src/local_ai_lab/api/app.py` + `schemas.py` + `rag/service.py` — **breaking
  privacy change**: ask response no longer returns `retrieved_chunks`; `Citation`
  drops `source_path` + `preview`; generic provider-error message (no internal
  leak); `top_k` bound.
- `apps/model-dashboard/model_dashboard/server.py` — path-safety helpers
  (`_safe_artifact_dir`), `_external_link_or_text`, inventory path cells, Ollama
  manifest path resolution.
- `compose.yaml` + `.env.example` — Qdrant/Open WebUI bound to `127.0.0.1` only;
  `WEBUI_AUTH` defaults to `true` via `OPEN_WEBUI_AUTH`.
- Tests added across `test_csv_io`, `test_model_dashboard`, `test_harness`,
  `test_reports`, `test_http_server`, `test_settings`, `test_documents`,
  `test_api`, `test_rag_service`.

**Steps.**
1. Fix the lint error: `uv run ruff check . --fix` (converts the `harness.py:895`
   `.format` to an f-string), then re-read that hunk to confirm the escape logic
   is unchanged.
2. Run the **full validation gate**. All green.
3. Document the breaking API change:
   - New ADR in `docs/adr/` recording the privacy-narrowing of the ask response
     (why `retrieved_chunks`/`source_path`/`preview` were removed; reference
     AGENTS.md §3).
   - Update any README / API docs that show the old `/ask` response shape.
   - One `docs/lab-notes/` entry summarizing the hardening pass.
4. Commit. Prefer logical splits over one mega-commit, e.g.:
   `security: harden harness + service URLs against traversal/injection` and
   `privacy: stop returning retrieved chunks and source paths from /ask`.
   A single well-described commit is acceptable if splitting is impractical.

**Definition of Done.** Full gate green incl. `ruff`; the breaking API change has
an ADR + doc update; pass is in git history.

---

## Iteration 2 — CI gate (carryover from Sprint 1, now doubly justified)

**Objective.** Make CI run the dashboard, eval, and smoke suites **and** `ruff`
over the whole repo, so a red lint or a broken dashboard test can never land
silently again (cf. issues #2, #4).

**Files.** `.github/workflows/ci.yml`.

**Steps.** After the existing `Pytest` step, add existence-guarded steps:
- `python3 -m unittest discover -s apps/model-dashboard/tests`
- `python3 -m unittest discover -s evals/local-llm-benchmark/tests`
- `python3 scripts/model_dashboard_smoke.py`
Confirm the existing `ruff` step lints the whole tree (not just `src/`). Do not
use `--probe-server`.

**Definition of Done.** CI runs all three suites + repo-wide ruff on PR + push;
a deliberately broken dashboard test or a lint error fails CI.

---

## Iteration 3 — Unified `ai-lab` CLI (carryover from Sprint 1)

Build exactly as specified in
[Sprint 1, Iteration 4](2026-06-16-refinement-sprint.md#iteration-4--unified-ai-lab-cli):
new `src/local_ai_lab/cli/lab.py`, `ai-lab` console script in `pyproject.toml`,
subcommands `status / radar list / bench run / import / report / dashboard`,
shelling out to existing entry points for the actions and direct stdlib reads for
status. Add `tests/test_lab_cli.py`. Add an ADR for the new operating surface.

**Definition of Done.** As in Sprint 1, Iteration 4.

---

## Iteration 4 — Repo hygiene

**Objective.** Remove the drift that makes the repo harder to reason about.

**Steps.**
1. **Reconcile roadmaps.** `ROADMAP.md` (root) and `docs/roadmap.md` have
   diverged. Pick one canonical location, merge content, and either delete the
   other or make it a one-line pointer. Update any links.
2. **Track the sprint docs.** `git add docs/sprints/` so this plan and the
   handoffs are in history.
3. **Resolve the idea doc.** Keep the Discord trading learning assistant
   proposal under an explicit `docs/ideas/` / `docs/projects/` folder. Don't
   leave idea documents dangling at the docs root.

**Definition of Done.** One canonical roadmap; sprint docs tracked; no stray
untracked docs at `docs/` root; gate green.

---

## Sequence & rationale

1. **Land hardening pass** — highest risk reduction; clears the red gate.
2. **CI gate** — locks in the protection that would have prevented the red gate.
3. **`ai-lab` CLI** — the deferred utility win, on a now-protected base.
4. **Hygiene** — cheap cleanup once the substantive work is in.

**Stretch (not committed this sprint):** `server.py` is ~3.9k lines. A future
sprint should split it into `pages/` + `components.py` + `filters.py` with tests
held constant. Track as a roadmap item, not half-built.
