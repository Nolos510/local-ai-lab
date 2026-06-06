# Model Security Vetting

AI Lab OS treats model recommendations as leads, not install approval. Radar can
say a model is interesting, but the security gate decides whether it is approved
to download, update, or run locally.

## Default Posture

- External candidates default to `security_review_status=needs_review`.
- External candidates default to `download_approval=not_approved`.
- Popularity, likes, stars, downloads, or benchmark claims do not make a model
  safe.
- Links to Hugging Face, GitHub, LM Studio, or Ollama are source-tracing
  metadata only until the user approves an install or run task.

## Screening Checklist

Before approving a new model artifact:

1. Confirm provenance: official publisher, mirror, quantizer, or known local
   artifact.
2. Confirm license: record the explicit license and any use restrictions.
3. Confirm artifact format: prefer GGUF, MLX, Safetensors, Ollama, LM Studio,
   or llama.cpp paths that load weights without upstream code execution.
4. Confirm runtime path: use a local runtime with loopback/private-LAN access
   only.
5. Check for red flags: custom code, pickled weights, install scripts,
   notebooks, unclear publisher chain, missing license, or mismatched local
   inventory name.
6. Record checksum/hash, release metadata, or file-list evidence when available.
7. Record isolation notes before the benchmark run.

## Dashboard Meanings

`security_review_status` is due diligence state:

- `unreviewed`: no explicit screening notes yet.
- `needs_review`: interesting, but not approved for download or update.
- `local_inventory_reviewed`: already local; no new download approval implied.
- `reviewed`: source, license, artifact, and runtime path have been reviewed.
- `blocked`: do not download, install, update, or run without a new approval.

`download_approval` is action state:

- `not_approved`: no download, install, or update.
- `not_needed_local`: already installed locally; still review before updating.
- `approved`: approved for the specific artifact and runtime path recorded.
- `blocked`: blocked until a security issue is resolved.

## Boundaries

Do not run model-card code, repository scripts, custom Python loaders, install
scripts, or notebooks as part of radar review. If a candidate requires those
steps, keep it `needs_review` or `blocked` and open a separate security task.
