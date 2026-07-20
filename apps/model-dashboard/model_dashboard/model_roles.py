"""Small, conservative model-role classification helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

MODEL_ROLES = ("generator", "embedding", "reranker", "multimodal", "unknown")
NON_GENERATIVE_ROLES = frozenset(("embedding", "reranker"))

_EXPLICIT_ROLE_MAP = {
    "chat": "generator",
    "completion": "generator",
    "embedding": "embedding",
    "embeddings": "embedding",
    "feature-extraction": "embedding",
    "llm": "generator",
    "rerank": "reranker",
    "reranker": "reranker",
    "text-generation": "generator",
    "vision-language": "multimodal",
    "vlm": "multimodal",
}
_RERANKER_RE = re.compile(r"(?:^|[^a-z0-9])(?:rerank|reranker)(?:[^a-z0-9]|$)")
_EMBEDDING_RE = re.compile(
    r"(?:^|[^a-z0-9])(?:"
    r"bge-m3|bge[-_ ]?(?:small|base|large)|e5[-_ ]?(?:small|base|large)|"
    r"gte[-_ ]?(?:small|base|large)|jina[-_ ]?embeddings?|mxbai[-_ ]?embed|"
    r"nomic[-_ ]?embed|snowflake[-_ ]?arctic[-_ ]?embed|text[-_ ]?embedding"
    r")(?:[^a-z0-9]|$)"
)
_MULTIMODAL_RE = re.compile(
    r"(?:^|[^a-z0-9])(?:llava|vision|vision[-_ ]?language|"
    r"qwen\d*(?:\.\d+)?[-_ ]?vl|vlm)(?:[^a-z0-9]|$)"
)


def infer_model_role(*values, explicit=None):
    normalized_explicit = str(explicit or "").strip().lower().replace("_", "-")
    if normalized_explicit in _EXPLICIT_ROLE_MAP:
        return _EXPLICIT_ROLE_MAP[normalized_explicit]

    text = " ".join(str(value or "") for value in values).lower()
    if _RERANKER_RE.search(text):
        return "reranker"
    if _EMBEDDING_RE.search(text):
        return "embedding"
    if _MULTIMODAL_RE.search(text):
        return "multimodal"
    if text.strip():
        return "generator"
    return "unknown"


def model_supports_generation(role):
    return str(role or "unknown").lower() not in NON_GENERATIVE_ROLES


def artifact_model_role(artifact_dir):
    metadata_path = Path(artifact_dir) / "metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "unknown"
    if not isinstance(metadata, dict):
        return "unknown"
    model = metadata.get("model") if isinstance(metadata.get("model"), dict) else {}
    run = metadata.get("run") if isinstance(metadata.get("run"), dict) else {}
    explicit = model.get("model_role") or model.get("model_type") or metadata.get("model_role")
    return infer_model_role(
        model.get("model_name"),
        model.get("model_family"),
        model.get("provider"),
        model.get("source_url"),
        model.get("notes"),
        run.get("backend"),
        run.get("format"),
        run.get("run_notes"),
        explicit=explicit,
    )


__all__ = (
    "MODEL_ROLES",
    "NON_GENERATIVE_ROLES",
    "artifact_model_role",
    "infer_model_role",
    "model_supports_generation",
)
