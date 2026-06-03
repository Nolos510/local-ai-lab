# AI Lab Radar Source Packet

Packet title: Real local candidate from first benchmark attempt
Packet date: 2026-06-03
Prepared by: Codex
Approved for radar review: yes
Safe to commit: yes

## Scope

This packet covers one installed local model observed in the first local
benchmark attempt. Source material is limited to committed repo-local benchmark
artifacts and lab notes. No web pages were fetched, no model card claims were
added, and no external source claims were inferred.

## Source References

| Source ID | Source type | Source date | Link or local reference | Notes |
| --- | --- | --- | --- | --- |
| A | local benchmark artifact | 2026-06-03 | `data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit/metadata.json` | Records model name, backend, format, quantization, hardware, and benchmark artifact paths. |
| B | local evidence note | 2026-06-03 | `data/eval_results/20260603-qwen3-coder-30b-a3b-lmstudio-mlx-4bit/evidence.md` | Records local LM Studio model path and runtime failure. |
| C | lab note | 2026-06-03 | `docs/lab-notes/first-local-benchmark-result-qwen3-coder.md` | Summarizes failed-runtime benchmark attempt and `retest` decision. |

## Copied Notes Or Excerpts

### Source A

```text
Model name: Qwen3-Coder-30B-A3B-Instruct-MLX-4bit
Backend: LM Studio
Format: MLX
Quantization: 4bit
Hardware: Mac Studio Apple M3 Ultra, 32-core CPU, 256 GB RAM, macOS 26.3.1
Prompt set: ai-lab-local-llm-core-v0.1
Rubric version: ai-lab-local-llm-rubric-v0.1
```

### Source B

```text
Candidate source: local LM Studio model files at
/Users/nolos/.lmstudio/models/lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-MLX-4bit.

Failure evidence: LM Studio CLI reported Timed out waiting for LM Studio daemon
to start and Failed to start or connect to local LM Studio API server.
```

### Source C

```text
This run is a failed-runtime benchmark attempt, not a scored model evaluation.
LM Studio did not start or expose the local server during the run, so no prompts
were executed and no model responses were captured.

Decision: retest
Retest condition: rerun after LM Studio daemon/server starts and the installed
local model can answer the full prompt set.
```

## Candidate Notes

### Candidate: Qwen3-Coder-30B-A3B-Instruct-MLX-4bit

| Field | Value |
| --- | --- |
| Candidate name from source | Qwen3-Coder-30B-A3B-Instruct-MLX-4bit |
| Model family | Qwen |
| Provider or org | lmstudio-community local artifact |
| Parameter count | 30B claimed by local model name |
| Format or runtime | MLX through LM Studio |
| Claimed context window | unknown |
| License | unknown |
| Local artifact status | Installed local LM Studio model path recorded in benchmark evidence |
| Hardware fit | Attempted on Mac Studio Apple M3 Ultra, 256 GB RAM |
| Claimed strengths | None added from external sources in this packet |
| Risks or caveats | LM Studio daemon/server failed before prompt execution; no model responses captured; no score or final label exists |
| Suggested radar disposition | `ready_for_eval` |
| Proposed local eval | Retest with `evals/local-llm-benchmark/SPEC.md` after LM Studio local server responds on the approved local endpoint |

## Reviewer Notes

- This is a local artifact candidate, not a source-claim candidate.
- Do not create eval scores until a successful prompt run produces model output.
- Keep the existing failed-runtime benchmark attempt as evidence for the
  `retest` decision.
- Next local action is runtime repair, not model discovery.
