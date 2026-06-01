from pathlib import Path
from typing import Any

from app.models import KnowledgeChunk


class ChromaKnowledgeStore:
    def __init__(self, persist_dir: str, collection_name: str = "knowledge_chunks") -> None:
        import chromadb

        self.persist_dir = str(Path(persist_dir))
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunks: list[KnowledgeChunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("Chunk count and embedding count must match.")

        self.collection.upsert(
            ids=[_chunk_external_id(chunk.id) for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=embeddings,
            metadatas=[_chunk_metadata(chunk) for chunk in chunks],
        )

    def query(self, query_embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        item_count = self.collection.count()
        if item_count <= 0:
            return []

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, item_count),
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        records: list[dict[str, Any]] = []
        for index, external_id in enumerate(ids):
            metadata = metadatas[index] or {}
            records.append(
                {
                    "id": external_id,
                    "content": documents[index] or "",
                    "metadata": metadata,
                    "distance": distances[index],
                }
            )
        return records


def _chunk_external_id(chunk_id: int) -> str:
    return f"knowledge-chunk-{chunk_id}"


def _chunk_metadata(chunk: KnowledgeChunk) -> dict[str, str | int | float | bool]:
    metadata = _sanitize_metadata(chunk.metadata_json or {})
    metadata["chunk_id"] = chunk.id
    metadata["file_id"] = chunk.file_id
    metadata["chunk_index"] = chunk.chunk_index
    return metadata


def _sanitize_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    sanitized: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if isinstance(value, str | int | float | bool):
            sanitized[key] = value
        elif value is not None:
            sanitized[key] = str(value)
    return sanitized
