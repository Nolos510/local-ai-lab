# Repo Docs Retrieval Corpus v0.1

This corpus contains small, non-private AI Lab OS excerpts for real retrieval
scoring. It is intentionally committed so retrieval changes can be measured
without using private notes.

The label file uses source-aware relevance rows:

```json
{"source_name": "rag-retrieval.md", "chunk_index": 0}
```

Run a local BGE-M3 collection only after Qdrant and Ollama are local and ready:

```bash
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3:latest \
LOCAL_AI_LAB_QDRANT_COLLECTION=repo_docs_v0_1_bge_m3 \
python3 evals/rag-retrieval/collect.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.1/labels.json \
  --corpus-path evals/rag-retrieval/corpora/repo-docs-v0.1/docs \
  --out evals/rag-retrieval/corpora/repo-docs-v0.1/bge-m3-results.jsonl \
  --top-k 5
```
