import logging

from sqlalchemy.orm import Session

from app.models import KnowledgeChunk
from app.rag import RetrievedChunk, create_retriever, create_simple_retriever, index_chunks_if_configured

logger = logging.getLogger(__name__)


def retrieve_knowledge(db: Session, query: str, top_k: int = 5) -> list[RetrievedChunk]:
    retriever = create_retriever(db)
    try:
        return retriever.retrieve(query=query, top_k=top_k)
    except Exception:
        logger.warning(
            "%s retriever failed during retrieval; falling back to simple retriever.",
            retriever.retriever_type,
            exc_info=True,
        )
        return create_simple_retriever(db).retrieve(query=query, top_k=top_k)


def index_knowledge_chunks(chunks: list[KnowledgeChunk]) -> None:
    try:
        index_chunks_if_configured(chunks)
    except Exception:
        logger.warning("Chroma chunk indexing failed; database upload remains saved.", exc_info=True)
