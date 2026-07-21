# ADR 0013: Growth / Skills Lab data and authority boundaries

## Status

Accepted

## Date

2026-07-21

## Context

AI Lab OS needs a way to compare useful skills, extensions, and learning paths
without treating catalog presence, local installation, active configuration, or
course completion as equivalent evidence. Extension inventory can also expose
machine-specific paths, account names, credentials, connector configuration, or
untrusted subprocess output if it is collected or persisted without a narrow
boundary.

The Growth roadmap includes discovery and narrowly reviewed installation, but
both are material expansions of authority. A read-only inventory or metadata
command must not become an implicit general-purpose package manager or grant
install authority to the dashboard, RAG runtime, radar, provider harness, or
unrelated automation.

## Decision

- Keep reviewed public catalogs as tracked JSON under `data/growth_registry/`.
  Catalog promotion is a reviewed repository patch, never a runtime write.
- Keep personal inventory, progress, discovery inbox records, preflight nonces,
  and install audit state under ignored `.local-ai-lab/` files. State
  replacement is fixed-target, no-follow, atomic, and private. The stored
  schemas exclude usernames, home paths, credentials, prompts, documents,
  credentialed connector URLs, and raw subprocess output.
- Keep every Growth command under `ai-lab growth`. Discovery is available only
  through explicit `discover --lookup` and `check-updates --lookup` calls to
  fixed public-metadata adapters. The adapters send no authorization or cookie
  data, inherit no proxy, cap responses, download nothing, and retain only
  escaped untrusted inbox records. `growth review` creates an ignored draft with
  no install authority; catalog promotion remains a reviewed repository patch.
- Make inventory subprocesses explicit and read-only. They use fixed argv lists
  for official host inventory commands, never a shell, and normalize results to
  safe identifiers, ecosystem/source labels, and explicit booleans for
  available, configured, installed, enabled, referenced, and evidenced.
- Treat proof as an existing repo-relative artifact. Installation, configuration,
  or a completed status without an artifact does not establish evidence or
  mastery.
- Keep recommendation rules deterministic and inspectable. Review blocks,
  unavailable items, and unmet prerequisites block first; evidence, selected
  career role, weekly effort, capability gaps, and review state then determine
  `Now`, `Next`, or `Later`. Curated `Watch` remains a catalog status and maps to
  `Later` in the four-outcome personalized recommendation rule.
- Store execution authority in a separate tracked
  `data/growth_registry/install-policies.json`. A policy contains only
  structured host, plugin, marketplace, immutable marketplace revision,
  reviewed version, scope, component, authorization, and data-scope fields; it
  never contains an argv fragment. The initial policy list is deliberately
  empty because none of the current catalog entries has the exact reviewed
  source/version/scope evidence needed for execution.
- Permit exactly four mutation argv shapes: `codex plugin add/remove` and
  `claude plugin install/uninstall`. Validate target, plugin, and marketplace
  identifiers with anchored execution-only character sets, construct argv as a
  list, set `shell=False`, use finite timeouts, and pass no secrets. Shells,
  curl, arbitrary `npx`, Homebrew, community installers, and direct MCP install
  commands are never execution alternatives.
- Keep dashboard mutation authority off unless the server is explicitly started
  with `ai-lab dashboard --enable-growth-installs`. Direct CLI mutation still
  requires the operation-specific allow flag, a first-step live preflight, an
  expiring single-use nonce, and a second-step `--yes` confirmation. Loopback,
  Host/Origin, CSRF-token, and capped-body checks protect dashboard actions.
- Pin direct CLI mutation to this repository's canonical tracked catalogs and
  policy plus its fixed ignored nonce/audit/lock targets; hidden test-path
  overrides cannot grant authority. Run inventory and mutation subprocesses
  with the reviewed repository as `cwd`, so Claude project/local scope cannot
  resolve against the caller's unrelated working directory.
- Bind preflight to the complete reviewed policy, catalog risk facts, exact
  source, marketplace, immutable revision, reviewed/live version, scope, argv,
  and rollback argv. Confirmation consumes the nonce, reloads tracked policy,
  repeats the live lookup, and blocks on any plan, source, or version drift.
  High-risk policies additionally require a tracked threat-review artifact whose
  digest, version, and scope match, followed by the exact typed plugin id and an
  explicit data-scope acknowledgement. Catalog connectors and MCP entries whose
  reviewed `writes` fact is not one of the packet's exact read-only findings are
  classified high-risk independently of the policy's own flag; unknown write
  scope therefore cannot bypass the threat-review lane.
- Treat the official hosts' `plugin@marketplace` install selector honestly: it
  does not itself carry a version argument. A real execution policy may land
  only when its reviewed patch establishes that the configured marketplace
  snapshot resolves the recorded immutable revision and reviewed version. The
  confirm-time recheck and exact post-install verification/rollback are
  compensating controls, not permission to populate the initially empty policy
  file. If that immutable-resolution guarantee cannot be established for a
  host, the target stays review-only.
- Serialize install/remove across dashboard threads and local CLI processes.
  Use persistent fixed-target sidecar locks for nonce and audit read-modify-write
  transactions. Keep the sanitized intent/outcome audit journal append-only;
  verify an install by exact plugin, marketplace, source, revision, and version;
  and automatically execute and verify the allowlisted uninstall whenever an
  install command times out, exits nonzero, or fails post-install verification.
  Removal is also verified absent. Background status exposes enum stages and
  step counts only, never raw output or invented percentages.
- No other product surface may reuse or infer Growth mutation authority.

## Consequences

- The dashboard can later read tracked catalogs and privacy-narrow local state
  without importing inventory subprocess behavior into its render path.
- A scan may report that an item is installed but not enabled, referenced, or
  evidenced; those states remain intentionally independent.
- Malformed or missing host inventory fails with a sanitized error and the
  private state is not replaced by partial untrusted data.
- Catalog risk facts describe known facts and unknowns. Neither
  `metadata_reviewed` nor a recommendation is an install approval or a blanket
  safety verdict.
- Popularity, discovery review drafts, `official: true`, and local detection do
  not create an execution policy. Until a reviewed policy patch lands, every
  catalog extension remains review-only even when the dashboard enable flag is
  present.
- A dry-run derives a static reviewed plan without host lookup, nonce issuance,
  audit mutation, or plugin execution. A live preflight is still non-mutating
  but performs the exact source/version check needed for later confirmation.

## Alternatives considered

- **Store inventory paths and raw host output for debugging.** Rejected because
  those values can contain usernames, home paths, secrets, and private connector
  configuration.
- **Infer usage from installation or course status.** Rejected because it would
  collapse detection into evidence and weaken the proof-first product promise.
- **Add install commands while implementing inventory.** Rejected because G3 is
  deliberately a separate, higher-risk review boundary.
- **Accept raw package names, marketplace URLs, or install commands from the
  inbox.** Rejected because discovery metadata is untrusted and cannot grant
  execution authority.
- **Use a generic package-manager or script fallback.** Rejected because it
  bypasses the official host allowlist, reviewed source/version binding, and
  automatic rollback contract.
- **Put Growth commands on `local-ai-lab`.** Rejected because `ai-lab` is the
  unified operational CLI and the RAG/provider surface must stay narrow.
