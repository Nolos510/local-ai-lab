# Local-First Rules

AI Lab OS keeps model evaluation and retrieval private by default. Agents must
not add hidden cloud calls, cloud API clients, model download logic, telemetry,
or secrets. External radar metadata can describe candidate models, but it must
not become scores or dashboard decisions without explicit review.

Qdrant is the v0 vector database. Ollama, LM Studio, MLX-LM, and llama.cpp are
treated as native macOS runtimes. Live model execution is gated by an exact
local runtime id and explicit approval.
