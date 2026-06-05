import re
import uuid
from dataclasses import dataclass
from typing import Any

from local_ai_lab.ingestion.documents import SourceDocument


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    text: str
    metadata: dict[str, Any]


def chunk_documents(
    documents: list[SourceDocument],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        for index, text in enumerate(_chunk_text(document.text, chunk_size, chunk_overlap)):
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document.id}:{index}:{text}"))
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    text=text,
                    metadata={
                        **document.metadata,
                        "chunk_id": chunk_id,
                        "chunk_index": index,
                    },
                )
            )
    return chunks


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    normalized = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not normalized:
        return []

    paragraphs = [paragraph.strip() for paragraph in normalized.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        parts = _split_long_paragraph(paragraph, chunk_size)
        for part in parts:
            candidate = f"{current}\n\n{part}".strip() if current else part
            if len(candidate) <= chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(current)
            current = _prefix_with_overlap(chunks[-1], chunk_overlap, part) if chunks else part

    if current:
        chunks.append(current)

    return chunks


def _split_long_paragraph(paragraph: str, chunk_size: int) -> list[str]:
    if len(paragraph) <= chunk_size:
        return [paragraph]

    words = paragraph.split()
    parts: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            parts.append(current)
        current = word
    if current:
        parts.append(current)
    return parts


def _prefix_with_overlap(previous: str, chunk_overlap: int, text: str) -> str:
    if chunk_overlap <= 0:
        return text
    overlap_start = max(len(previous) - chunk_overlap, 0)
    overlap = previous[overlap_start:].strip()
    if _starts_inside_word(previous, overlap_start, overlap):
        overlap_parts = overlap.split(maxsplit=1)
        overlap = overlap_parts[1] if len(overlap_parts) > 1 else ""
    return f"{overlap}\n\n{text}".strip() if overlap else text


def _starts_inside_word(previous: str, overlap_start: int, overlap: str) -> bool:
    return (
        overlap_start > 0
        and bool(overlap)
        and previous[overlap_start - 1].isalnum()
        and overlap[0].isalnum()
    )
