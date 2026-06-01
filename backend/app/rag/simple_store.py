from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeChunk


class SimpleKnowledgeStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_chunks(self) -> list[KnowledgeChunk]:
        return list(self.db.scalars(select(KnowledgeChunk).order_by(KnowledgeChunk.id.asc())))
