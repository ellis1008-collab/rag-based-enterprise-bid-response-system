from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SourceChunkItem(BaseModel):
    chunk_id: int
    content: str
    score: float


class BidResponseItem(BaseModel):
    requirement_id: int
    match_status: Literal["satisfied", "partial", "unsupported"]
    response_text: str = Field(min_length=1)
    risk_level: Literal["low", "medium", "high"]
    source_chunks: list[SourceChunkItem] = Field(default_factory=list)


class BidResponseGenerationResult(BaseModel):
    responses: list[BidResponseItem] = Field(default_factory=list)


class BidResponseRead(BaseModel):
    id: int
    project_id: int
    requirement_id: int
    match_status: str
    response_text: str
    risk_level: str
    source_chunks: list[SourceChunkItem]
    human_status: str
    human_note: str
    created_at: datetime
    updated_at: datetime


class BidResponseUpdate(BaseModel):
    match_status: Literal["satisfied", "partial", "unsupported"] | None = None
    response_text: str | None = Field(default=None, min_length=1)
    risk_level: Literal["low", "medium", "high"] | None = None
    human_status: Literal["pending", "confirmed", "rejected"] | None = None
    human_note: str | None = None


class RiskReportItem(BaseModel):
    requirement_id: int
    requirement_code: str
    category: str
    requirement_content: str
    match_status: str
    risk_level: str
    response_text: str
    source_chunks: list[SourceChunkItem]
    human_status: str
    human_note: str


class RiskReport(BaseModel):
    total_requirements: int
    satisfied_count: int
    partial_count: int
    unsupported_count: int
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    pending_review_count: int
    confirmed_count: int
    rejected_count: int
    risk_items: list[RiskReportItem]
    pending_confirmation_items: list[RiskReportItem]
