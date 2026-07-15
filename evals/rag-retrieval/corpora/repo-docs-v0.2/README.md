# Repo Docs Retrieval Corpus v0.2

This is the harder real-retrieval corpus for AI Lab OS. It preserves
`repo-docs-v0.1` unchanged as the small regression fixture and expands coverage
to 22 curated, non-private excerpts from the repository's operating agreement,
architecture, ADRs, benchmark methodology, RAG documentation, privacy policy,
runtime strategy, and lab notes.

## Design Intent

The 29 labels are deliberately not an easy keyword quiz:

- competing passages repeat local-first, runtime, privacy, approval, benchmark,
  and retrieval concepts, while some questions label only the passage that
  resolves the specific distinction;
- paraphrases substitute terms such as "authoritative history," "meaning-aware
  search," "scouting lead," and "geometric ranking" for source vocabulary;
- questions 008, 011, 013, 017-020, 023, 025, and 027 require multiple relevant
  chunks for full recall;
- questions 026-028 are intentionally indirect stress cases expected to miss
  or rank poorly in at least some configurations.

The expected-miss designation is a corpus hypothesis, not a recorded result.
No v0.2 retrieval scores are committed or claimed here.

## Stable Label Contract

`labels.json` contains only `query_id`, `query`, and `relevant_chunk_ids` for
each label. Relevance values are UUID chunk IDs produced by the existing
chunker with `chunk_size=900` and `chunk_overlap=120`; labels contain no source
paths, raw passages, keys, prompts, or responses. All corpus excerpts currently
fit in one chunk, making their IDs deterministic from committed content.

Editing corpus text changes its stable chunk ID and requires updating the
corresponding labels. The offline test validates every label against chunks
generated from the committed corpus and does not load an embedding model.

## BGE-M3 Comparison Commands

Run these from the repository root only after local Qdrant is ready and
`bge-m3:latest` is already installed in Ollama. Each collection name below must
be new or empty so stale chunks cannot affect the comparison.

Dense retrieval with the identity reranker:

```bash
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3:latest \
LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \
LOCAL_AI_LAB_QDRANT_COLLECTION=repo_docs_v0_2_bge_m3_dense_identity \
LOCAL_AI_LAB_RERANKER_PROVIDER=identity \
uv run python evals/rag-retrieval/collect.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.2/labels.json \
  --corpus-path evals/rag-retrieval/corpora/repo-docs-v0.2/docs \
  --out evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-dense-identity-results.jsonl \
  --retrieval-mode dense \
  --top-k 5

python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.2/labels.json \
  --results evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-dense-identity-results.jsonl \
  --k 5 \
  > evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-dense-identity-metrics.json
```

Hybrid retrieval with the identity reranker:

```bash
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3:latest \
LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \
LOCAL_AI_LAB_QDRANT_COLLECTION=repo_docs_v0_2_bge_m3_hybrid_identity \
LOCAL_AI_LAB_RERANKER_PROVIDER=identity \
uv run python evals/rag-retrieval/collect.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.2/labels.json \
  --corpus-path evals/rag-retrieval/corpora/repo-docs-v0.2/docs \
  --out evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-hybrid-identity-results.jsonl \
  --retrieval-mode hybrid \
  --top-k 5

python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.2/labels.json \
  --results evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-hybrid-identity-results.jsonl \
  --k 5 \
  > evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-hybrid-identity-metrics.json
```

For cross-encoder runs, install the reviewed optional extra explicitly and set
the path to an already-local cross-encoder artifact. The guard command fails
instead of resolving or downloading a model when the path is absent:

```bash
uv sync --extra rerank
export LOCAL_CROSS_ENCODER_PATH=/absolute/path/to/already-local/cross-encoder
test -e "$LOCAL_CROSS_ENCODER_PATH"
```

Dense retrieval with the cross-encoder reranker:

```bash
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3:latest \
LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \
LOCAL_AI_LAB_QDRANT_COLLECTION=repo_docs_v0_2_bge_m3_dense_cross_encoder \
LOCAL_AI_LAB_RERANKER_PROVIDER=cross_encoder \
LOCAL_AI_LAB_RERANKER_MODEL_PATH="$LOCAL_CROSS_ENCODER_PATH" \
uv run --extra rerank python evals/rag-retrieval/collect.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.2/labels.json \
  --corpus-path evals/rag-retrieval/corpora/repo-docs-v0.2/docs \
  --out evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-dense-cross-encoder-results.jsonl \
  --retrieval-mode dense \
  --top-k 5

python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.2/labels.json \
  --results evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-dense-cross-encoder-results.jsonl \
  --k 5 \
  > evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-dense-cross-encoder-metrics.json
```

Hybrid retrieval with the cross-encoder reranker:

```bash
LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \
LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL=bge-m3:latest \
LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \
LOCAL_AI_LAB_QDRANT_COLLECTION=repo_docs_v0_2_bge_m3_hybrid_cross_encoder \
LOCAL_AI_LAB_RERANKER_PROVIDER=cross_encoder \
LOCAL_AI_LAB_RERANKER_MODEL_PATH="$LOCAL_CROSS_ENCODER_PATH" \
uv run --extra rerank python evals/rag-retrieval/collect.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.2/labels.json \
  --corpus-path evals/rag-retrieval/corpora/repo-docs-v0.2/docs \
  --out evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-hybrid-cross-encoder-results.jsonl \
  --retrieval-mode hybrid \
  --top-k 5

python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/corpora/repo-docs-v0.2/labels.json \
  --results evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-hybrid-cross-encoder-results.jsonl \
  --k 5 \
  > evals/rag-retrieval/corpora/repo-docs-v0.2/bge-m3-hybrid-cross-encoder-metrics.json
```
