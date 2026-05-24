from fastapi.testclient import TestClient

from local_ai_lab.api.app import create_app
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
                    source_path="data/sample_docs/README.md",
                    source_name="README.md",
                    chunk_index=0,
                    score=0.9,
                    preview="Local AI engineering.",
                )
            ],
            retrieved_chunks=[],
        )


def test_ask_endpoint_returns_answer(monkeypatch) -> None:
    monkeypatch.setattr("local_ai_lab.api.app.build_rag_service", lambda settings: FakeRAGService())
    client = TestClient(create_app())

    response = client.post("/ask", json={"question": "What is this lab for?", "top_k": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "It is for local AI engineering."
    assert payload["citations"][0]["source_name"] == "README.md"
