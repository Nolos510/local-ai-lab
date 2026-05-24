# RAG Pipeline

The v0 RAG pipeline is intentionally simple:

```text
markdown/text source
  -> load documents
  -> chunk with metadata
  -> embed chunks
  -> index in Qdrant
  -> retrieve top-k chunks
  -> assemble prompt with citations
  -> generate answer with local model
```

## Current Capabilities

- Markdown and plain text ingestion.
- Stable chunk IDs.
- Source path, source name, source hash, and chunk index metadata.
- Deterministic embedding provider for repeatable development.
- Qdrant vector search.

## TODO

- [ ] Add BGE-M3 embedding provider.
- [ ] Add hybrid dense/sparse retrieval.
- [ ] Add reranker abstraction.
- [ ] Add retrieval evaluation datasets.
- [ ] Add citation rendering helpers.
- [ ] Add parser version tracking.
