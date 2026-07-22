# SkillOpt Pilot

## Product Question

Can a local skill optimizer improve reusable Codex and Claude instructions
reliably enough to justify adding it to AI Lab OS?

## Finding

SkillOpt is useful as an experiment, but the evaluated revision is not yet
dependable enough for autonomous use in this lab.

| Evidence | Result |
| --- | --- |
| Deterministic supplied fixture | Improved from 33% to 100%; harmful edit blocked |
| Initial local baseline | 0/4 hard test; 8.3% soft score |
| Best exploratory hard-gated run | 4/4 untouched hard test |
| Three fresh independent repeats | One accepted; two made no edit |
| Accepted fresh repeat | 3/4 hard test; 91.7% soft score |

The exploratory success proves the idea can work. The fresh repeats show it is
not reliable enough to become a background self-updater.

## Current Integration State

| Surface | State | Meaning |
| --- | --- | --- |
| Local AI Lab | Evaluation only | Can report qualification and inspect the pinned checkout |
| Codex | Blocked until qualified | No global skill, installer, transcript harvesting, or adoption |
| Claude Code | Blocked until qualified | No plugin, hook, scheduler, transcript harvesting, or adoption |

Inspect the tracked sanitized evidence:

```bash
uv run ai-lab skills status
uv run ai-lab skills status --json
```

Inspect an external checkout without running its code:

```bash
uv run ai-lab skills preflight --checkout /path/to/reviewed/SkillOpt
```

Inspect a host handoff state:

```bash
uv run ai-lab skills handoff --host local
uv run ai-lab skills handoff --host codex
uv run ai-lab skills handoff --host claude
```

These commands do not install, execute, or adopt SkillOpt output.

## Promotion Gate

Activation review may begin only after all conditions pass:

- One versioned cohort with at least five fresh independent trials.
- At least 80% of trials produce a successful improvement.
- Every accepted candidate improves hard validation.
- Every accepted candidate scores 100% on the untouched hard test.
- No backend errors.
- Synthetic reviewed tasks only, with hard gate and untouched test.

Failed cohorts remain immutable evidence. Do not cherry-pick successful runs or
combine retries from different optimizer/protocol versions to manufacture a
passing rate.

Passing this gate still does not install anything. It permits a separate
architecture, privacy, and Growth-policy review.

## Explicit Non-Goals

- Mining `~/.codex` or `~/.claude` sessions.
- Sending private session excerpts to any model provider.
- Nightly scheduling.
- Automatic adoption into `AGENTS.md`, `CLAUDE.md`, or `SKILL.md`.
- Running vendor installer scripts.
- Bypassing `ai-lab growth` installation authority.
