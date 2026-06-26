# Model Security Review: Dolphin-Mistral-24B-Venice-Edition

Review date: 2026-06-05
Reviewer: Codex
Candidate ID: `20260605-dolphin-mistral-24b-venice-edition`
Outcome: `local_inventory_reviewed`
Download approval: `not_needed_local`

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

The original registry row was source-metadata-only. A later local inventory
refresh detected an already-installed LM Studio model with exact runtime id:

```text
dolphin-mistral-24b-venice-edition
```

This review approves benchmark execution for that exact local runtime id only.
It does not approve any new download, reinstall, update, mirror, or alternate
artifact.

## License

Reviewed metadata records Apache-2.0 from the source packet. The already-local
runtime item may be benchmarked, but license status remains `needs_review` for
any keep/share/reinstall decision.

## Format And Runtime

- Source model: not approved for direct execution or download.
- Local artifact: already installed in LM Studio local inventory.
- Runtime path: managed by LM Studio; do not commit private absolute paths.
- LM Studio local model id: `dolphin-mistral-24b-venice-edition`.
- Ollama model id: not visible.
- llama.cpp/GGUF path: not selected.

Approved execution path for v1 is LM Studio CLI only:

```text
lms chat dolphin-mistral-24b-venice-edition --stats --yes --dont-fetch-catalog
```

The benchmark runner must preserve raw responses and evidence locally.

## Hash / Checksum Evidence

No checksum, hash, release digest, or file-list evidence has been captured for a
downloadable artifact. This still blocks download/reinstall/update approval, but
does not block benchmarking the already-installed local runtime id.

## Red Flags And Caveats

- Dolphin/uncensored framing increases behavior and safety-review importance.
- A 24B model is feasible on the target 256 GB RAM machine, but hardware fit is
  not the same as artifact safety.
- Do not run repository scripts, notebooks, custom loaders, or model-card code.
- Do not download, reinstall, update, or switch artifacts under this approval.
- Do not convert source claims into scores.

## Approval State

This candidate may be benchmarked through the exact local LM Studio CLI id
`dolphin-mistral-24b-venice-edition`. It is not approved to download, install,
update, or benchmark under any other runtime id or artifact.

Any future download/reinstall/update approval requires:

1. A specific local artifact path or runtime package.
2. Explicit license confirmation for that artifact.
3. File-list or checksum/hash evidence when available.
4. Exact local runtime id from `lms ls --json`, `lms ps --json`, `ollama list`,
   or an equivalent local inventory command.
5. Updated registry row with download approval for that exact artifact only.
