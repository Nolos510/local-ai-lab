# Codex Handoff — Design Landing + Capability Finish (2026-06-18)

Paste the fenced block into Codex. Self-contained.

---

```text
You are the main builder finishing the AI Lab OS Capability Sprint and landing
design polish in the local-ai-lab repo (local-first Apple Silicon AI lab).

START HERE:
1. Read AGENTS.md in full — local-first rules, dependency gate, Definition of
   Done are binding.
2. Read docs/sprints/2026-06-18-design-capability-finish-sprint.md — the plan.
   It carries over L4.5 and L5 from docs/sprints/2026-06-17-capability-sprint.md
   (linked for full specs) and adds design polish, perf surfacing, and a
   portfolio refresh. Execute loops F1 → F5 IN ORDER.

CURRENT STATE:
- Capability Sprint L0,L1,L2,L3 (approval-gated execution),L4(baseline),L6(interim)
  are committed and green.
- The dashboard was redesigned ("Midnight Neon" dark theme + left collapsible
  sidebar) in commit 992f661. Build on it; do not introduce a second visual
  language.
- Gate is green: dashboard unittest 67, repo pytest 141, ruff clean.

HARD CONSTRAINTS:
- No new runtime dependencies. Dashboard + harness stay stdlib-only.
- NO external/network assets in the dashboard. The ONLY client JS allowed is
  inline, no src, no network (the sidebar toggle). The test
  test_capability_page_uses_no_external_assets enforces this — keep it green.
- Model execution stays confined to the L3 surface behind explicit per-run
  approval. No other path calls a model. No cloud APIs, secrets, telemetry.
- Narrow, package-scoped changes; preserve passing tests. No architecture change
  without an ADR in docs/adr/.

LOOP PROTOCOL (per loop):
1. Re-read AGENTS.md + the sprint doc. Inspect `git status -sb`.
2. Implement only the listed files; add/extend the listed tests.
3. Run the FULL validation gate and make it pass:
     python3 -m unittest discover -s apps/model-dashboard/tests
     python3 -m unittest discover -s evals/local-llm-benchmark/tests
     python3 scripts/model_dashboard_smoke.py
     uv run pytest -q
     uv run ruff check .
4. Run the loop-specific smoke if listed.
5. Update docs/lab-notes/ADR only where the loop specifies.
6. Commit a self-contained change (format below), then STOP and report: files
   changed, tests added, gate pass/fail lines, smoke result, deviations, next
   recommended loop.
   Commit format:
     <scope>: <summary>

     <what changed, why, how validated, what was NOT tested>

     Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
   Scopes: dashboard, bench, docs, ci.

THE LOOPS (full detail in the sprint doc):
F1 dashboard: L4.5 GATED DELETE ACTION (per Capability Sprint L4.5). Per-row
   Remove in Installed Models: OFF by default (--enable-delete-actions; reuse the
   loopback + action-token gate); TWO-STEP confirm; LM Studio -> macOS Trash via
   osascript (recoverable, no new dep, macOS-guarded); Ollama -> `ollama rm`;
   PATH-CONTAINED to ~/.lmstudio/models or ~/.ollama/models (server-derived path,
   never client-supplied); never rm -rf. FOLD IN the scanner fix
   (_scan_lmstudio_filesystem_models skips folders with no real weight file). ADR
   required. Tests use fakes (no real deletion): disabled->403; LM Studio->Trash
   not rm; Ollama->`ollama rm`; out-of-root refused; first request only confirms;
   scanner skips .DS_Store-only dirs. Style the confirm page to match Midnight
   Neon; use a danger/draft treatment for the destructive confirm button.
F2 dashboard: DESIGN POLISH. (a) Neon-ify charts.py SVG bars with a violet->cyan
   linearGradient in <defs> (solid var(--accent) fallback), keep deterministic +
   empty-state placeholder; extend test_charts.py. (b) Collapsed-rail tooltips:
   when the sidebar is collapsed, hovering a nav icon reveals its label via CSS
   (title attr or ::after) with NO new JS; keep the label in the DOM (visually
   hidden), accessible.
F3 dashboard: L5 MODULARIZATION (per Capability Sprint L5). Split the ~4,170-line
   server.py into layout.py + components.py + filters.py + pages/<page>.py;
   server.py keeps routing + make_handler + serve. BEHAVIOR-PRESERVING — all 67
   dashboard tests pass UNCHANGED (import-path edits only). ALSO relocate the
   Midnight Neon <style> block, the sidebar markup, and the INLINE toggle script
   (must stay inline, no src). Land page-group by page-group if risk grows.
F4 dashboard: PERF FOLLOW-UP. Surface ttft_seconds/total_latency_seconds (+
   tokens_per_sec) in the compare/capability views via charts.py (neon bars from
   F2), with a GRACEFUL EMPTY STATE — no real perf data exists until an approved
   L3 run; the view must read cleanly with all-null columns. Test empty + populated.
F5 docs: PORTFOLIO REFRESH. Update portfolio-case-study.md, resume-bullets.md, a
   docs/lab-notes/2026-06-18-design-capability-finish-complete.md, and ROADMAP.md
   to reflect the redesign, gated delete, and approval-gated execution. TRUTHFUL +
   locally verifiable only; if no real benchmark has run, say so — do not imply
   live perf data exists.

If a validation command cannot run in your environment, document the exact reason
— never claim a command passed unless it was run. Begin with F1.
```

---

## Notes for the human

- A Claude Code `/loop` integrator runs on each commit: full gate + loop-specific
  smoke, checks Definition-of-Done, and flags regressions, new deps, external
  assets, any unapproved model call, delete-safety violations, or behavior changes
  during the F3 refactor.
- **F1 is the destructive one** — extra scrutiny on the delete gate (off by
  default, Trash not rm, path containment).
- **F3 is the riskiest** (big refactor on the just-redesigned file). The order
  (F1/F2 before F3) is deliberate so the modularization sweeps them up once.
- The optional real-benchmark run is yours to trigger when ready; it's what gives
  F4's charts live data.
```
