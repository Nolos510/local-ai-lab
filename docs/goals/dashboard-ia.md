# Goal — Dashboard IA restructure (11 → 4) + per-page explainers

- **Branch:** `codex/dashboard-ia`
- **Area:** `apps/model-dashboard/` only
- A Claude reviewer QCs each loop (gate + live render on :8765 + IA read).

```text
GOAL: Restructure the local-ai-lab dashboard from 11 nav items to 4 workflow-based
sections, build a consolidated Home that makes the use-case obvious, and add a
brief explainer to each page. This is a DELIBERATE REDESIGN (not a
behavior-preserving refactor): UPDATE nav/page tests to match the new IA, but keep
the safety invariants green.

BRANCH: codex/dashboard-ia. AREA: apps/model-dashboard/ only.

START HERE: Read AGENTS.md. The dashboard is stdlib-only, dark "Midnight Neon"
themed, makes NO external/network calls and uses inline no-src JS only (the
test_capability_page_uses_no_external_assets invariant MUST stay green). Reuse the
existing design tokens (var(--*)); do not introduce a new palette/font.

TARGET NAV — 4 primary items + one export action. KEEP ROUTE PATHS STABLE to limit
churn (just relabel nav + consolidate content):
1. Home      — route /          — absorbs Overview + Lab Dashboard + Capability.
2. Discover  — route /radar     — absorbs Radar candidates + Specialty (-> a filter
                                  chip) + Project Radar (-> a secondary tab/section).
3. My Models — route /inventory — absorbs Installed Models + Storage/Install Status
                                  (-> a keep/watch decisions section).
4. Benchmark — route /runs      — absorbs Model Runs + Compare (-> a tab/section).
- Reports (/reports): REMOVE from nav; expose as an "Export report" button/link
  (on Home or Benchmark).
- Demoted routes (/lab, /capability, /specialty, /projects, /storage, /compare,
  /reports): keep them REACHABLE (no 404s) but OUT of the primary nav — prefer
  redirecting each to its new parent section, or keep as deep-link detail views.
  The 4 sections are the canonical surfaces.

HOME (/) — the centerpiece; make the use-case obvious in 5 seconds:
- An explainer line at top: one sentence on what AI Lab OS does (e.g. "Benchmark
  and decide on local models, privately on your Mac.").
- A WORKFLOW LOOP STRIP: Discover -> Install -> Benchmark -> Compare -> Decide,
  each with a LIVE COUNT from real data (candidates ready, models installed,
  artifacts, scores, decisions). Each step links to its section. Honest counts
  only — never fabricate.
- A "DO THIS NEXT" card: ONE guided action computed from current state, e.g.
  "N models ready to benchmark -> Run", or (no runs yet) "Benchmark your first
  model", or "N approved candidates -> install". Pick the highest-priority step.
- Key metrics row (Models, Runs, Avg score, Kept) — reuse the stat cards.
- "Top results" — best-scoring models (condensed table or the existing perf chart).
- "This machine" — a compact hardware/capability card (from the Capability page's
  hardware/readiness content).

PER-PAGE EXPLAINERS: each of the 4 pages opens with a brief 1-2 sentence muted
intro explaining what the tab is for + the primary action. Compact (an intro line/
banner, not a wall of text). Examples:
- Discover: "Models worth evaluating — from your radar, specialty lanes, and GitHub
  projects. Approve a candidate to queue it for benchmarking."
- My Models: "What's installed locally. Run a benchmark, then keep / watchlist /
  skip each model."
- Benchmark: "Benchmark runs and side-by-side comparisons. Higher score and
  throughput are better."

CONSTRAINTS: stdlib-only; NO external/network assets; inline no-src JS only;
Midnight Neon tokens; changes confined to apps/model-dashboard. Because this is a
deliberate IA change, nav/page tests SHOULD be updated to match — but these
invariants MUST stay green: no external assets / no <script src>; chart bar width
never exceeds its plot; wide tables keep overflow-x scroll; the collapsible sidebar
+ its inline toggle still work; no raw private paths leaked.

LOOP PROTOCOL (per loop; run the FULL gate green before each commit):
  python3 -m unittest discover -s apps/model-dashboard/tests
  python3 -m unittest discover -s evals/local-llm-benchmark/tests
  python3 scripts/model_dashboard_smoke.py
  uv run pytest -q
  uv run ruff check .
Commit (scope: dashboard), then STOP and report (files, tests, gate lines, next loop).

LOOPS (in order):
L1 Nav -> 4 items (Home / Discover / My Models / Benchmark); demote the other 7
   routes from primary nav but keep them reachable; add Reports as an "Export
   report" action. Update nav tests. Verify no route 404s.
L2 Build the consolidated Home: explainer line, loop strip (live counts),
   "do this next" card, metrics, top results, "this machine" card.
L3 Discover: merge Radar + a Specialty filter chip + a Projects tab/section + the
   explainer.
L4 My Models: merge Installed Models + a keep/watch decisions section (from
   Storage) + the explainer.
L5 Benchmark: merge Model Runs + a Compare tab/section + the explainer.
L6 Cleanup: finalize Reports->export, remove any dead nav/links, add a docs/
   lab-note summarizing the new IA, final full gate.

Never claim a command passed unless it was run. Begin with L1.
```
