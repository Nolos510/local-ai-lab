#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AnswerLabel:
    query_id: str
    query: str
    required_citations: frozenset[str]
    required_terms: tuple[str, ...]
    forbidden_terms: tuple[str, ...]


@dataclass(frozen=True)
class AnswerResult:
    query_id: str
    answer: str
    citations: frozenset[str]


def load_labels(path: Path) -> list[AnswerLabel]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    queries = payload.get("queries")
    if not isinstance(queries, list):
        raise ValueError("labels file must include a queries list")
    labels: list[AnswerLabel] = []
    seen: set[str] = set()
    for index, item in enumerate(queries, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"label {index} must be an object")
        query_id = _required_string(item, "query_id", context=f"label {index}")
        if query_id in seen:
            raise ValueError(f"duplicate query_id in labels: {query_id}")
        seen.add(query_id)
        labels.append(
            AnswerLabel(
                query_id=query_id,
                query=_required_string(item, "query", context=query_id),
                required_citations=frozenset(
                    _required_string_list(item, "required_citations", context=query_id)
                ),
                required_terms=tuple(
                    _required_string_list(item, "required_terms", context=query_id)
                ),
                forbidden_terms=tuple(
                    _required_string_list(item, "forbidden_terms", context=query_id)
                ),
            )
        )
    return labels


def load_results_jsonl(path: Path) -> list[AnswerResult]:
    results: list[AnswerResult] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        if not isinstance(payload, dict):
            raise ValueError(f"result line {line_number} must be an object")
        query_id = _required_string(payload, "query_id", context=f"result line {line_number}")
        if query_id in seen:
            raise ValueError(f"duplicate query_id in results: {query_id}")
        seen.add(query_id)
        results.append(
            AnswerResult(
                query_id=query_id,
                answer=_required_string(payload, "answer", context=query_id),
                citations=frozenset(_required_string_list(payload, "citations", context=query_id)),
            )
        )
    return results


def score_results(labels: list[AnswerLabel], results: list[AnswerResult]) -> dict[str, Any]:
    result_by_query = {result.query_id: result for result in results}
    per_query: list[dict[str, Any]] = []
    citation_total = 0.0
    term_total = 0.0
    violation_total = 0
    for label in labels:
        result = result_by_query.get(label.query_id, AnswerResult(label.query_id, "", frozenset()))
        answer_lower = result.answer.lower()
        citation_hits = label.required_citations.intersection(result.citations)
        term_hits = [term for term in label.required_terms if term.lower() in answer_lower]
        violations = [term for term in label.forbidden_terms if term.lower() in answer_lower]
        citation_rate = len(citation_hits) / len(label.required_citations)
        term_coverage = len(term_hits) / len(label.required_terms)
        citation_total += citation_rate
        term_total += term_coverage
        violation_total += len(violations)
        per_query.append(
            {
                "query_id": label.query_id,
                "citation_hit_rate": citation_rate,
                "required_term_coverage": term_coverage,
                "forbidden_term_violations": len(violations),
            }
        )
    query_count = len(labels)
    return {
        "query_count": query_count,
        "citation_hit_rate": citation_total / query_count if query_count else 0.0,
        "required_term_coverage": term_total / query_count if query_count else 0.0,
        "forbidden_term_violations": violation_total,
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score RAG answer/citation rows offline.")
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    metrics = score_results(load_labels(args.labels), load_results_jsonl(args.results))
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


def _required_string(payload: dict[str, Any], key: str, *, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} must include a non-empty string field '{key}'")
    return value


def _required_string_list(payload: dict[str, Any], key: str, *, context: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{context} must include a list of non-empty strings in '{key}'")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
