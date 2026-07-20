"""Read-only retrieval evaluation lane for committed local evidence."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from ..components import _command_block, _number, _pill, _table, _text
from ..layout import _layout

RETRIEVAL_CORPORA_DIR = (
    Path(__file__).resolve().parents[4] / "evals" / "rag-retrieval" / "corpora"
)


@dataclass(frozen=True)
class RetrievalConfiguration:
    corpus: str
    embedding_model: str
    embedding_slug: str
    retrieval_mode: str
    reranker: str
    metrics_filename: str
    results_filename: str
    collection_name: str
    k: int = 5
    include_vector_size: bool = True
    collect_runner: str = "uv run python"


def _configuration(corpus, retrieval_mode, reranker, *, legacy=False):
    embedding_slug = "bge-m3"
    suffix = (
        embedding_slug
        if legacy
        else f"{embedding_slug}-{retrieval_mode}-{reranker}"
    )
    collection_suffix = f"{embedding_slug}_{retrieval_mode}_{reranker}".replace("-", "_")
    corpus_slug = re.sub(r"[^a-zA-Z0-9]+", "_", corpus).strip("_")
    return RetrievalConfiguration(
        corpus=corpus,
        embedding_model="bge-m3:latest",
        embedding_slug=embedding_slug,
        retrieval_mode=retrieval_mode,
        reranker=reranker,
        metrics_filename=f"{suffix}-metrics.json",
        results_filename=f"{suffix}-results.jsonl",
        collection_name=f"{corpus_slug}_{collection_suffix}",
        include_vector_size=not legacy,
        collect_runner="python3" if legacy else "uv run python",
    )


EXPECTED_CONFIGURATIONS = {
    "repo-docs-v0.1": (
        _configuration("repo-docs-v0.1", "dense", "identity", legacy=True),
    ),
    "repo-docs-v0.2": tuple(
        _configuration("repo-docs-v0.2", retrieval_mode, reranker)
        for retrieval_mode in ("dense", "hybrid")
        for reranker in ("identity", "cross-encoder")
    ),
}

_EXPLICIT_METRICS_RE = re.compile(
    r"^(?P<embedding>.+)-(?P<mode>dense|hybrid)-"
    r"(?P<reranker>identity|cross-encoder)-metrics\.json$"
)
_LEGACY_METRICS_RE = re.compile(r"^(?P<embedding>.+)-metrics\.json$")


def load_retrieval_metrics(path):
    """Load and validate one aggregate retrieval metrics file without side effects."""

    metrics_path = Path(path)
    if not metrics_path.is_file():
        return {"status": "not_scored"}
    try:
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("metrics root must be an object")
        query_count = payload.get("query_count")
        k = payload.get("k")
        recall_at_k = payload.get("recall_at_k")
        mrr = payload.get("mrr")
        if isinstance(query_count, bool) or not isinstance(query_count, int) or query_count < 0:
            raise ValueError("query_count must be a non-negative integer")
        if isinstance(k, bool) or not isinstance(k, int) or k < 1:
            raise ValueError("k must be a positive integer")
        for label, value in (("recall_at_k", recall_at_k), ("mrr", mrr)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{label} must be numeric")
            if not math.isfinite(float(value)) or not 0 <= float(value) <= 1:
                raise ValueError(f"{label} must be between zero and one")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError):
        return {"status": "unavailable"}
    return {
        "status": "scored",
        "query_count": query_count,
        "k": k,
        "recall_at_k": float(recall_at_k),
        "mrr": float(mrr),
    }


def _configuration_from_metrics_filename(corpus, filename):
    match = _EXPLICIT_METRICS_RE.fullmatch(filename)
    if match:
        embedding_slug = match.group("embedding")
        retrieval_mode = match.group("mode")
        reranker = match.group("reranker")
        suffix = filename.removesuffix("-metrics.json")
        return RetrievalConfiguration(
            corpus=corpus,
            embedding_model=(
                "bge-m3:latest" if embedding_slug == "bge-m3" else embedding_slug
            ),
            embedding_slug=embedding_slug,
            retrieval_mode=retrieval_mode,
            reranker=reranker,
            metrics_filename=filename,
            results_filename=f"{suffix}-results.jsonl",
            collection_name=f"{corpus}_{suffix}".replace("-", "_"),
        )
    match = _LEGACY_METRICS_RE.fullmatch(filename)
    if not match:
        return None
    embedding_slug = match.group("embedding")
    return RetrievalConfiguration(
        corpus=corpus,
        embedding_model="bge-m3:latest" if embedding_slug == "bge-m3" else embedding_slug,
        embedding_slug=embedding_slug,
        retrieval_mode="dense",
        reranker="identity",
        metrics_filename=filename,
        results_filename=f"{embedding_slug}-results.jsonl",
        collection_name=f"{corpus}_{embedding_slug}".replace("-", "_"),
        include_vector_size=False,
        collect_runner="python3",
    )


def _corpus_configurations(corpus_dir):
    corpus = corpus_dir.name
    configurations = {
        config.metrics_filename: config
        for config in EXPECTED_CONFIGURATIONS.get(corpus, ())
    }
    try:
        metrics_paths = sorted(corpus_dir.glob("*-metrics.json"))
    except OSError:
        metrics_paths = []
    for metrics_path in metrics_paths:
        discovered = _configuration_from_metrics_filename(corpus, metrics_path.name)
        if discovered is not None:
            configurations.setdefault(discovered.metrics_filename, discovered)
    return sorted(
        configurations.values(),
        key=lambda config: (
            config.embedding_model.casefold(),
            0 if config.retrieval_mode == "dense" else 1,
            0 if config.reranker == "identity" else 1,
            config.metrics_filename,
        ),
    )


def _production_command(config):
    base = f"evals/rag-retrieval/corpora/{config.corpus}"
    lines = []
    runner = config.collect_runner
    if config.reranker == "cross-encoder":
        lines.extend(
            (
                "uv sync --extra rerank",
                "export LOCAL_CROSS_ENCODER_PATH=/absolute/path/to/already-local/cross-encoder",
                'test -e "$LOCAL_CROSS_ENCODER_PATH"',
            )
        )
        runner = "uv run --extra rerank python"
    lines.extend(
        (
            "LOCAL_AI_LAB_EMBEDDING_PROVIDER=ollama \\",
            f"LOCAL_AI_LAB_OLLAMA_EMBEDDING_MODEL={config.embedding_model} \\",
        )
    )
    if config.include_vector_size:
        lines.append("LOCAL_AI_LAB_QDRANT_VECTOR_SIZE=1024 \\")
    lines.extend(
        (
            f"LOCAL_AI_LAB_QDRANT_COLLECTION={config.collection_name} \\",
            f"LOCAL_AI_LAB_RERANKER_PROVIDER={config.reranker.replace('-', '_')} \\",
        )
    )
    if config.reranker == "cross-encoder":
        lines.append('LOCAL_AI_LAB_RERANKER_MODEL_PATH="$LOCAL_CROSS_ENCODER_PATH" \\')
    lines.extend(
        (
            f"{runner} evals/rag-retrieval/collect.py \\",
            f"  --labels {base}/labels.json \\",
            f"  --corpus-path {base}/docs \\",
            f"  --out {base}/{config.results_filename} \\",
            f"  --retrieval-mode {config.retrieval_mode} \\",
            f"  --top-k {config.k}",
            "",
            "python3 evals/rag-retrieval/scorer.py \\",
            f"  --labels {base}/labels.json \\",
            f"  --results {base}/{config.results_filename} \\",
            f"  --k {config.k} \\",
            f"  > {base}/{config.metrics_filename}",
        )
    )
    return "\n".join(lines)


def _evidence_cell(config, evidence):
    relative_path = f"evals/rag-retrieval/corpora/{config.corpus}/{config.metrics_filename}"
    if evidence["status"] == "scored":
        return (
            '<div class="cell-stack">'
            f'{_pill("scored")}<code>{_text(relative_path)}</code>'
            "</div>"
        )
    if evidence["status"] == "unavailable":
        status = "metrics unavailable"
        guidance = "Run the exact local command below to replace this invalid file."
    else:
        status = "not scored yet"
        guidance = "Run the exact local command below to produce this evidence."
    status_html = _pill(status)
    guidance_html = _text(guidance)
    command_html = _command_block(_production_command(config))
    return f"""
    <div class="retrieval-empty cell-stack">
      {status_html}
      <span class="empty">{guidance_html}</span>
      <details>
        <summary>Exact local collection and scoring command</summary>
        {command_html}
      </details>
    </div>
    """


def _configuration_row(corpus_dir, config):
    evidence = load_retrieval_metrics(corpus_dir / config.metrics_filename)
    scored = evidence["status"] == "scored"
    return [
        f"<code>{_text(config.corpus)}</code>",
        _text(config.embedding_model),
        _pill(config.retrieval_mode),
        _pill(config.reranker),
        _text(evidence.get("query_count", "—")),
        _number(evidence.get("recall_at_k"), 3, "—") if scored else "—",
        _number(evidence.get("mrr"), 3, "—") if scored else "—",
        _text(evidence.get("k", "—")),
        _evidence_cell(config, evidence),
    ]


def _retrieval(corpora_dir=RETRIEVAL_CORPORA_DIR):
    root = Path(corpora_dir)
    try:
        corpus_dirs = sorted(
            (path for path in root.iterdir() if path.is_dir()),
            key=lambda path: path.name.casefold(),
        )
    except OSError:
        corpus_dirs = []

    sections = []
    for corpus_dir in corpus_dirs:
        configurations = _corpus_configurations(corpus_dir)
        if not configurations:
            continue
        rows = [_configuration_row(corpus_dir, config) for config in configurations]
        note = (
            "One row per embedding, retrieval mode, and reranker configuration. "
            "Compare rows within this corpus; metrics from different corpora are "
            "not interchangeable."
        )
        sections.append(
            """
            <section class="retrieval-corpus-section">
              <div class="section-heading-row">
                <div>
                  <h2>Corpus: <code>{corpus}</code></h2>
                  <p class="section-note">{note}</p>
                </div>
              </div>
              {table}
            </section>
            """.format(
                corpus=_text(corpus_dir.name),
                note=_text(note),
                table=_table(
                    (
                        "Corpus",
                        "Embedding model",
                        "Retrieval mode",
                        "Reranker",
                        "Query count",
                        "Recall@k",
                        "MRR",
                        "k",
                        "Evidence",
                    ),
                    rows,
                    table_class="retrieval-table",
                    empty_message="No retrieval configurations declared for this corpus.",
                    header_tip_keys={
                        "Query count": "retrieval_query_count",
                        "Recall@k": "recall_at_k",
                        "MRR": "mrr",
                        "k": "retrieval_k",
                    },
                ),
            )
        )

    if sections:
        corpus_content = "".join(sections)
    else:
        corpus_content = """
        <section class="panel retrieval-empty-state">
          <h2>No retrieval corpora found</h2>
          <p class="empty">
            No committed corpus directories are available under
            <code>evals/rag-retrieval/corpora</code>. No retrieval score is claimed.
          </p>
        </section>
        """

    body = f"""
    <section class="panel page-intro retrieval-intro">
      <p>
        Retrieval Evaluation is the evidence lane for embedding and reranker models.
      </p>
      <p class="empty">
        This page reads committed aggregate JSON only. It does not call a network,
        Qdrant, Ollama, a model, or a subprocess while rendering. Recall@k and MRR
        are retrieval metrics, never LLM rubric scores. Configuration identity
        comes from the committed corpus matrix and metrics filename; displayed
        metric values come only from the JSON file.
      </p>
      <p>
        <a href="/runs">Back to generative Benchmark</a> ·
        <a href="/inventory">Open model-role inventory</a>
      </p>
    </section>
    {corpus_content}
    """
    return _layout("Retrieval Evaluation", "/retrieval", body)


__all__ = (
    "EXPECTED_CONFIGURATIONS",
    "RETRIEVAL_CORPORA_DIR",
    "RetrievalConfiguration",
    "_retrieval",
    "load_retrieval_metrics",
)
