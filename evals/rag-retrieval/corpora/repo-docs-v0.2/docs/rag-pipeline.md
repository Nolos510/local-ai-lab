# RAG Pipeline And Evaluation

Markdown and text sources are loaded, divided into stable source-aware chunks,
embedded, stored in Qdrant, retrieved with dense or opt-in hybrid search,
optionally reranked, and assembled into a cited prompt for a local provider.
Identity ranking and deterministic embeddings keep the default test path
offline.

The retrieval scorer reads saved IDs and reports recall at a cutoff plus mean
reciprocal rank. It never calls Qdrant, Ollama, an LLM, a cloud API, or a model
endpoint. Live BGE-M3 collection is a separate manual local check; a tiny
fixture proves plumbing, not real-corpus retrieval quality.
