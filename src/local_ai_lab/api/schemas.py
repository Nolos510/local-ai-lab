from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class CitationResponse(BaseModel):
    chunk_id: str
    source_name: str
    chunk_index: int | str
    score: float


class AskResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
