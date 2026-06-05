from local_ai_lab.prompts.templates import build_rag_prompt
from local_ai_lab.vectorstores.base import RetrievedChunk


def test_build_rag_prompt_includes_question_and_context() -> None:
    prompt = build_rag_prompt(
        "What is the lab for?",
        [
            RetrievedChunk(
                id="chunk-1",
                text="The lab is for local AI engineering.",
                score=0.91,
                metadata={"source_name": "README.md", "chunk_index": 0},
            )
        ],
    )

    assert "What is the lab for?" in prompt
    assert "The lab is for local AI engineering." in prompt
    assert "README.md#chunk_0" in prompt
