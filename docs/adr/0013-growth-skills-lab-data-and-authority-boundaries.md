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

The Growth roadmap eventually includes installation, but installation is a
material expansion of authority. A read-only inventory command must not become
an implicit general-purpose package manager or grant install authority to the
dashboard, RAG runtime, radar, provider harness, or unrelated automation.

## Decision

- Keep reviewed public catalogs as tracked JSON under `data/growth_registry/`.
  Catalog promotion is a reviewed repository patch, never a runtime write.
- Keep personal inventory, progress, future discovery inbox records, and future
  install audit state under ignored `.local-ai-lab/` files. State replacement is
  atomic and the stored schema excludes usernames, home paths, credentials,
  prompts, documents, connector URLs, and raw subprocess output.
- Expose G1 only through `ai-lab growth list`, `ai-lab growth scan`, and
  `ai-lab growth progress`. The `local-ai-lab` RAG CLI is not a Growth entry
  point.
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
- Grant no installation or removal capability in G1. Any future authority to
  install or remove an extension is limited to the separately reviewed Growth
  flow described by G3, with its explicit consent, allowlist, version pin,
  verification, rollback, and audit gates. No other product surface may reuse or
  infer that authority.

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

## Alternatives considered

- **Store inventory paths and raw host output for debugging.** Rejected because
  those values can contain usernames, home paths, secrets, and private connector
  configuration.
- **Infer usage from installation or course status.** Rejected because it would
  collapse detection into evidence and weaken the proof-first product promise.
- **Add install commands while implementing inventory.** Rejected because G3 is
  deliberately a separate, higher-risk review boundary.
- **Put Growth commands on `local-ai-lab`.** Rejected because `ai-lab` is the
  unified operational CLI and the RAG/provider surface must stay narrow.
