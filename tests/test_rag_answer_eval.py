from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCORER_PATH = ROOT / "evals" / "rag-answer" / "scorer.py"


def _load_scorer() -> Any:
    spec = importlib.util.spec_from_file_location("rag_answer_scorer", SCORER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_fixture_scores_answer_citations_offline() -> None:
    scorer = _load_scorer()
    metrics = scorer.score_results(
        scorer.load_labels(ROOT / "evals/rag-answer/fixtures/labels.json"),
        scorer.load_results_jsonl(ROOT / "evals/rag-answer/fixtures/results.jsonl"),
    )

    assert metrics["query_count"] == 2
    assert metrics["citation_hit_rate"] == pytest.approx(1.0)
    assert metrics["required_term_coverage"] == pytest.approx(1.0)
    assert metrics["forbidden_term_violations"] == 0


def test_answer_scorer_counts_missing_result_as_zero() -> None:
    scorer = _load_scorer()
    labels = [
        scorer.AnswerLabel(
            query_id="q1",
            query="What is cited?",
            required_citations=frozenset({"a.md#chunk_0"}),
            required_terms=("local",),
            forbidden_terms=("public upload",),
        )
    ]

    metrics = scorer.score_results(labels, [])

    assert metrics["citation_hit_rate"] == 0.0
    assert metrics["required_term_coverage"] == 0.0
    assert metrics["forbidden_term_violations"] == 0
