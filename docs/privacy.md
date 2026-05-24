# Privacy-First Local Workflows

The default posture is local-first and private.

## Defaults

- Keep raw data under `data/`.
- Keep model artifacts under `models/`.
- Keep generated reports under `reports/`.
- Run Qdrant and Open WebUI locally.
- Run Ollama, LM Studio, MLX-LM, and llama.cpp natively on macOS.

## Logging Discipline

Future request logs should include:

- request ID
- model ID
- runtime provider
- prompt template version
- retrieved chunk IDs
- reranker scores when reranking exists
- token counts
- latency
- evaluation labels where available

Do not log secrets or private raw documents into external services by default.
