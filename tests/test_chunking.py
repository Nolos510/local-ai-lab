from pathlib import Path

from local_ai_lab.ingestion.chunking import chunk_documents
from local_ai_lab.ingestion.documents import SourceDocument


def test_chunk_documents_preserves_source_metadata() -> None:
    document = SourceDocument(
        id="doc-1",
        path=Path("sample.md"),
        text="Alpha beta gamma.\n\nDelta epsilon zeta.",
        metadata={"source_path": "sample.md", "source_name": "sample.md", "source_hash": "doc-1"},
    )

    chunks = chunk_documents([document], chunk_size=100, chunk_overlap=10)

    assert len(chunks) == 1
    assert chunks[0].metadata["source_name"] == "sample.md"
    assert chunks[0].metadata["chunk_index"] == 0


def test_chunk_documents_splits_long_text() -> None:
    document = SourceDocument(
        id="doc-1",
        path=Path("sample.md"),
        text=" ".join(["token"] * 80),
        metadata={"source_path": "sample.md", "source_name": "sample.md", "source_hash": "doc-1"},
    )

    chunks = chunk_documents([document], chunk_size=120, chunk_overlap=20)

    assert len(chunks) > 1
    assert all(chunk.text for chunk in chunks)
