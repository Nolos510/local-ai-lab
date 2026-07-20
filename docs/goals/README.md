# Codex Goals — parallel agent assignments

Standing goal prompts for the Codex agents. Each goal is paste-ready and runs on
its **own branch** in its **own area** so parallel agents don't collide. The
Claude Code integrator `/loop` gate-checks every branch's commits.

The current integrated product gate is tracked in
[`release-readiness.md`](release-readiness.md). It remains active until the
evidence-backed score reaches 92/100 and every mandatory category gate passes.

## Coordination map

| Goal | File | Branch | Area (owns these files) | Reserved ADR # |
|---|---|---|---|---|
| UI/UX discrepancies | [ui-ux.md](ui-ux.md) | `codex/ui-ux` | `apps/model-dashboard/` | — |
| RAG Quality (R1–R5) | [rag-quality.md](rag-quality.md) | `codex/rag-quality` | `src/local_ai_lab/`, `evals/rag-retrieval/` | 0007–0008 |
| Benchmark breadth + real perf | [bench-breadth.md](bench-breadth.md) | `codex/bench-breadth` | `evals/local-llm-benchmark/`, `src/local_ai_lab/cli/` | 0009 |
| Security / privacy audit | [security-audit.md](security-audit.md) | `codex/security-audit` | read-only report first | 0010 |
| Onboarding + v1 release | [onboarding-v1.md](onboarding-v1.md) | `codex/onboarding-v1` | `docs/`, `README`, `.github/`, `scripts/` | 0011 |

## Shared seams (expect occasional merge conflicts)

`pyproject.toml` (edit only your section), `tests/`, `ROADMAP.md`, and ADR
numbers — hence the reservations above.

## Safety rails baked in

- The **security audit** is report-first / read-only; it applies fixes only after
  approval, on its branch.
- The **onboarding/v1** goal prepares the release but must NOT push or create a
  remote tag without the user.
- Model execution stays behind the existing approval gate everywhere.
