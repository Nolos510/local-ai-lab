# Goal — Growth / Skills Lab (phased: catalog → dashboard → discovery+install)

- **Branch:** `codex/growth-skills-lab` (supersedes the parked `codex/level-up-radar` L1).
- **Builder:** Codex `gpt-5.6-sol`, reasoning `xhigh`.
- **Source of truth for content:** [docs/product/growth-catalog-research-packet.md](../product/growth-catalog-research-packet.md)
  (Claude's curated catalog — real items, provenance, risk facts, proof projects, deterministic
  Now/Next/Later/Watch/Blocked ranking). The existing `data/growth_registry/*.csv` seeds are raw
  material only; the catalog ships as JSON per below.
- **Phasing is deliberate:** install/execute is the highest-risk code, built LAST on a verified
  foundation with the heaviest security QC. Install is IN scope (user requirement) — not optional.

```text
GOAL: Execute G1 -> G2 -> G3 in order in local-ai-lab. Read AGENTS.md and the research packet first.

STANDING CONSTRAINTS (all phases):
- Two-lane boundary holds: the dashboard (apps/model-dashboard) stays stdlib-only with NO new deps,
  NO external assets, NO network or subprocess at render time. The growth package
  (src/local_ai_lab/growth/ or a stdlib helper the dashboard imports) must not pull any dependency
  into the dashboard render path. No agents/MCP/cloud SDKs/telemetry/new frontend framework added to
  the RAG runtime.
- Subprocess work (inventory scan, installs) happens ONLY in explicit CLI commands or gated POST
  actions that tests patch — never at render time (delete-safety tests assert zero render subprocess).
- Reuse Midnight Neon tokens, the metric-tip pattern, I3 keyboard-a11y rules, U4 sorting, U3 filters,
  I1 pagination. Escape everything.
- HONESTY / SAFETY: "safe?" is never a blanket label. Render review_state + specific risk facts
  verbatim; never upgrade a rating. Distinguish available/installed/enabled/referenced/evidenced;
  never infer usage or mastery from installation. Ranking is deterministic (Now/Next/Later/Watch/
  Blocked) from role+effort+prereqs+gaps+review+evidence — no opaque scores. Missing values -> em dash.
- PRIVACY: never store or render usernames, home paths, secrets, env values, prompts, answers,
  chunks, documents, transcripts, credential identifiers, connector URLs containing credentials, or
  private source paths. Sanitize all subprocess output. Never inspect assistant conversation history.
- Dual-layer data: tracked public catalogs in data/growth_registry/{skills,extensions,learning}.json;
  personal inventory + progress + inbox in IGNORED .local-ai-lab/ (growth-state-v1, growth-inbox-v1),
  atomic replacement. Catalog promotion requires a reviewed repo patch (not a runtime write).
- CLI verb is `ai-lab growth ...` (matches `ai-lab radar`; ai-lab is the unified operational CLI).
- Your sandbox cannot write .git: do NOT git commit; end each phase with a report (files, tests,
  gate lines, live verification). Full gate green before each commit-point:
    python3 -m unittest discover -s apps/model-dashboard/tests
    python3 -m unittest discover -s evals/local-llm-benchmark/tests
    python3 scripts/model_dashboard_smoke.py
    uv run pytest -q ; uv run ruff check .
  (Note any sandbox-only 127.0.0.1 bind failures separately; they pass on the real host.)

G1 — CATALOG + INVENTORY + CLI (PR: feat/growth-catalog-inventory)
- ADR for the Growth/Skills Lab surface + an AGENTS.md note that install authority is limited to the
  reviewed Growth flow only.
- JSON schemas + seed catalogs (skills.json, extensions.json, learning.json) built FROM the research
  packet: fields per item incl. id, type, official/provenance, source_url, availability+review_date,
  career_lenses (AIA/AUT/MLD), practical_value, marketability, effort_tier (1-3|4-6|7-10 hrs/wk),
  cost, prereqs, risk_facts{code_exec,fs,network,creds,private_data,writes,hooks,background,
  provenance,license,version_pin,rollback}, status (Now/Next/Later/Watch/Blocked), review_state, and
  a required proof_artifact path field (evidence, not self-attestation).
- Inventory adapters (sanitized, read-only): repo skills/ dir, $CODEX_HOME skills,
  `codex plugin list --json`, `codex mcp list --json`; equivalent Claude CLI + skill locations ONLY
  if the Claude CLI exists. Retain ecosystem+source labels; distinguish configured/installed/enabled.
- Deterministic recommendation rules producing Now/Next/Later/Blocked from role+effort+prereqs+
  capability gaps+review_state+evidence.
- CLI: `ai-lab growth list [--kind][--role][--effort][--json]`,
  `growth scan [--ecosystem repo|codex|claude|all][--dry-run]`,
  `growth progress ITEM --status queued|in_progress|completed|skipped [--evidence PATH]`.
  Exit codes: 0 ok, 1 exec/fetch failure, 2 unsupported host/missing consent/missing CLI/review-gated.
- Tests (mock all subprocess/platform; no live services): schema parse, malformed inventory, missing
  CLIs, duplicate ecosystems, installed-vs-evidenced distinction, deterministic ranking, atomic
  progress writes, and that state/JSON/errors exclude secrets/usernames/home-paths/raw subprocess out.

G2 — DASHBOARD COCKPIT (PR: feat/growth-dashboard)
- Nav label "Growth", route /growth, title "Growth / Skills Lab", views ?view=skills|extensions|
  learning|inbox with filters for role, effort, status, risk, evidence. Keyboard-accessible view
  switcher (aria-current), sortable (U4), paginated if heavy (I1).
- Present "detected vs evidenced" explicitly; render risk_facts + review_state verbatim with a
  metric-tip explaining "safe?" is a review prompt, not a verdict. Show each item's proof_artifact
  and next_action. Personal progress actions (queued/in_progress/completed/skipped, with an evidence
  path) work on loopback behind the action token — these change ignored .local-ai-lab/ state only,
  never a catalog and never anything installed.
- Home/loop-strip may show a small "growth" glance (e.g. skills evidenced, next recommended) — honest
  counts only.
- Tests: each view renders seeded catalog + sanitized inventory, filters work, risk/review verbatim,
  progress writes ignored state atomically, no external assets, render subprocess-safety, a11y
  contracts (skip-link/aria-current/focusable controls).

G3 — DISCOVERY + INSTALL/REMOVE (PR: feat/growth-discovery-installs) — highest-risk; heaviest QC
- Discovery (opt-in metadata ONLY, never installable): `growth discover --source codex|claude|github|
  huggingface|mcp --lookup [--query]` and `growth check-updates --lookup`. Network happens ONLY with
  --lookup (public metadata, no tokens, no downloads, per-item failures non-fatal). Results land in
  the ignored growth-inbox-v1 as untrusted text (escaped); popularity/stars are context, never
  approval. `growth review INBOX_ID` creates an ignored review draft; catalog promotion still needs a
  reviewed repo patch.
- Install/remove — allowlisted OFFICIAL host CLIs ONLY: `codex plugin add/remove`,
  `claude plugin install/uninstall`. NEVER shell, curl, community scripts, arbitrary npx, Homebrew,
  or direct MCP-command install. Gated behind `ai-lab dashboard --enable-growth-installs` (off by
  default; personal progress works without it). CLI: `growth install|remove --target --scope
  --dry-run --yes --allow-install|--allow-remove`.
- INTEGRATOR-REQUIRED HARDENING (all four, with tests):
  1. Airtight argv: validate every plugin/target id against a strict charset (reuse SAFE_RUN_ID_RE
     style); build argv as a LIST, never a shell string; a hostile/typo'd catalog id cannot inject
     extra flags or commands.
  2. Auto-rollback on verify-failure: after install, verify the exact expected plugin+version via the
     inventory scan; if it does not confirm, automatically run the allowlisted uninstall and report
     failure — never leave a half-installed connector.
  3. Audit journal: record every install/remove (target, source, reviewed version, argv, timestamp,
     outcome) to ignored .local-ai-lab/ state — feeds evidence + rollback history.
  4. Source+version pinning at execution: install only from the specific reviewed marketplace+version
     the preflight showed; if the live version drifted from the reviewed one between preflight and
     confirm, re-block until re-reviewed.
- High-risk connectors stay review-only until a dedicated threat-review patch approves an exact
  version+scope; then require two-step confirm + typed plugin ID + explicit data-scope ack.
- Preflight shows exact source, marketplace, reviewed version, components, auth policy, scope, risk
  facts, command argv, and rollback. One serialized background job with sanitized stages (preflight/
  installing/verifying/complete|failed) + a step indicator (no invented %). Reuse loopback + CSRF +
  capped POST bodies + expiring preflight nonces + subprocess timeouts + post-install verification.
- Tests (fakes only; NO live network/CLI/install): no-network-without-flag; metadata parse from
  fixtures; per-item failure non-fatal; id-charset rejection; argv-as-list (no shell); high-risk
  blocked without threat-review; confirmation/nonce expiry; concurrency serialized; verify-failure
  triggers rollback; audit journal written; version-drift re-blocks; CSRF; output escaping; and all
  state/HTML/JSON/errors exclude secrets/home-paths/raw subprocess output.

Per phase: implement, test, run the full gate, STOP with a concise report. Never claim a command
passed unless it was run. Begin with G1.
```
