import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

RRF_RANK_CONSTANT = 60
SUPPORTED_RETRIEVAL_MODES = {"dense", "hybrid"}
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    text: str
    score: float
    metadata: dict[str, Any]


def validate_retrieval_mode(mode: str) -> str:
    normalized = mode.lower()
    if normalized in SUPPORTED_RETRIEVAL_MODES:
        return normalized
    msg = f"unsupported retrieval mode: {mode}"
    raise ValueError(msg)


def lexical_rank_chunks(
    query: str,
    chunks: list[RetrievedChunk],
    *,
    limit: int,
) -> list[RetrievedChunk]:
    """Rank chunks with a small local BM25-style lexical signal."""

    if limit < 1:
        return []
    query_terms = Counter(_tokenize(query))
    if not query_terms or not chunks:
        return []

    chunk_tokens = [_tokenize(chunk.text) for chunk in chunks]
    doc_freqs = _document_frequencies(chunk_tokens, set(query_terms))
    avg_doc_len = sum(len(tokens) for tokens in chunk_tokens) / len(chunk_tokens)
    scored: list[RetrievedChunk] = []
    for chunk, tokens in zip(chunks, chunk_tokens, strict=True):
        score = _bm25_score(
            query_terms=query_terms,
            doc_terms=Counter(tokens),
            doc_len=len(tokens),
            avg_doc_len=avg_doc_len,
            doc_freqs=doc_freqs,
            corpus_size=len(chunks),
        )
        if score <= 0:
            continue
        scored.append(
            RetrievedChunk(
                id=chunk.id,
                text=chunk.text,
                score=score,
                metadata={**chunk.metadata, "lexical_score": score},
            )
        )
    return sorted(scored, key=lambda chunk: (-chunk.score, chunk.id))[:limit]


def reciprocal_rank_fuse(
    rankings: list[list[RetrievedChunk]],
    *,
    limit: int,
    rank_constant: int = RRF_RANK_CONSTANT,
) -> list[RetrievedChunk]:
    if limit < 1:
        return []

    by_id: dict[str, RetrievedChunk] = {}
    fused_scores: dict[str, float] = {}
    for ranking in rankings:
        seen_in_ranking: set[str] = set()
        for rank, chunk in enumerate(ranking, start=1):
            if chunk.id in seen_in_ranking:
                continue
            seen_in_ranking.add(chunk.id)
            by_id.setdefault(chunk.id, chunk)
            fused_scores[chunk.id] = fused_scores.get(chunk.id, 0.0) + (
                1.0 / (rank_constant + rank)
            )

    ordered_ids = sorted(fused_scores, key=lambda chunk_id: (-fused_scores[chunk_id], chunk_id))
    return [
        RetrievedChunk(
            id=by_id[chunk_id].id,
            text=by_id[chunk_id].text,
            score=fused_scores[chunk_id],
            metadata={**by_id[chunk_id].metadata, "rrf_score": fused_scores[chunk_id]},
        )
        for chunk_id in ordered_ids[:limit]
    ]


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _document_frequencies(
    chunk_tokens: list[list[str]],
    query_terms: set[str],
) -> dict[str, int]:
    frequencies = dict.fromkeys(query_terms, 0)
    for tokens in chunk_tokens:
        unique_tokens = set(tokens)
        for term in query_terms:
            if term in unique_tokens:
                frequencies[term] += 1
    return frequencies


def _bm25_score(
    *,
    query_terms: Counter[str],
    doc_terms: Counter[str],
    doc_len: int,
    avg_doc_len: float,
    doc_freqs: dict[str, int],
    corpus_size: int,
) -> float:
    if doc_len == 0 or avg_doc_len == 0:
        return 0.0
    k1 = 1.2
    b = 0.75
    score = 0.0
    for term, query_count in query_terms.items():
        term_freq = doc_terms.get(term, 0)
        if term_freq == 0:
            continue
        doc_freq = doc_freqs.get(term, 0)
        idf = math.log(1.0 + ((corpus_size - doc_freq + 0.5) / (doc_freq + 0.5)))
        denominator = term_freq + k1 * (1 - b + b * (doc_len / avg_doc_len))
        score += query_count * idf * ((term_freq * (k1 + 1)) / denominator)
    return score
