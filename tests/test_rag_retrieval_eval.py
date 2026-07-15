from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

from local_ai_lab.ingestion.chunking import chunk_documents
from local_ai_lab.ingestion.documents import load_documents

ROOT = Path(__file__).resolve().parents[1]
COLLECT_PATH = ROOT / "evals" / "rag-retrieval" / "collect.py"
SCORER_PATH = ROOT / "evals" / "rag-retrieval" / "scorer.py"
V0_2_ROOT = ROOT / "evals" / "rag-retrieval" / "corpora" / "repo-docs-v0.2"


def _load_scorer() -> Any:
    spec = importlib.util.spec_from_file_location("rag_retrieval_scorer", SCORER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_collector() -> Any:
    spec = importlib.util.spec_from_file_location("rag_retrieval_collector", COLLECT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_fixture_scores_recall_and_mrr_offline() -> None:
    scorer = _load_scorer()

    labels = scorer.load_labels(ROOT / "evals/rag-retrieval/fixtures/labels.json")
    results = scorer.load_results_jsonl(
        ROOT / "evals/rag-retrieval/fixtures/deterministic-results.jsonl"
    )
    metrics = scorer.score_results(labels, results, k=2)

    assert metrics["query_count"] == 3
    assert metrics["k"] == 2
    assert metrics["recall_at_k"] == pytest.approx(0.5)
    assert metrics["mrr"] == pytest.approx(0.5)
    assert [row["query_id"] for row in metrics["per_query"]] == [
        "RAGRET-v0.1-001",
        "RAGRET-v0.1-002",
        "RAGRET-v0.1-003",
    ]


def test_scorer_counts_missing_result_rows_as_empty_retrieval() -> None:
    scorer = _load_scorer()
    labels = [
        scorer.QueryLabel(
            query_id="q1",
            query="Where is the local vector store?",
            relevant_chunk_ids=frozenset({"chunk-qdrant"}),
            relevant_sources=frozenset(),
        )
    ]

    metrics = scorer.score_results(labels, [], k=5)

    assert metrics["recall_at_k"] == 0.0
    assert metrics["mrr"] == 0.0
    assert metrics["per_query"][0]["hit_count_at_k"] == 0


def test_scorer_validates_duplicate_result_ids(tmp_path: Path) -> None:
    scorer = _load_scorer()
    results_path = tmp_path / "results.jsonl"
    results_path.write_text(
        "\n".join(
            [
                json.dumps({"query_id": "q1", "retrieved_chunk_ids": ["a"]}),
                json.dumps({"query_id": "q1", "retrieved_chunk_ids": ["b"]}),
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate query_id"):
        scorer.load_results_jsonl(results_path)


def test_source_aware_fixture_scores_repo_docs_labels(tmp_path: Path) -> None:
    scorer = _load_scorer()
    labels_path = ROOT / "evals/rag-retrieval/corpora/repo-docs-v0.1/labels.json"
    results_path = tmp_path / "results.jsonl"
    results_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "query_id": "REPO-RAG-v0.1-001",
                        "retrieved": [
                            {"source_name": "local-first-rules.md", "chunk_index": 0}
                        ],
                    }
                ),
                json.dumps(
                    {
                        "query_id": "REPO-RAG-v0.1-002",
                        "retrieved": [
                            {"source_name": "rag-retrieval.md", "chunk_index": 0},
                            {"source_name": "local-first-rules.md", "chunk_index": 0},
                        ],
                    }
                ),
                json.dumps(
                    {
                        "query_id": "REPO-RAG-v0.1-003",
                        "retrieved": [
                            {"source_name": "dashboard-loop.md", "chunk_index": 0}
                        ],
                    }
                ),
                json.dumps(
                    {
                        "query_id": "REPO-RAG-v0.1-004",
                        "retrieved": [
                            {"source_name": "rag-retrieval.md", "chunk_index": 0}
                        ],
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    metrics = scorer.score_results(
        scorer.load_labels(labels_path),
        scorer.load_results_jsonl(results_path),
        k=5,
    )

    assert metrics["query_count"] == 4
    assert metrics["recall_at_k"] == pytest.approx(1.0)
    assert metrics["mrr"] == pytest.approx(1.0)


def test_repo_docs_v0_2_labels_are_stable_id_only_and_match_corpus() -> None:
    payload = json.loads((V0_2_ROOT / "labels.json").read_text(encoding="utf-8"))
    queries = payload["queries"]

    assert payload["corpus_id"] == "repo-docs-v0.2"
    assert 20 <= len(queries) <= 30
    assert len({item["query_id"] for item in queries}) == len(queries)
    assert sum(len(item["relevant_chunk_ids"]) > 1 for item in queries) >= 5

    chunks = chunk_documents(
        load_documents(V0_2_ROOT / "docs"),
        chunk_size=900,
        chunk_overlap=120,
    )
    corpus_chunk_ids = {chunk.id for chunk in chunks}

    for item in queries:
        assert set(item) == {"query_id", "query", "relevant_chunk_ids"}
        assert item["query_id"].startswith("REPO-RAG-v0.2-")
        assert item["query"].strip()
        assert item["relevant_chunk_ids"]
        for chunk_id in item["relevant_chunk_ids"]:
            assert str(uuid.UUID(chunk_id)) == chunk_id
            assert chunk_id in corpus_chunk_ids


def test_existing_collector_loads_repo_docs_v0_2_queries_offline() -> None:
    collector = _load_collector()

    queries = collector._load_queries(V0_2_ROOT / "labels.json")

    assert len(queries) == 29
    assert queries[0]["query_id"] == "REPO-RAG-v0.2-001"
    assert queries[-1]["query_id"] == "REPO-RAG-v0.2-029"
