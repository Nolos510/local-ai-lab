#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class QueryLabel:
    query_id: str
    query: str
    relevant_chunk_ids: frozenset[str]


@dataclass(frozen=True)
class QueryResult:
    query_id: str
    retrieved_chunk_ids: tuple[str, ...]


def load_labels(path: Path) -> list[QueryLabel]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    queries = payload.get("queries")
    if not isinstance(queries, list):
        msg = "labels file must contain a 'queries' list"
        raise ValueError(msg)
    labels: list[QueryLabel] = []
    seen: set[str] = set()
    for index, item in enumerate(queries, start=1):
        if not isinstance(item, dict):
            msg = f"query label at index {index} must be an object"
            raise ValueError(msg)
        query_id = _required_string(item, "query_id", context=f"query label {index}")
        if query_id in seen:
            msg = f"duplicate query_id in labels: {query_id}"
            raise ValueError(msg)
        seen.add(query_id)
        query = _required_string(item, "query", context=query_id)
        relevant_ids = _required_string_list(item, "relevant_chunk_ids", context=query_id)
        if not relevant_ids:
            msg = f"{query_id} must have at least one relevant chunk id"
            raise ValueError(msg)
        labels.append(
            QueryLabel(
                query_id=query_id,
                query=query,
                relevant_chunk_ids=frozenset(relevant_ids),
            )
        )
    return labels


def load_results_jsonl(path: Path) -> list[QueryResult]:
    results: list[QueryResult] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            msg = f"result line {line_number} must be an object"
            raise ValueError(msg)
        query_id = _required_string(payload, "query_id", context=f"result line {line_number}")
        if query_id in seen:
            msg = f"duplicate query_id in results: {query_id}"
            raise ValueError(msg)
        seen.add(query_id)
        retrieved_ids = _required_string_list(payload, "retrieved_chunk_ids", context=query_id)
        results.append(QueryResult(query_id=query_id, retrieved_chunk_ids=tuple(retrieved_ids)))
    return results


def score_results(
    labels: list[QueryLabel],
    results: list[QueryResult],
    *,
    k: int,
) -> dict[str, Any]:
    if k < 1:
        msg = "k must be >= 1"
        raise ValueError(msg)
    result_by_query = {result.query_id: result for result in results}
    per_query: list[dict[str, Any]] = []
    recall_total = 0.0
    reciprocal_rank_total = 0.0

    for label in labels:
        result = result_by_query.get(label.query_id, QueryResult(label.query_id, ()))
        ranked_ids = _dedupe_preserving_order(result.retrieved_chunk_ids[:k])
        relevant_hits = [
            chunk_id for chunk_id in ranked_ids if chunk_id in label.relevant_chunk_ids
        ]
        recall = len(set(relevant_hits)) / len(label.relevant_chunk_ids)
        reciprocal_rank = _reciprocal_rank(ranked_ids, label.relevant_chunk_ids)
        recall_total += recall
        reciprocal_rank_total += reciprocal_rank
        per_query.append(
            {
                "query_id": label.query_id,
                "relevant_count": len(label.relevant_chunk_ids),
                "retrieved_count_at_k": len(ranked_ids),
                "hit_count_at_k": len(set(relevant_hits)),
                "recall_at_k": recall,
                "reciprocal_rank": reciprocal_rank,
            }
        )

    query_count = len(labels)
    return {
        "query_count": query_count,
        "k": k,
        "recall_at_k": recall_total / query_count if query_count else 0.0,
        "mrr": reciprocal_rank_total / query_count if query_count else 0.0,
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score RAG retrieval results offline.")
    parser.add_argument("--labels", type=Path, required=True, help="Path to labels.json")
    parser.add_argument("--results", type=Path, required=True, help="Path to results JSONL")
    parser.add_argument("--k", type=int, default=5, help="Rank cutoff for recall@k and MRR")
    args = parser.parse_args()

    metrics = score_results(
        load_labels(args.labels),
        load_results_jsonl(args.results),
        k=args.k,
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


def _required_string(payload: dict[str, Any], key: str, *, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        msg = f"{context} must include a non-empty string field '{key}'"
        raise ValueError(msg)
    return value


def _required_string_list(payload: dict[str, Any], key: str, *, context: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        msg = f"{context} must include a list of non-empty strings in '{key}'"
        raise ValueError(msg)
    return value


def _dedupe_preserving_order(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return tuple(deduped)


def _reciprocal_rank(
    ranked_ids: tuple[str, ...],
    relevant_chunk_ids: frozenset[str],
) -> float:
    for index, chunk_id in enumerate(ranked_ids, start=1):
        if chunk_id in relevant_chunk_ids:
            return 1.0 / index
    return 0.0


if __name__ == "__main__":
    raise SystemExit(main())
