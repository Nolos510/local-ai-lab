# Goal — UX streamline sprint (auto-import · removal coverage · click-filters · sortable columns · run-all)

- **Branch:** `codex/ux-streamline`
- **Thesis:** user-reported friction from real use. Automate what's mechanical
  (imports), make every row actionable (removal), make navigation direct
  (click-filters, sorting, one-click batch actions) — no digging.

```text
GOAL: Execute loops U1 -> U5 in order in local-ai-lab. Read AGENTS.md first.

STANDING CONSTRAINTS (all loops):
- Dashboard stays stdlib-only; NO new default runtime deps; NO external assets
  or <script src> (the only client JS remains the inline sidebar toggle — new
  interactions must be plain links/forms with server-side handling).
- Render paths NEVER spawn subprocesses (delete-safety tests patch global
  subprocess.run and assert zero calls during renders). Subprocess work happens
  only in explicit POST actions or startup/refresh flows that tests can patch.
- Reuse Midnight Neon tokens + metric-tip pattern. Escape everything.
- Destructive/model-executing actions keep their gates (action token, enable
  flags, two-step confirm for deletion, approval semantics for model runs).
- Never fabricate; missing values render as em dash.
- Your sandbox cannot write .git: do NOT attempt git commit; end each loop with
  a report (files, tests, gate lines).
- Full validation gate green before ending each loop:
    python3 -m unittest discover -s apps/model-dashboard/tests
    python3 -m unittest discover -s evals/local-llm-benchmark/tests
    python3 scripts/model_dashboard_smoke.py
    uv run pytest -q
    uv run ruff check .

U1 — IMPORT AUTOMATION (user's top priority)
- Default --enable-import-actions to ON when the serve bind is loopback (keep a
  --disable-import-actions escape hatch; non-loopback binds keep it off).
- AUTO-IMPORT SYNC: at server startup and after inventory refresh / dashboard-
  triggered runs, detect eval_results artifact sets whose dashboard-import CSVs
  are not reflected in the active DB (the same signal Home's do-this-next uses)
  and import them automatically. Idempotent: never duplicate rows for
  already-imported benchmark_run_ids; corrupt/incomplete sets are skipped with
  a visible note, never crash the server.
- Add an "Import all pending" button (Benchmark page + the do-this-next card
  when relevant) for manual re-sync, behind the action token like existing
  import actions.
- Do-this-next and Benchmark artifact listings must reflect the post-sync state.
- Tests: startup sync imports pending fixture sets exactly once (idempotency on
  second boot), corrupt set skipped with note, loopback default-on vs
  non-loopback default-off, button behind token, no render-time subprocesses
  (sync happens at startup, and tests must be able to patch it).

U2 — REMOVAL COVERAGE (no more "Removal unavailable for this row")
- Diagnose+fix per runtime so every inventory row is either removable or shows
  a SPECIFIC reason:
  - LM Studio rows whose local_path/source_path is missing or does not resolve
    under LMSTUDIO_MODELS_ROOT: attempt resolution by locating the model's
    folder in the root via the indexed publisher/model-id path segments before
    declaring unavailable (the current failure mode for e.g. Gemma-4-12B-QAT
    and Qwen3.6-35B rows). Still refuse anything that resolves outside the
    root.
  - Ollama rows: `ollama rm <model-id>` needs only the exact id — do not
    require a manifest local_path to enable removal; keep id validation.
  - MLX (HF cache) rows: support Trash-based removal of the model's snapshot
    directory with strict containment under the Hugging Face hub cache root;
    same two-step confirm + token + macOS-guard as LM Studio removal.
  - Anything still unavailable must render the concrete reason (e.g. "path not
    found under LM Studio root", "embedding row — remove via LM Studio") in
    place of the generic message.
- Safety invariants unchanged: off-by-default flag, two-step confirm, path
  containment, Trash/ollama-rm only, never rm -rf, tests with fakes for every
  new branch incl. out-of-root refusal for the HF cache path.

U3 — CLICKABLE DECISION FILTERS + BACK-TO-ALL (My Models)
- The keep/watch decisions stat boxes (e.g. "Decisions 4", "Keep installed 3")
  become links that filter the decisions section to that subset via query
  params, with a visible active-filter state and a Clear/All link that returns
  to the unfiltered view. No dead-end: filtering keeps the user on My Models at
  the decisions section (use a fragment anchor), and the Clear link restores.
- Replace the current "go to decision filters" jump-with-no-way-back with this
  pattern.
- Tests: filter subsets, active state, clear restores all, anchors present.

U4 — SORTABLE COLUMNS (server-side, no JS)
- Add clickable column-header sorting to the main tables: My Models inventory,
  the decisions table, Benchmark runs, and Discover candidates. Header links
  carry ?sort=<col>&dir=asc|desc (preserving other active query params);
  current sort shows an arrow indicator; clicking toggles direction.
  Numeric columns sort numerically (None/em-dash values last), text columns
  case-insensitively. Server-side only — no new JS.
- Tests: numeric vs alpha ordering, None-last, direction toggle, param
  preservation, header indicator.

U5 — RUN-ALL BUTTON (My Models)
- A "Run all runnable" control on My Models, visible only with
  --enable-run-tests: first click shows a confirm page enumerating every
  runnable model (exact ids + runners — mirror the batch-queue preflight);
  confirming (with action token) starts the existing background run flow for
  each sequentially, reusing run history + U1's auto-import so results appear
  without manual steps. Per-model failures don't abort the rest.
- Models without an exact local id/runner are listed as skipped with reasons.
- Tests with fakes: control hidden without the flag, confirm page enumerates,
  token required, sequential dispatch, partial-failure summary, no execution
  without confirm.

Per loop: implement, test, run the full gate, STOP with a concise report.
Never claim a command passed unless it was run. Begin with U1.
```
