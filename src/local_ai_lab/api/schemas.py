from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1)


class CitationResponse(BaseModel):
    chunk_id: str
    source_path: str
    source_name: str
    chunk_index: int | str
    score: float
    preview: str


class AskResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    retrieved_chunks: list[dict[str, Any]]
