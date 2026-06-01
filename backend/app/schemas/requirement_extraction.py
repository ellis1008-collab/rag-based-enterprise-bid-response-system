from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RequirementItem(BaseModel):
    requirement_code: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    priority: Literal["high", "medium", "low"]
    source_page: int | None = None


class RequirementExtractionResult(BaseModel):
    requirements: list[RequirementItem] = Field(min_length=1)


class RfpRequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    requirement_code: str
    category: str
    content: str
    priority: str
    source_page: int | None
    created_at: datetime
