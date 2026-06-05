from local_ai_lab.ingestion.documents import load_documents


def test_load_documents_reads_markdown_and_text(tmp_path) -> None:
    markdown = tmp_path / "a.md"
    text = tmp_path / "b.txt"
    ignored = tmp_path / "c.pdf"
    markdown.write_text("# Hello", encoding="utf-8")
    text.write_text("World", encoding="utf-8")
    ignored.write_text("nope", encoding="utf-8")

    documents = load_documents(tmp_path)

    assert [document.path.name for document in documents] == ["a.md", "b.txt"]
    assert all(document.metadata["source_hash"] for document in documents)
