from fastapi.testclient import TestClient

from local_ai_lab.api.app import create_app
from local_ai_lab.llms.base import ChatProviderResponseError
from local_ai_lab.rag.service import AskResult, Citation


class FakeRAGService:
    def ask(self, question: str, *, top_k: int | None = None) -> AskResult:
        assert question == "What is this lab for?"
        assert top_k == 1
        return AskResult(
            answer="It is for local AI engineering.",
            citations=[
                Citation(
                    chunk_id="chunk-1",
                    source_name="README.md",
                    chunk_index=0,
                    score=0.9,
                )
            ],
        )


class FailingRAGService:
    def ask(self, question: str, *, top_k: int | None = None) -> None:
        del question, top_k
        raise ChatProviderResponseError(
            "LM Studio/OpenAI-compatible provider failed: HTTP 500. "
            "Endpoint: http://localhost:1234. "
            "Configured model: local-model. "
            "Run `uv run local-ai-lab doctor`."
        )


def test_ask_endpoint_returns_answer(monkeypatch) -> None:
    monkeypatch.setattr("local_ai_lab.api.app.build_rag_service", lambda settings: FakeRAGService())
    client = TestClient(create_app())

    response = client.post("/ask", json={"question": "What is this lab for?", "top_k": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "It is for local AI engineering."
    assert payload["citations"][0]["source_name"] == "README.md"
    assert "retrieved_chunks" not in payload
    assert "source_path" not in payload["citations"][0]
    assert "preview" not in payload["citations"][0]


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
