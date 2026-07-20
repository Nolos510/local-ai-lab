# Goal — Dashboard depth sprint (Benchmark density · retrieval lane · keyboard a11y)

- **Branch:** `codex/dashboard-depth`
- **Builder:** Codex `gpt-5.6-sol`, reasoning `xhigh`.
- **Thesis:** three genuinely-useful, measured-gap improvements that build on the
  existing feature set (score-review queue, model-role lanes ADR 0012, runtime
  health, authoritative-run/confirmed-score authority) without duplicating it.
  Each closes a specific criterion in docs/goals/release-readiness.md.

```text
GOAL: Execute loops I1 -> I3 in order in local-ai-lab. Read AGENTS.md and
docs/goals/release-readiness.md first.

STANDING CONSTRAINTS (all loops):
- Dashboard stays stdlib-only; NO new default runtime deps; NO external assets
  or <script src> (the only client JS is the existing inline sidebar toggle;
  new interactions are plain links/forms handled server-side, or no-JS
  <details>/<summary>).
- Render paths NEVER spawn subprocesses (delete-safety tests patch global
  subprocess.run and assert zero calls during renders).
- Reuse Midnight Neon tokens + the metric-tip pattern. Escape everything.
- Never fabricate: missing values render as em dash; estimates stay "est.";
  scores respect confirmed-vs-draft authority (never show a draft as
  authoritative); a lane with no real evidence shows an honest empty state.
- Preserve existing behavior: sorting (U4), decision filters (U3),
  observed-tok/s (F1), authoritative run + grouped history + confirmed-score
  authority (D1), fresh-id guard (D2), the /reviews queue, model-role lanes, and
  runtime health all keep working. Keep every currently-passing test green.
- Your sandbox cannot write .git: do NOT attempt git commit; end each loop with
  a report (files, tests, gate lines, and what you verified live).
- Full validation gate green before ending each loop:
    python3 -m unittest discover -s apps/model-dashboard/tests
    python3 -m unittest discover -s evals/local-llm-benchmark/tests
    python3 scripts/model_dashboard_smoke.py
    uv run pytest -q
    uv run ruff check .

I1 — BENCHMARK PAGE DENSITY + PAGINATION (readiness #5: /runs ~306 KB)
- The Benchmark (/runs) page renders every run row inline (~306 KB) — a wall.
  Make it compact-by-default and paginated, WITHOUT losing history or breaking
  sorting/filtering:
  * Default view leans on D1's authoritative grouping: show one current run per
    model with its older runs behind the existing <details> "N earlier runs"
    collapsible, so the default payload is a fraction of today's.
  * Add server-side pagination for the ungrouped/flat runs table via
    ?page=N&page_size=K (sensible default page_size, capped max), with prev/next
    links that PRESERVE ?sort/?dir and any active filters (U3/U4). Show
    "showing X-Y of Z". Page 1 with no params must behave sanely.
  * Measure and report the new default /runs byte size vs the ~306 KB baseline;
    target a large reduction (aim <150 KB) with no data lost (older runs still
    reachable).
- Apply the same pagination pattern to /radar if it is similarly heavy (~192 KB)
  — same param names, same preservation rules. Keep it DRY (shared helper).
- Tests: pagination slices correctly, out-of-range page clamps, params
  preserved across page links, grouped default hides older runs but keeps them
  reachable, sorting still applies within a page, no external assets, render
  subprocess-safety.

I2 — RETRIEVAL EVALUATION LANE (readiness #8: embedding/reranker home)
- Embedding/reranker models (BGE-M3, cross-encoder) currently have no dashboard
  home and sit "outside the LLM lane". Add a retrieval lane that surfaces the
  real recall@k / MRR evidence already in the repo:
  * Read the committed metrics under evals/rag-retrieval/corpora/*/ (e.g.
    repo-docs-v0.1/bge-m3-metrics.json; repo-docs-v0.2/* once a run exists) —
    read-only, stdlib json, no network, no model calls at render time.
  * Surface as a section/route consistent with the model-role lanes (ADR 0012):
    per corpus + configuration (embedding model, retrieval_mode dense|hybrid,
    reranker identity|cross-encoder), show query_count, recall@k, MRR, and the
    corpus/k. Where multiple configurations exist for a corpus, present them so
    dense-vs-hybrid and identity-vs-reranker are directly comparable.
    Corpus/config with no metrics file yet -> honest "not scored yet" state with
    the exact command to produce it (do NOT run it; it needs a model).
  * Link it into the IA sensibly (e.g. under Benchmark or a small lane surface);
    do not fabricate LLM-style scores for retrieval models, and keep them out of
    the LLM Top Results / task recommender.
- Tests: parse a fixture metrics file, multi-config comparison rendering,
  not-scored-yet empty state, malformed/missing file handled gracefully,
  retrieval models excluded from LLM leaderboards, no external assets.

I3 — KEYBOARD & FOCUS ACCESSIBILITY COMPLETION (readiness #3/#7)
- The dashboard already has a skip-link, aria-labels, and :focus-visible. Finish
  the job so every interactive element is keyboard-operable with a visible focus
  ring and correct semantics:
  * Verify/repair: skip-link targets the real main-content id and works; nav has
    aria-current on the active item; sortable column headers are real focusable
    controls with an accessible name conveying current sort + direction; U3
    filter chips and pagination links are focusable with visible focus;
    <details>/<summary> groups are keyboard-togglable (native) and labeled; the
    /reviews queue confirm/adjust actions and any two-step confirmations are
    fully keyboard-reachable with focus not lost after the action.
  * Ensure focus-visible styling meets contrast against Midnight Neon on every
    interactive surface (links, buttons, chips, headers, summaries).
  * No new JS: rely on native focus order + semantic HTML. Escape everything.
- Tests: rendered pages expose the skip-link + matching target id, aria-current
  on the active nav item, sortable headers/pagination/filter chips are anchors
  or buttons (focusable) with accessible names, no external assets. (Automated
  DOM-string assertions; the human keyboard walkthrough stays a manual checklist
  item — note it in the report.)

Per loop: implement, test, run the full gate, STOP with a concise report
(files, tests, gate lines, live verification incl. measured page sizes for I1).
Never claim a command passed unless it was run. Begin with I1.
```
