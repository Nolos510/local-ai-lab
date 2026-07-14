# RAG Answer Evaluation v0.1

This scaffold scores answer/citation output offline. It does not call an LLM,
Qdrant, Ollama, cloud APIs, or model endpoints.

## Label Format

`labels.json` contains:

- `query_id`
- `query`
- `required_citations`: source-aware citation strings such as
  `rag-retrieval.md#chunk_0`
- `required_terms`: terms or phrases expected in the answer
- `forbidden_terms`: terms or phrases that should not appear

## Result Format

Results are JSONL records with:

- `query_id`
- `answer`
- `citations`: list of source-aware citation strings

## Metrics

- `citation_hit_rate`
- `required_term_coverage`
- `forbidden_term_violations`
