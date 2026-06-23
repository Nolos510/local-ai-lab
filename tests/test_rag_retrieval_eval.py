from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCORER_PATH = ROOT / "evals" / "rag-retrieval" / "scorer.py"


def _load_scorer() -> Any:
    spec = importlib.util.spec_from_file_location("rag_retrieval_scorer", SCORER_PATH)
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
