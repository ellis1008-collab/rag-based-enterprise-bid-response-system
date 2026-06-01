from typing import Any

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class RetrievedChunk(BaseModel):
    chunk_id: int
    file_id: int
    content: str
    score: float
    metadata: dict[str, Any]
    retriever_type: str
