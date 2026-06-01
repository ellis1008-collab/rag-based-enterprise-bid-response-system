from datetime import datetime

from pydantic import BaseModel, Field


class ModelConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(default="openai-compatible", min_length=1, max_length=100)
    base_url: str | None = Field(default=None, max_length=500)
    api_key: str | None = None
    model_name: str = Field(min_length=1, max_length=255)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1)
    is_default: bool = False
    enabled: bool = True


class ModelConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider: str | None = Field(default=None, min_length=1, max_length=100)
    base_url: str | None = Field(default=None, max_length=500)
    api_key: str | None = None
    model_name: str | None = Field(default=None, min_length=1, max_length=255)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    is_default: bool | None = None
    enabled: bool | None = None


class ModelConfigRead(BaseModel):
    id: int
    name: str
    provider: str
    base_url: str | None
    masked_api_key: str | None
    model_name: str
    temperature: float
    max_tokens: int
    is_default: bool
    enabled: bool
    created_at: datetime
    updated_at: datetime


class ModelConfigTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: int
