# Local Semantic Embedding Decision

The deterministic hash provider stays the default for reproducible offline
tests, but it does not measure meaning. Real semantic retrieval uses Ollama's
local `/api/embed` endpoint with BGE-M3 only after the operator selects the
Ollama embedding provider. This adds no cloud call, SDK client, secret, or
automatic model download.

BGE-M3 vectors use 1024 dimensions. A Qdrant collection created with the
384-dimensional deterministic provider must be recreated before switching;
the collection's vector size is fixed and mixing models or dimensions would
invalidate retrieval quality.
