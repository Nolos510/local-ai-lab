# RAG Retrieval Eval Spec v0.1

Status: initial offline fixture

Target: Local RAG Backbone retrieval quality

Metrics: `recall@k`, `MRR`

## Goal

Measure whether retrieval returns the chunks that a small labeled set expects
before changing ranking behavior. This eval is intentionally tiny and fully
offline so it can run in CI without Qdrant, Ollama, local models, or network
access.

The fixture is not a benchmark of a real corpus. It is a regression harness for
retrieval plumbing, scorer behavior, and later RAG Quality sprint loops.

## Files

```text
evals/rag-retrieval/
  SPEC.md
  scorer.py
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
live Qdrant/BGE-M3 retrieval runs as manual smoke checks unless a future loop
adds a dedicated local fixture export command.
