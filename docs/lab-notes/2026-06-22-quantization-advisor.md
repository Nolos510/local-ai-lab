# Quantization Advisor

## Summary

AI Lab OS now includes a local-first quantization advisor for planning GGUF
artifact selection before a model is installed or benchmarked.

The advisor is exposed as:

```bash
uv run ai-lab quant advise --repo-id deepseek-ai/DeepSeek-R1-0528-Qwen3-8B
```

Default mode is local-only. Public Hugging Face metadata lookup is available
only when the user explicitly adds `--lookup-hf`.

## Safety Boundary

- The advisor does not download, install, run, or score models.
- It does not use Hugging Face SDKs, API tokens, secrets, or cloud inference.
- Saved advice under `data/model_registry/quant_advice/` is candidate metadata,
  not an eval score or install approval.
- Recommendations such as `Q5_K_M`, `Q6_K`, or `Q4_K_M` are hypotheses until a
  reviewed exact local runtime model id is benchmarked through
  `evals/local-llm-benchmark`.
- Dashboard rendering reads saved JSON advice only and performs no external
  network lookup.

## Practical Use

For an 8B model on the 256 GB Apple Silicon target, the advisor treats
`Q5_K_M` as the balanced starting point, `Q6_K` and `Q8_0` as quality-first
comparison options, and `Q4_K_M` / `Q4_K_XL` / `UD-Q4_K_XL` as faster or
smaller alternatives. Sub-4-bit and IQ quants are kept as fit-constrained
fallbacks, not the default for this hardware class.

The next step after choosing a candidate quant is still the existing local
benchmark workflow: verify source, license, provenance, exact local model id,
and runtime isolation, then run an explicitly approved local benchmark.
