# AI Lab Radar Source Packet

Packet title: LLMCORE v0.1 supplied-source candidate notes
Packet date: 2026-06-03
Prepared by: Codex
Approved for radar review: yes
Safe to commit: yes

## Scope

This packet copies the supplied-source model notes already present in
`evals/local-llm-benchmark/SPEC.md`, prompt
`LLMCORE-v0.1-008: Research Synthesis From Supplied Sources`.

The packet exists so future AI Lab Radar runs have an approved repo-local input
source instead of needing to infer candidates from reports, memory, or thin air.
It does not add web research, downloads, model runs, cloud calls, secrets, or
eval scores.

## Source References

| Source ID | Source type | Source date | Link or local reference | Notes |
| --- | --- | --- | --- | --- |
| A | benchmark source snippet | unknown | `local-file:evals/local-llm-benchmark/SPEC.md#LLMCORE-v0.1-008` | Supplied facts about Model Atlas 7B. |
| B | benchmark source snippet | unknown | `local-file:evals/local-llm-benchmark/SPEC.md#LLMCORE-v0.1-008` | Supplied facts about Model Boreal 13B. |
| C | benchmark source snippet | unknown | `local-file:evals/local-llm-benchmark/SPEC.md#LLMCORE-v0.1-008` | Shared test-scope notes for both models. |

## Copied Notes Or Excerpts

### Source A

```text
Model Atlas 7B is fast on a MacBook Air M2 and answers simple coding prompts
well, but it often gives overconfident dates.
```

### Source B

```text
Model Boreal 13B is slower than Atlas 7B but gives stronger long-form summaries
and better uncertainty statements.
```

### Source C

```text
Both models were tested without internet access. Neither model was tested on
image input, browser use, or private document retrieval.
```

## Candidate Notes

### Candidate: Model Atlas 7B

| Field | Value |
| --- | --- |
| Candidate name from source | Model Atlas 7B |
| Model family | unknown |
| Provider or org | unknown |
| Parameter count | 7B |
| Format or runtime | unknown |
| Claimed context window | unknown |
| License | unknown |
| Local artifact status | unknown |
| Hardware fit | Source claims fast behavior on MacBook Air M2; RAM or VRAM practicality unknown. |
| Claimed strengths | Source claims fast behavior on MacBook Air M2 and good answers on simple coding prompts. |
| Risks or caveats | Source claims overconfident dates. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, and local artifact path are unknown. |
| Suggested radar disposition | `watchlist` |
| Proposed local eval | Revisit after confirming local artifact, runtime, and license; test coding and date-sensitive truthfulness before treating as a daily-driver candidate. |

### Candidate: Model Boreal 13B

| Field | Value |
| --- | --- |
| Candidate name from source | Model Boreal 13B |
| Model family | unknown |
| Provider or org | unknown |
| Parameter count | 13B |
| Format or runtime | unknown |
| Claimed context window | unknown |
| License | unknown |
| Local artifact status | unknown |
| Hardware fit | Source claims slower behavior than Atlas 7B; RAM or VRAM practicality unknown. |
| Claimed strengths | Source claims stronger long-form summaries and better uncertainty statements than Atlas 7B. |
| Risks or caveats | Slower than Atlas 7B. Image input, browser use, and private document retrieval were not tested. License, runtime, context window, and local artifact path are unknown. |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | If already locally available and approved for testing, run `evals/local-llm-benchmark/SPEC.md` through `skills/local-llm-eval`, especially research synthesis and uncertainty prompts. |

## Reviewer Notes

- Candidate records must follow `automations/ai-lab-radar/candidate-schema.md`.
- Do not create `eval_scores.csv`, dashboard decisions, or benchmark scores from
  these source claims.
- Do not fetch links, download models, call cloud APIs, or use secrets.
- Treat all missing metadata as unknown until a user-approved local source or
  real local benchmark run provides it.
