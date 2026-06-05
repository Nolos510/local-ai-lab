# Local Qwen3 30B LM Studio Candidate Source Packet

Date: 2026-06-05
Reviewer: Codex

Approved for radar review: yes
Safe to commit: yes

## Source Boundary

This packet uses local operator notes and local LM Studio inventory checks only.
No models were downloaded, no model APIs outside localhost were called, no cloud
APIs were used, and no secrets were recorded.

## User-Approved Note

The user reported that LM Studio shows `Qwen3-30B-A3B-Instruct` and clarified
that it does not appear to be an abliterated model.

## Local Inventory Evidence

Observed local checks on 2026-06-05:

- Local working machine has LM Studio CLI available at `~/.lmstudio/bin/lms`.
- `lms ls --json` currently exposes one loaded LLM:
  `qwen3-coder-30b-a3b-instruct-mlx`.
- `lms ps --json` reports the loaded model display name as
  `Qwen3 Coder 30B A3B Instruct`.
- The exact vanilla model id `Qwen3-30B-A3B-Instruct` was not visible through
  the CLI inventory at the time of this packet.
- `http://127.0.0.1:1234/v1/models` was reachable after local network approval,
  but returned `401 Unauthorized`, so the OpenAI-compatible runner could not
  confirm the exact model list without a local auth path.

## Candidate

| Field | Value |
| --- | --- |
| Candidate ID | `20260605-qwen3-30b-a3b-instruct-lmstudio` |
| Model name | `Qwen3-30B-A3B-Instruct` |
| Provider/org | Local LM Studio inventory |
| Model family | Qwen3 |
| Runtime hint | LM Studio local OpenAI-compatible endpoint |
| Proposed run ID | `20260605-qwen3-30b-a3b-instruct-lmstudio-r1` |
| Proposed eval | Local LLM benchmark core v0.1 |

## Why Interesting

The model is a 30B-class Qwen candidate that should fit the 256 GB RAM local lab
well and gives the v1 loop a large non-abliterated comparison point against the
existing Qwen3 Coder result.

## Risks And Caveats

- Exact runtime identity is unresolved.
- Current CLI inventory exposes the Coder variant, not the vanilla model.
- Do not import scores until the exact model id is confirmed and benchmarked.
- Do not relabel this as abliterated.

## Recommended Next Step

Confirm the exact model id through LM Studio's OpenAI-compatible endpoint or CLI
inventory. If `Qwen3-30B-A3B-Instruct` is visible, run:

```bash
python3 evals/local-llm-benchmark/harness.py init-run \
  --benchmark-run-id 20260605-qwen3-30b-a3b-instruct-lmstudio-r1 \
  --model-name "Qwen3-30B-A3B-Instruct" \
  --backend "LM Studio" \
  --format "Local OpenAI-compatible" \
  --quantization "not reported" \
  --hardware "Mac Studio Apple M3 Ultra, 32-core CPU, 256 GB RAM, macOS 26.3.1" \
  --temperature 0.2 \
  --top-p 0.9
```
