# Agent Workflow

This repo can use multiple AI assistants, but the local Mac remains the source of truth for what actually runs.

## Roles

- Human owner: product owner, final reviewer, and merge decision-maker.
- ChatGPT architecture tab: mentor, architecture memory, roadmap helper, and prompt drafter.
- Codex main agent: implementation lead for scoped tasks.
- Codex review agents: read-only reviewers for architecture, tests/QA, docs, privacy/security, and Apple Silicon runtime assumptions.
- Local Mac: execution environment for real checks, smoke tests, and runtime validation.

## Recommended Flow

1. One main builder agent implements the scoped change.
2. The human owner runs the project locally when runtime behavior matters.
3. Review-only agents inspect architecture, tests, docs, Apple Silicon assumptions, and privacy/security.
4. One integrator applies selected fixes.
5. The human owner reviews diffs and reruns checks.
6. Merge only after checks and review.

## Review Lanes

- Architecture: confirms v0 scope, provider boundaries, and ADR requirements.
- Tests/QA: checks focused coverage and command results.
- Docs: checks README, ADRs, workflow docs, and user-facing command accuracy.
- Privacy/security: checks secrets, hidden cloud calls, logging, and local-first assumptions.
- Apple Silicon runtime: checks native macOS runtime assumptions for Ollama, LM Studio, MLX/MLX-LM, and llama.cpp.

## Anti-Patterns

- Multiple agents editing the same core files at once.
- Agents adding frameworks before there is a proven need.
- Agents changing architecture without an ADR.
- Agents claiming commands passed when they did not run.
- Agents creating large speculative abstractions.
- Agents adding cloud services to a local-first repo without approval.

## Practical Rules

- Every agent reads `AGENTS.md` before starting.
- Builder agents keep patches narrow and explain any dependency changes.
- Review agents stay read-only unless explicitly asked to patch.
- Integrators apply selected fixes instead of merging every suggestion.
- Failed or skipped commands are documented honestly in PR notes.
