from typing import Any

from pydantic import BaseModel

from app.schemas.bid_response import BidResponseGenerationResult, BidResponseItem
from app.schemas.requirement_extraction import RequirementExtractionResult, RequirementItem


class ProviderTextResponse(BaseModel):
    content: str
    raw_response: dict[str, Any] | None = None


class LLMTextResult(BaseModel):
    content: str
    provider: str
    model_name: str
    latency_ms: int


ExtractedRequirement = RequirementItem
ResponseGenerationResult = BidResponseGenerationResult
