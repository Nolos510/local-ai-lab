import sys

from local_ai_lab.cli.app import main
from local_ai_lab.embeddings.base import EmbeddingProviderConnectionError
from local_ai_lab.llms.base import ChatProviderConnectionError
from local_ai_lab.rag.service import AskResult, Citation, RetrievalInspection
from local_ai_lab.vectorstores.base import VectorStoreConfigurationError


class FailingRAGService:
    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        inspect_retrieval: bool = False,
    ) -> None:
        del question, top_k, inspect_retrieval
        raise ChatProviderConnectionError("safe provider failure")


class FailingEmbeddingRAGService:
    def ingest_path(self, path) -> None:
        del path
        raise EmbeddingProviderConnectionError("safe embedding failure")

    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        inspect_retrieval: bool = False,
    ) -> None:
        del question, top_k, inspect_retrieval
        raise EmbeddingProviderConnectionError("safe embedding failure")


class SuccessfulRAGService:
    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        inspect_retrieval: bool = False,
    ) -> AskResult:
        del question, top_k
        return AskResult(
            answer="Local answer.",
            citations=[Citation(source_name="README.md", chunk_index=0)],
            retrieval_inspection=[
                RetrievalInspection(
                    chunk_id="chunk-1",
                    source_name="README.md",
                    chunk_index=0,
                    score=0.9,
                    text="PRIVATE_CHUNK_TEXT",
                )
            ]
            if inspect_retrieval
            else None,
        )


class FailingVectorStoreRAGService:
    def ingest_path(self, path) -> None:
        del path
        raise VectorStoreConfigurationError("safe vector dimension failure")

    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        inspect_retrieval: bool = False,
    ) -> None:
        del question, top_k, inspect_retrieval
        raise VectorStoreConfigurationError("safe vector dimension failure")


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


def test_cli_ingest_catches_vector_store_error_without_traceback(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["local-ai-lab", "ingest", "--path", "data/sample_docs/private.md"],
    )
    monkeypatch.setattr(
        "local_ai_lab.cli.app.build_rag_service",
        lambda: FailingVectorStoreRAGService(),
    )

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Vector store error: safe vector dimension failure" in captured.err
    assert "private.md" not in captured.err
    assert "Traceback" not in captured.err


def test_cli_ask_json_hides_retrieval_inspection_by_default(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["local-ai-lab", "ask", "PRIVATE_PROMPT_TEXT", "--json"])
    monkeypatch.setattr(
        "local_ai_lab.cli.app.build_rag_service",
        lambda: SuccessfulRAGService(),
    )

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"citations"' in captured.out
    assert '"source_name": "README.md"' in captured.out
    assert "retrieval_inspection" not in captured.out
    assert "PRIVATE_CHUNK_TEXT" not in captured.out
    assert "chunk-1" not in captured.out
    assert "score" not in captured.out


def test_cli_ask_json_inspection_flag_includes_chunk_text_and_score(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["local-ai-lab", "ask", "PRIVATE_PROMPT_TEXT", "--json", "--inspect-retrieval"],
    )
    monkeypatch.setattr(
        "local_ai_lab.cli.app.build_rag_service",
        lambda: SuccessfulRAGService(),
    )

    exit_code = main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "retrieval_inspection" in captured.out
    assert "PRIVATE_CHUNK_TEXT" in captured.out
    assert '"score": 0.9' in captured.out
    assert "chunk-1" in captured.out
