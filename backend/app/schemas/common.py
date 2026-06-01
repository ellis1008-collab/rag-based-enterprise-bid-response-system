from pydantic import BaseModel


class DeleteResponse(BaseModel):
    status: str
