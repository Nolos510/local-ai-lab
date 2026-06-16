# Odysseus Idea Extraction

This document extracts product ideas from Odysseus without copying source code.

References:

- [Odysseus README](https://github.com/pewdiepie-archdaemon/odysseus)
- [Odysseus setup guide](https://raw.githubusercontent.com/pewdiepie-archdaemon/odysseus/dev/docs/setup.md)
- [Odysseus threat model](https://github.com/pewdiepie-archdaemon/odysseus/blob/dev/THREAT_MODEL.md)

## Boundary

Odysseus is a broad self-hosted AI workspace with chat, agents, research,
documents, email, notes, calendar, local model workflows, model comparison, and
security controls. It is AGPL-licensed. `local-ai-lab` should use it as product
inspiration only.

No Odysseus source code, templates, assets, or implementation details should be
copied into this repository.

## Product Ideas To Adopt

### Workspace Cockpit

One local dashboard should show lab health, model inventory, benchmark status,
candidate decisions, project radar items, recent reports, and next actions.

Current repo fit:

- `apps/model-dashboard` already provides `/lab`, `/radar`, `/projects`,
  `/compare`, and `/reports`.
- Next improvement is degraded-state reporting across Qdrant, Open WebUI,
  Ollama, LM Studio, benchmark artifacts, and dashboard DB.

### Model Compare

Add a proper side-by-side comparison workflow:

- Run the same prompt against two local models.
- Hide model identity during review when practical.
- Support vote, tie, reveal, and comparison history.
- Preserve prompt ID, model IDs, runtime profile, latency, score notes, and
  final decision.

Current repo fit:

- Dashboard already has compare views.
- Benchmark harness already has prompt sets and score artifacts.
- Future work should connect prompt replay to local providers without adding
  cloud calls or hidden downloads.

### Model Cookbook

Add hardware-aware model fit guidance for Apple Silicon:

- Model size, quantization, runtime, context window, expected memory fit.
- Install/load status through LM Studio/Ollama inventory checks.
- Runtime readiness and exact remediation commands.
- Distinguish "fits in memory" from "usable for this workflow."

Current repo fit:

- `local-ai-lab doctor` already checks selected provider readiness.
- `docs/runtime-profiles.md` documents LM Studio and Ollama setup.
- The dashboard can add a model-cookbook page after the model registry has
  enough reviewed candidates.

### Degraded-State Reporting

The lab should clearly report partial readiness:

- Qdrant reachable/missing.
- Open WebUI optional/running/missing.
- Ollama reachable/missing model.
- LM Studio reachable/missing configured model ID.
- Dashboard DB present/missing.
- Benchmark artifacts complete/incomplete/sanitized.

Current repo fit:

- `doctor` already handles Qdrant and provider checks.
- Dashboard smoke checks already validate local server behavior.
- Next step is to expose this status in the dashboard cockpit.

### Deep Research Lane

Long-term: local/web research workflow with source capture, source reading,
progress tracking, and report output.

Do not implement now. This requires an ADR because it introduces external web
content, source trust boundaries, prompt-injection risk, and likely new
dependencies.

### Documents Lane

Long-term: document intelligence and editor workflow that builds on RAG:

- Local document parsing.
- Source-aware summaries.
- Citation-preserving edits.
- Exportable notes/reports.

Do not implement now. The v0 RAG backbone should become reliable before a
document editor is added.

### Memory And Skills Lane

Long-term: reusable workflow skills and local memory for repeated lab tasks.

Do not implement now. Skill/memory features can easily become agent/MCP scope.
They require an ADR and explicit privacy rules before code is added.

### Security Model

Treat this repo as a private local admin-style lab:

- Raw local service ports should bind to localhost/private network only.
- External web content, email, documents, and model output are untrusted input.
- Logs should not include prompts, private docs, chunks, secrets, or raw model
  outputs by default.
- Shell/file actions require explicit human intent.
- Telemetry is disabled or opt-in by default.

Current repo fit:

- `AGENTS.md`, `SECURITY.md`, and provider error sanitization already establish
  the baseline.
- Future external-content lanes need threat-model updates before implementation.

## Product Ideas To Defer

- Autonomous agents.
- MCP tool orchestration.
- Browser automation.
- Email/calendar/tasks.
- Persistent memory.
- Deep research.
- Document editor.
- Multi-user auth.
- Public network exposure.

These are valid long-term workspace lanes, but they are not v0 implementation
scope.
