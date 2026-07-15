# Native Model Runtime Decision

Use Docker for infrastructure such as Qdrant and Open WebUI, but keep Ollama,
LM Studio, MLX/MLX-LM, and llama.cpp native on macOS. Keep the FastAPI and CLI
harness native through `uv`, use Qdrant as the v0 vector database, and treat
Open WebUI as optional rather than required by RAG.

An all-in-Docker design was rejected because containerizing inference adds
complexity and may interfere with the normal Apple Silicon acceleration paths
used by the supported local runtimes. Future changes to these boundaries must
be recorded in an ADR.
