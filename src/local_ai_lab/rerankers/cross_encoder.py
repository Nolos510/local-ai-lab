from __future__ import annotations

from pathlib import Path

from local_ai_lab.vectorstores.base import RetrievedChunk


class CrossEncoderReranker:
    """Optional local cross-encoder reranker.

    The model path must point at an already-local artifact. This backend lazy
    imports sentence-transformers so the default install path stays lightweight.
    """

    def __init__(self, *, model_path: str) -> None:
        path = Path(model_path).expanduser()
        if not model_path or not path.exists():
            msg = (
                "cross_encoder reranker requires LOCAL_AI_LAB_RERANKER_MODEL_PATH "
                "pointing to an existing local model directory or file"
            )
            raise ValueError(msg)
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            msg = "cross_encoder reranker requires installing the optional [rerank] extra"
            raise ValueError(msg) from exc
        self.model_path = str(path)
        self._model = CrossEncoder(
            self.model_path,
            automodel_args={"local_files_only": True},
            tokenizer_args={"local_files_only": True},
        )

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not chunks:
            return []
        pairs = [(query, chunk.text) for chunk in chunks]
        scores = self._model.predict(pairs)
        scored = [
            RetrievedChunk(
                id=chunk.id,
                text=chunk.text,
                score=float(score),
                metadata={**chunk.metadata, "cross_encoder_score": float(score)},
            )
            for chunk, score in zip(chunks, scores, strict=True)
        ]
        return sorted(scored, key=lambda chunk: (-chunk.score, chunk.id))
