import logging

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import KnowledgeChunk
from app.rag.chroma_store import ChromaKnowledgeStore
from app.rag.embeddings import (
    BaseEmbeddingProvider,
    MockEmbeddingProvider,
    OpenAICompatibleEmbeddingProvider,
)
from app.rag.retriever import Retriever, SimpleKeywordRetriever
from app.rag.simple_store import SimpleKnowledgeStore
from app.rag.vector_retriever import ChromaVectorRetriever

logger = logging.getLogger(__name__)


def create_retriever(db: Session, settings: Settings | None = None) -> Retriever:
    active_settings = settings or get_settings()
    retriever_type = _normalize(active_settings.rag_retriever_type)
    if retriever_type == "simple":
        return create_simple_retriever(db)

    if retriever_type == "chroma":
        try:
            return create_chroma_retriever(active_settings)
        except Exception:
            logger.warning("Chroma retriever initialization failed; falling back to simple retriever.", exc_info=True)
            return create_simple_retriever(db)

    logger.warning("Unsupported RAG_RETRIEVER_TYPE=%s; falling back to simple retriever.", retriever_type)
    return create_simple_retriever(db)


def create_simple_retriever(db: Session) -> SimpleKeywordRetriever:
    return SimpleKeywordRetriever(SimpleKnowledgeStore(db))


def create_chroma_retriever(settings: Settings | None = None) -> ChromaVectorRetriever:
    active_settings = settings or get_settings()
    embedding_provider = create_embedding_provider(active_settings)
    store = ChromaKnowledgeStore(persist_dir=active_settings.chroma_persist_dir)
    return ChromaVectorRetriever(store=store, embedding_provider=embedding_provider)


def create_embedding_provider(settings: Settings | None = None) -> BaseEmbeddingProvider:
    active_settings = settings or get_settings()
    provider_type = _normalize(active_settings.embedding_provider)
    if provider_type == "mock":
        return MockEmbeddingProvider()

    if provider_type in {"openai-compatible", "openai_compatible"}:
        return OpenAICompatibleEmbeddingProvider(
            base_url=active_settings.embedding_base_url or "",
            api_key=active_settings.embedding_api_key,
            model_name=active_settings.embedding_model_name or "",
        )

    raise ValueError(f"Unsupported EMBEDDING_PROVIDER={provider_type}.")


def index_chunks_if_configured(chunks: list[KnowledgeChunk], settings: Settings | None = None) -> None:
    active_settings = settings or get_settings()
    if _normalize(active_settings.rag_retriever_type) != "chroma":
        return

    retriever = create_chroma_retriever(active_settings)
    retriever.add_chunks(chunks)


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()
