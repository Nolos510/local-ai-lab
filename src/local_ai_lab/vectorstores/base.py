from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    text: str
    score: float
    metadata: dict[str, Any]
