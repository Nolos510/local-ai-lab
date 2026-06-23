# Goal — Standing security / privacy audit

- **Branch:** `codex/security-audit`
- **Area:** read-only report first; fixes on branch after approval
- **Reserved ADR:** 0010 (only if a fix needs one)

```text
GOAL: Run a thorough security + privacy audit of the local-ai-lab repo using your
security tooling, triage against the project's local-first invariants, and produce
a report. This is a STANDING goal — re-run it whenever significant changes land.

BRANCH: codex/security-audit. PHASE 1 IS READ-ONLY (report only, no code changes)
so it doesn't collide with the other agents. Reserve ADR 0010 (only if a fix needs
one).

START HERE: Read AGENTS.md (its non-negotiable local-first / privacy rules are the
audit criteria).

STEP 1 — RUN YOUR SECURITY TOOLS across the repo and collect findings:
- the security scan tool,
- the security best-practices tool,
- the deep security scan tool.

STEP 2 — TRIAGE every finding against these project invariants, and also check
them directly:
- No hidden cloud calls, cloud API clients, model-download logic, secrets, or
  telemetry anywhere. The ONLY sanctioned external call is the quant advisor's
  opt-in --lookup-hf (public metadata only).
- The dashboard makes NO external/network calls at render time; inline no-src JS
  only.
- The default /ask response stays privacy-narrow: no retrieved_chunks, source_path,
  or preview (ADR 0003). Raw retrieval only behind an explicit opt-in flag.
- Loopback-only service binds (compose 127.0.0.1; settings loopback validators).
- Destructive actions are gated + safe: model removal is off by default, two-step
  confirm, Trash/ollama rm (never rm -rf), path-contained to the model roots.
- Benchmark execution is approval-gated; no model call without explicit approval.
- CSV formula-injection neutralization + path-traversal guards in the harness.
- Logs never dump documents, prompts, retrieved chunks, API keys, or private paths.

STEP 3 — WRITE A REPORT to reports/security/<date>-audit.md: tool findings,
triage (true positive / false positive / accepted risk), severity, and a
remediation proposal per real issue. Make NO code changes in this phase.

STEP 4 — STOP and present the report for approval. Apply fixes ONLY after approval,
each as a scoped commit on this branch with the full gate green (the repo's 5
validation commands), then re-report. Never claim a tool/command ran unless it did.
```
