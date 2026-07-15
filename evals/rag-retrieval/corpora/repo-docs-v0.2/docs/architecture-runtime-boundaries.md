# Architecture Runtime Boundaries

Docker is reserved for local infrastructure services: Qdrant and optional Open
WebUI. Model runtimes remain native on macOS: Ollama, LM Studio, MLX/MLX-LM,
and llama.cpp. Open WebUI is a parallel chat surface rather than a dependency
of the FastAPI RAG harness.

The system talks to local runtimes only when explicitly configured. Radar,
dashboard views, and benchmark planning must not introduce hidden cloud calls,
automatic installs, model download logic, telemetry, secrets, or cloud SDKs.
Runtime-boundary changes require an architecture decision record.
