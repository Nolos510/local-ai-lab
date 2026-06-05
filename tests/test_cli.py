import sys

from local_ai_lab.cli.app import main
from local_ai_lab.embeddings.base import EmbeddingProviderConnectionError
from local_ai_lab.llms.base import ChatProviderConnectionError


class FailingRAGService:
    def ask(self, question: str, *, top_k: int | None = None) -> None:
        del question, top_k
        raise ChatProviderConnectionError("safe provider failure")


class FailingEmbeddingRAGService:
    def ingest_path(self, path) -> None:
        del path
        raise EmbeddingProviderConnectionError("safe embedding failure")

    def ask(self, question: str, *, top_k: int | None = None) -> None:
        del question, top_k
        raise EmbeddingProviderConnectionError("safe embedding failure")


def test_cli_ask_catches_provider_error_without_traceback(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["local-ai-lab", "ask", "PRIVATE_PROMPT_TEXT"])
    monkeypatch.setattr(
        "local_ai_lab.cli.app.build_rag_service",
        lambda: FailingRAGService(),
    )

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Provider error: safe provider failure" in captured.err
    assert "PRIVATE_PROMPT_TEXT" not in captured.err
    assert "Traceback" not in captured.err


def test_cli_ask_catches_embedding_error_without_traceback(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["local-ai-lab", "ask", "PRIVATE_PROMPT_TEXT"])
    monkeypatch.setattr(
        "local_ai_lab.cli.app.build_rag_service",
        lambda: FailingEmbeddingRAGService(),
    )

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Embedding provider error: safe embedding failure" in captured.err
    assert "PRIVATE_PROMPT_TEXT" not in captured.err
    assert "Traceback" not in captured.err


def test_cli_ingest_catches_embedding_error_without_traceback(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["local-ai-lab", "ingest", "--path", "data/sample_docs/private.md"],
    )
    monkeypatch.setattr(
        "local_ai_lab.cli.app.build_rag_service",
        lambda: FailingEmbeddingRAGService(),
    )

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Embedding provider error: safe embedding failure" in captured.err
    assert "private.md" not in captured.err
    assert "Traceback" not in captured.err
