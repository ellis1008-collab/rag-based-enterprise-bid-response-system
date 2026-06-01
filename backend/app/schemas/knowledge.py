from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class KnowledgeFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_text: str
    status: str
    created_at: datetime


class KnowledgeChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_id: int
    chunk_index: int
    content: str
    metadata_json: dict[str, Any]
    created_at: datetime
