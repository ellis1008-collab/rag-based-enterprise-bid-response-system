from app.models import KnowledgeChunk
from app.rag.chroma_store import ChromaKnowledgeStore
from app.rag.embeddings import BaseEmbeddingProvider
from app.rag.retriever import Retriever
from app.rag.schemas import RetrievedChunk


class ChromaVectorRetriever(Retriever):
    retriever_type = "chroma"

    def __init__(
        self,
        store: ChromaKnowledgeStore,
        embedding_provider: BaseEmbeddingProvider,
    ) -> None:
        self.store = store
        self.embedding_provider = embedding_provider

    def add_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        embeddings = self.embedding_provider.embed_documents([chunk.content for chunk in chunks])
        self.store.upsert_chunks(chunks=chunks, embeddings=embeddings)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        query_embedding = self.embedding_provider.embed_query(query)
        records = self.store.query(query_embedding=query_embedding, top_k=top_k)
        chunks: list[RetrievedChunk] = []
        for record in records:
            metadata = record["metadata"]
            chunks.append(
                RetrievedChunk(
                    chunk_id=int(metadata["chunk_id"]),
                    file_id=int(metadata["file_id"]),
                    content=record["content"],
                    score=_distance_to_score(float(record["distance"])),
                    metadata=metadata,
                    retriever_type=self.retriever_type,
                )
            )
        return chunks


def _distance_to_score(distance: float) -> float:
    return round(max(0.0, 1.0 - distance), 4)
