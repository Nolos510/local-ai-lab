# Model Security Review: Dolphin-Mistral-24B-Venice-Edition

Review date: 2026-06-05  
Reviewer: Codex  
Candidate ID: `20260605-dolphin-mistral-24b-venice-edition`  
Outcome: `needs_review`  
Download approval: `not_approved`

## Candidate

- Model name: `Dolphin-Mistral-24B-Venice-Edition`
- Provider/org: Cognitive Computations / Venice AI
- Family: Dolphin / Mistral
- Size: 24B in source name
- Source packet: `automations/ai-lab-radar/inputs/2026-06-05-abliterated-dolphin-shortlist.md`
- Radar report: `automations/ai-lab-radar/reports/2026-06-05-abliterated-dolphin-shortlist.md`

## Provenance

Reviewed source metadata names the upstream Hugging Face model card:

```text
https://huggingface.co/dphn/Dolphin-Mistral-24B-Venice-Edition
```

The current registry row is source-metadata-only. No concrete local artifact,
mirror, quantizer package, file list, checksum, or runtime inventory entry has
been approved.

## License

Reviewed metadata records Apache-2.0 from the source packet. The license must
be rechecked on the exact artifact selected for local use before approval.

## Format And Runtime

- Source model: not approved for direct execution.
- Local artifact: not selected.
- Runtime path: not selected.
- LM Studio local model id: not visible.
- Ollama model id: not visible.
- llama.cpp/GGUF path: not selected.

Preferred path is a concrete local quantized artifact that LM Studio, Ollama, or
llama.cpp can load without executing upstream model-card code.

## Hash / Checksum Evidence

No checksum, hash, release digest, or file-list evidence has been captured for a
specific local artifact. This blocks download approval.

## Red Flags And Caveats

- Dolphin/uncensored framing increases behavior and safety-review importance.
- A 24B model is feasible on the target 256 GB RAM machine, but hardware fit is
  not the same as artifact safety.
- Do not run repository scripts, notebooks, custom loaders, or model-card code.
- Do not convert source claims into scores.

## Approval State

This candidate may remain visible in Radar and Specialty views as a queued
target, but it is not approved to download, install, update, or benchmark.

Approval requires:

1. A specific local artifact path or runtime package.
2. Explicit license confirmation for that artifact.
3. File-list or checksum/hash evidence when available.
4. Exact local runtime id from `lms ls --json`, `lms ps --json`, `ollama list`,
   or an equivalent local inventory command.
5. Updated registry row with `security_review_status=reviewed` and
   `download_approval=approved` for that exact artifact only.
