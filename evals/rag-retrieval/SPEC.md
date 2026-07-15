# RAG Retrieval Eval Spec v0.1

Status: offline regression fixture plus manual real-retrieval corpora

Target: Local RAG Backbone retrieval quality

Metrics: `recall@k`, `MRR`

## Goal

Measure whether retrieval returns the chunks that a small labeled set expects
before changing ranking behavior. This eval is intentionally tiny and fully
offline so it can run in CI without Qdrant, Ollama, local models, or network
access.

The offline fixture is not a benchmark of a real corpus. It is a regression
harness for retrieval plumbing and scorer behavior. Committed repo-docs corpora
provide separate manual real-embedding comparisons:

- `repo-docs-v0.1` remains the four-query regression baseline with its observed
  BGE-M3 evidence intact.
- `repo-docs-v0.2` adds 29 deliberately hard labels over a larger slice of
  non-private repository documentation. It includes competing passages,
  vocabulary gaps, paraphrases, multiple-relevance labels, and expected misses.

## Files

```text
evals/rag-retrieval/
  SPEC.md
  collect.py
  scorer.py
  corpora/
    repo-docs-v0.1/
    repo-docs-v0.2/
  fixtures/
    labels.json
    deterministic-results.jsonl
```

## Label Format

`fixtures/labels.json` records each query and the relevant chunk IDs:

```json
{
  "queries": [
    {
      "query_id": "RAGRET-v0.1-001",
      "query": "What keeps the lab local-first?",
      "relevant_chunk_ids": ["sample-local-first-0000"]
    }
  ]
}
```

Labels use stable chunk IDs only. They must not include private source paths,
raw document text, prompts, API keys, or model responses.

The v0.1 real-retrieval corpus predates the ID-only corpus contract and retains
source-aware rows as an unchanged regression fixture. New v0.2 relevance labels
use `relevant_chunk_ids` only. Its README documents the fixed chunk settings and
the exact four-way BGE-M3 collection/scoring matrix.

## Result Format

`fixtures/deterministic-results.jsonl` is one JSON object per query:

```json
{"query_id": "RAGRET-v0.1-001", "retrieved_chunk_ids": ["sample-local-first-0000"]}
```

Result rows may come from fake retrieval providers, deterministic embeddings,
or exported local retrieval runs. The scorer reads IDs only; it does not call
Qdrant, Ollama, an LLM, cloud APIs, or model endpoints.

## Metrics

- `recall@k`: per-query fraction of labeled relevant chunk IDs present in the
  top `k`, averaged across all labeled queries.
- `MRR`: reciprocal rank of the first relevant chunk in the top `k`, averaged
  across all labeled queries.

Missing result rows count as empty retrieval results.

## Offline Command

```bash
python3 evals/rag-retrieval/scorer.py \
  --labels evals/rag-retrieval/fixtures/labels.json \
  --results evals/rag-retrieval/fixtures/deterministic-results.jsonl \
  --k 2
```

The command prints JSON with aggregate metrics and per-query evidence. Keep
live Qdrant/BGE-M3 retrieval runs as manual smoke checks. `collect.py` exports
those local results without calling an answer model; it is not part of the
offline test gate.
