from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RfpProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    customer_name: str = Field(min_length=1, max_length=255)
    status: str = Field(default="draft", min_length=1, max_length=50)


class RfpProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    customer_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class RfpDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    filename: str
    content_text: str
    created_at: datetime
