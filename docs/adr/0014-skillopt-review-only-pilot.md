# ADR 0014: Keep SkillOpt behind a review-only qualification boundary

## Status

Accepted

## Date

2026-07-21

## Context

SkillOpt treats skill text as an optimizable artifact and can propose bounded
edits selected through a validation gate. Its Codex and Claude Code integrations
can also harvest session history, replay tasks with a model backend, stage
changes, schedule runs, and adopt generated skill or memory edits.

Those capabilities are relevant to AI Lab OS, but they cross high-trust
boundaries: private transcripts, model-provider calls, recurring execution, and
mutation of instructions used by coding agents. A deterministic mock improved
the supplied fixture, but our three fresh local hard-gated trials improved only
once. That accepted candidate scored 75% on the untouched hard test, below the
required 100%.

## Decision

- Pin the evaluated external source revision to
  `61735e3922efc2b90c6d6cab561e62e98452ca90`.
- Keep SkillOpt outside this repository and interact only through a small
  read-only qualification boundary. Do not import or vendor its code.
- Store only sanitized aggregate trial evidence. Never store prompts, responses,
  transcripts, credentials, endpoints, documents, or machine paths in the
  tracked evidence file.
- Require reviewed synthetic tasks, a hard validation gate, and an untouched
  test set for every pilot run.
- Require at least five fresh independent trials, an 80% successful-improvement
  rate, 100% untouched hard-test score for every accepted candidate, validation
  improvement for every accepted candidate, and zero backend errors.
- Expose status, pinned-checkout preflight, and host handoff states through
  `ai-lab skills`. The boundary contains no optimizer execution or installation
  command.
- Keep local operation evaluation-only while the gate is blocked. Keep Codex
  and Claude activation blocked until qualification succeeds.
- Even a successful qualification does not authorize installation. Codex or
  Claude activation requires a separate ADR, threat review, and the existing
  reviewed Growth policy flow. Auto-adopt, transcript harvesting, and scheduled
  background optimization remain out of scope unless explicitly approved.

## Consequences

- The lab can measure whether SkillOpt becomes dependable without treating one
  impressive result as proof.
- Current Codex and Claude environments remain unchanged.
- A user can inspect the exact reason activation is blocked without exposing
  private experiment content.
- The lab does not yet run SkillOpt from the canonical CLI. Isolated experiments
  remain manual and external until a later execution-boundary review.

## Alternatives Considered

- **Install the supplied Codex and Claude integrations now.** Rejected because
  the fresh repeatability result did not meet the gate and the installers would
  add transcript, scheduling, and mutation authority.
- **Use automatic transcript harvesting with redaction.** Rejected because
  pattern-based redaction cannot guarantee that private material is removed.
- **Auto-adopt any validation winner.** Rejected because one accepted candidate
  still failed an untouched hard-test case.
- **Vendor SkillOpt into this repository.** Rejected to avoid source drift,
  dependency sprawl, and an unclear ownership boundary.

## Follow-up Work

1. Preserve this failed baseline cohort and investigate deterministic seeds and
   optimizer failure modes without weakening the untouched test gate.
2. After a material optimizer or experiment-protocol change, create a new
   versioned cohort of at least five fresh independent trials. Do not cherry-pick
   successful trials or combine retries across cohorts.
3. If a complete new cohort passes, write a new ADR and reviewed Growth policy before any
   Codex or Claude installation is proposed.
