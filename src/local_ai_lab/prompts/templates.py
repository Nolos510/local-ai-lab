from local_ai_lab.vectorstores.base import RetrievedChunk

SYSTEM_PROMPT = """You are a local, privacy-first AI assistant.
Answer only from the supplied context when context is provided.
If the context is insufficient, say what is missing.
Use concise citations like [source_name#chunk_index]."""


def build_rag_prompt(question: str, contexts: list[RetrievedChunk]) -> str:
    context_text = "\n\n".join(
        _format_context(index, chunk) for index, chunk in enumerate(contexts, 1)
    )
    return f"""Question:
{question}

Retrieved context:
{context_text or "No context retrieved."}

Instructions:
- Answer the question using the retrieved context.
- Include citations for factual claims.
- If the retrieved context is not enough, say so clearly.
"""


def _format_context(index: int, chunk: RetrievedChunk) -> str:
    source_name = chunk.metadata.get("source_name", chunk.metadata.get("source_path", "unknown"))
    chunk_index = chunk.metadata.get("chunk_index", "?")
    return (
        f"[{index}] {source_name}#chunk_{chunk_index} "
        f"(score={chunk.score:.4f}, id={chunk.id})\n{chunk.text}"
    )
