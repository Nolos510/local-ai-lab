from fastapi.testclient import TestClient

from local_ai_lab.api.app import create_app
from local_ai_lab.llms.base import ChatProviderResponseError
from local_ai_lab.rag.service import AskResult, Citation, RetrievalInspection
from local_ai_lab.vectorstores.base import VectorStoreConfigurationError


class FakeRAGService:
    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        inspect_retrieval: bool = False,
    ) -> AskResult:
        assert question == "What is this lab for?"
        assert top_k == 1
        return AskResult(
            answer="It is for local AI engineering.",
            citations=[
                Citation(
                    source_name="README.md",
                    chunk_index=0,
                )
            ],
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


class FailingRAGService:
    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        inspect_retrieval: bool = False,
    ) -> None:
        del question, top_k, inspect_retrieval
        raise ChatProviderResponseError(
            "LM Studio/OpenAI-compatible provider failed: HTTP 500. "
            "Endpoint: http://localhost:1234. "
            "Configured model: local-model. "
            "Run `uv run local-ai-lab doctor`."
        )


class FailingVectorStoreRAGService:
    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        inspect_retrieval: bool = False,
    ) -> None:
        del question, top_k, inspect_retrieval
        raise VectorStoreConfigurationError(
            "PRIVATE_COLLECTION uses 384; token=PRIVATE_TOKEN"
        )


def test_ask_endpoint_returns_answer(monkeypatch) -> None:
    monkeypatch.setattr("local_ai_lab.api.app.build_rag_service", lambda settings: FakeRAGService())
    client = TestClient(create_app())

    response = client.post("/ask", json={"question": "What is this lab for?", "top_k": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "It is for local AI engineering."
    assert payload["citations"] == [{"source_name": "README.md", "chunk_index": 0}]
    assert "retrieval_inspection" not in payload
    assert "retrieved_chunks" not in payload
    assert "source_path" not in payload["citations"][0]
    assert "preview" not in payload["citations"][0]
    assert "chunk_id" not in payload["citations"][0]
    assert "score" not in payload["citations"][0]
    assert "PRIVATE_CHUNK_TEXT" not in response.text


def test_ask_endpoint_returns_retrieval_inspection_only_when_requested(monkeypatch) -> None:
    monkeypatch.setattr("local_ai_lab.api.app.build_rag_service", lambda settings: FakeRAGService())
    client = TestClient(create_app())

    response = client.post(
        "/ask",
        json={"question": "What is this lab for?", "top_k": 1, "inspect_retrieval": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["citations"] == [{"source_name": "README.md", "chunk_index": 0}]
    assert payload["retrieval_inspection"] == [
        {
            "chunk_id": "chunk-1",
            "source_name": "README.md",
            "chunk_index": 0,
            "score": 0.9,
            "text": "PRIVATE_CHUNK_TEXT",
        }
    ]


def test_ask_endpoint_rejects_large_top_k(monkeypatch) -> None:
    monkeypatch.setattr("local_ai_lab.api.app.build_rag_service", lambda settings: FakeRAGService())
    client = TestClient(create_app())

    response = client.post("/ask", json={"question": "What is this lab for?", "top_k": 21})

    assert response.status_code == 422


def test_ask_endpoint_returns_502_for_provider_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "local_ai_lab.api.app.build_rag_service",
        lambda settings: FailingRAGService(),
    )
    client = TestClient(create_app())

    response = client.post("/ask", json={"question": "PRIVATE_PROMPT_TEXT", "top_k": 1})

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "Local chat provider failed" in detail
    assert "http://localhost:1234" not in detail
    assert "local-model" not in detail
    assert "uv run local-ai-lab doctor" in detail
    assert "PRIVATE_PROMPT_TEXT" not in detail
    assert "secret" not in detail
    assert "token=abc" not in detail


def test_ask_endpoint_returns_sanitized_503_for_vector_store_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "local_ai_lab.api.app.build_rag_service",
        lambda settings: FailingVectorStoreRAGService(),
    )
    client = TestClient(create_app())

    response = client.post("/ask", json={"question": "PRIVATE_PROMPT_TEXT", "top_k": 1})

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "Local vector store configuration failed" in detail
    assert "uv run local-ai-lab doctor" in detail
    assert "PRIVATE_COLLECTION" not in detail
    assert "PRIVATE_TOKEN" not in detail
    assert "PRIVATE_PROMPT_TEXT" not in detail
