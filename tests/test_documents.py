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


def test_load_documents_ignores_directory_symlink_outside_root(tmp_path) -> None:
    outside = tmp_path.parent / "outside-secret.txt"
    outside.write_text("PRIVATE-SYMLINK-PROOF", encoding="utf-8")
    linked = tmp_path / "linked.txt"
    linked.symlink_to(outside)
    inside = tmp_path / "inside.txt"
    inside.write_text("inside", encoding="utf-8")

    documents = load_documents(tmp_path)

    assert [document.path.name for document in documents] == ["inside.txt"]
