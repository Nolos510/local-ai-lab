# Local-First Operating Rules

Do not add hidden cloud calls, cloud API clients, model download logic, or
secrets. Open WebUI stays optional and parallel; the FastAPI RAG harness must
not depend on it. Qdrant is the v0 vector database, while Ollama, LM Studio,
MLX/MLX-LM, and llama.cpp are native macOS tools by default.

Logs must not dump user documents, prompts, retrieved chunks, API keys, or
private paths. External Radar may gather public metadata on demand, but it may
not download models, run models, call model APIs, or register a candidate
without explicit approval. Radar candidates are review records, not eval
scores.
