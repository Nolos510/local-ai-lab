# AI Lab Radar Source Packet

Packet title: Local Runtime And Project Scope Follow-Up Packet
Packet date: 2026-06-29
Prepared by: Codex
Approved for radar review: yes - user requested a small approved local source packet
Safe to commit: yes - repo-local metadata and public candidate names only

## Scope

This packet captures a small approved local source packet from existing
repo-local registry, benchmark, and security-review evidence. It is intended to
make the next radar run concrete without adding external research.

No web pages were fetched. No repositories were cloned. No models were downloaded or run.
No APIs or secrets were used. No dashboard scores or decisions were created.

## Source References

| Source ID | Source type | Source date | Link or local reference | Notes |
| --- | --- | --- | --- | --- |
| A | model registry row | current local registry | `data/model_registry/candidates.csv` | Existing local-inventory row for Qwen3-Coder-30B-A3B-Instruct-MLX-4bit. |
| B | benchmark source packet | 2026-06-03 | `automations/ai-lab-radar/inputs/2026-06-03-real-local-candidates.md` | Local LM Studio artifact evidence for Qwen3-Coder-30B-A3B-Instruct-MLX-4bit. |
| C | model registry row | current local registry | `data/model_registry/candidates.csv` | Existing local-inventory row for Dolphin-Mistral-24B-Venice-Edition. |
| D | security review | 2026-06-05 | `automations/ai-lab-radar/security-reviews/2026-06-05-dolphin-mistral-24b-venice-edition.md` | Local runtime approval gate for the exact LM Studio id only. |
| E | project registry row | current local registry | `data/project_registry/github_repos.csv` | Existing project-registry row for llama.cpp; project scope only, not a model eval candidate. |
| F | project source packet | 2026-06-05 | `automations/ai-lab-radar/inputs/2026-06-05-github-project-radar.md` | Source packet that separates GitHub project opportunities from model candidates. |

## Copied Notes Or Excerpts

### Source A And B

```text
Candidate ID: 20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit
Model name: Qwen3-Coder-30B-A3B-Instruct-MLX-4bit
Format/runtime: MLX through LM Studio
Local runner: lmstudio-cli
Local model id: qwen3-coder-30b-a3b-instruct-mlx
Download approval: not_needed_local
License review status: needs_review
Claimed context window: unknown
Registry scope: model_registry
```

### Source C And D

```text
Candidate ID: 20260605-dolphin-mistral-24b-venice-edition
Model name: Dolphin-Mistral-24B-Venice-Edition
Provider/org: Cognitive Computations / Venice AI
Format/runtime: LM Studio local runtime
Local runner: lmstudio-cli
Local model id: dolphin-mistral-24b-venice-edition
Download approval: not_needed_local
License review status: needs_review
Claimed context window: unknown
Registry scope: model_registry
```

### Source E And F

```text
Project ID: 20260605-llama-cpp
Project name: llama.cpp
Owner: ggml-org
Project URL: https://github.com/ggml-org/llama.cpp
Category: local inference
License: MIT
Status: ready_for_review
Registry scope: project_registry
```

## Candidate Notes

### Candidate: Qwen3-Coder-30B-A3B-Instruct-MLX-4bit

| Field | Value |
| --- | --- |
| Candidate name from source | Qwen3-Coder-30B-A3B-Instruct-MLX-4bit |
| Registry scope | `model_registry` |
| Model family | Qwen |
| Provider or org | lmstudio-community local artifact |
| Parameter count | 30B claimed by local model name |
| Format or runtime | MLX through LM Studio |
| Claimed context window | unknown |
| License | unknown; registry license review remains `needs_review` |
| Local artifact status | Already present in local LM Studio inventory as `qwen3-coder-30b-a3b-instruct-mlx` |
| Security review status | `local_inventory_reviewed` in current registry row |
| Download approval | `not_needed_local` for the already-local artifact only |
| License review status | `needs_review` |
| Provenance status | `local_inventory` |
| Security notes | Treat as local inventory evidence only; do not infer approval for reinstall, update, or alternate artifacts. |
| Isolation notes | Use the exact LM Studio CLI model id only; keep raw benchmark evidence local. |
| Hardware fit | Previously attempted on the 256 GB RAM Mac Studio local lab. |
| Claimed strengths | Current registry notes a completed LM Studio CLI retest with 12/12 prompt responses; source claims are not scores. |
| Risks or caveats | Prior retest notes include workflow advice and privacy guidance issues; do not change dashboard scores from this packet. |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | For any retest or comparison, run `evals/local-llm-benchmark/SPEC.md` via `skills/local-llm-eval` after exact local model id and security gate approval are confirmed. |

### Candidate: Dolphin-Mistral-24B-Venice-Edition

| Field | Value |
| --- | --- |
| Candidate name from source | Dolphin-Mistral-24B-Venice-Edition |
| Registry scope | `model_registry` |
| Model family | Dolphin / Mistral |
| Provider or org | Cognitive Computations / Venice AI |
| Parameter count | 24B claimed by model name |
| Format or runtime | LM Studio local runtime |
| Claimed context window | unknown |
| License | Apache-2.0 in prior source packet metadata; registry license review remains `needs_review` |
| Local artifact status | Already present in local LM Studio inventory as `dolphin-mistral-24b-venice-edition` |
| Security review status | `local_inventory_reviewed` |
| Download approval | `not_needed_local` for the already-local artifact only |
| License review status | `needs_review` |
| Provenance status | `local_inventory` |
| Security notes | Security review approves benchmark execution for the exact local LM Studio id only; it does not approve download, reinstall, update, mirror, or alternate artifact use. |
| Isolation notes | Use LM Studio CLI only and keep raw responses/evidence local. |
| Hardware fit | 24B is plausible on the 256 GB RAM Mac Studio, but hardware fit does not settle artifact safety. |
| Claimed strengths | Prior source packet frames it as a Dolphin/Venice uncensored Mistral 24B collaboration. |
| Risks or caveats | Low-refusal/uncensored framing requires safety, stability, and license review before daily-driver use. |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | Run `evals/local-llm-benchmark/SPEC.md` via `skills/local-llm-eval` through LM Studio CLI after explicit local-run approval. |

### Project: llama.cpp

| Field | Value |
| --- | --- |
| Candidate name from source | llama.cpp |
| Registry scope | `project_registry` |
| Project owner | ggml-org |
| Project URL | https://github.com/ggml-org/llama.cpp |
| Category | local inference |
| Format or runtime | Local GGUF inference runtime and OpenAI-compatible server path, per project registry notes |
| Claimed context window | not applicable |
| License | MIT in project registry row |
| Local artifact status | Project opportunity only; no clone, install, model download, or runtime execution from this packet |
| Security review status | `ready_for_review` as a project, not a model security gate |
| Download approval | not applicable; radar must not install binaries or download models |
| License review status | project license recorded as MIT; integration review still required before adoption |
| Provenance status | project_registry source packet |
| Security notes | Keep as runtime integration review; do not turn this project row into a model score or dashboard eval result. |
| Isolation notes | Any future runtime setup must be a separate explicit task with local-only controls. |
| Hardware fit | Strong fit for the 256 GB RAM Mac Studio according to existing project registry rationale. |
| Claimed strengths | Existing registry notes Apple Silicon optimization, quantization support, and OpenAI-compatible server examples. |
| Risks or caveats | Project radar must not install binaries, clone repositories, download packages, or download models. |
| Suggested radar disposition | `ready_for_review` in `data/project_registry`, not `ready_for_eval` in `data/model_registry` |
| Proposed local eval | None from radar. Review as a runtime integration option before any explicit setup or benchmark-lane task. |

## Reviewer Notes

- This packet is a source packet only. It does not add new registry rows.
- The first two items are model-registry candidates; the llama.cpp item is a
  project-registry opportunity and must not create model eval scores.
- Ready-for-eval model candidates should continue to point to
  `evals/local-llm-benchmark/SPEC.md` and `skills/local-llm-eval`.
- Unknown context-window claims stay unknown.
- Do not create download, install, model execution, dashboard score, or final
  decision steps from this packet without an explicit follow-up task.
