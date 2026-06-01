from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    run_type: str
    status: str
    steps_json: dict[str, Any]
    error_message: str | None
    created_at: datetime
    finished_at: datetime | None
