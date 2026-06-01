import re
from abc import ABC, abstractmethod

from app.rag.schemas import RetrievedChunk
from app.rag.simple_store import SimpleKnowledgeStore


class Retriever(ABC):
    retriever_type: str

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        pass


class SimpleKeywordRetriever(Retriever):
    retriever_type = "simple"

    def __init__(self, store: SimpleKnowledgeStore) -> None:
        self.store = store

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        terms = self._query_terms(query)
        if not terms:
            return []

        scored_chunks: list[RetrievedChunk] = []
        for chunk in self.store.list_chunks():
            score = self._score(query, terms, chunk.content)
            if score <= 0:
                continue

            scored_chunks.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    file_id=chunk.file_id,
                    content=chunk.content,
                    score=round(score, 4),
                    metadata=chunk.metadata_json,
                    retriever_type=self.retriever_type,
                )
            )

        scored_chunks.sort(key=lambda item: (-item.score, item.chunk_id))
        return scored_chunks[:top_k]

    def _query_terms(self, query: str) -> list[str]:
        raw_terms = re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+", query.lower())
        terms: list[str] = []
        for term in raw_terms:
            terms.append(term)
            if self._is_cjk(term) and len(term) > 2:
                terms.extend(term[index : index + 2] for index in range(0, len(term) - 1))
        return list(dict.fromkeys(terms))

    def _score(self, query: str, terms: list[str], content: str) -> float:
        normalized_query = self._normalize(query)
        normalized_content = self._normalize(content)
        content_lower = content.lower()

        score = 0.0
        exact_matches = 0
        for term in terms:
            if term in content_lower:
                exact_matches += 1
                score += 2.0 + min(len(term), 12) / 10

        if normalized_query and normalized_query in normalized_content:
            score += 4.0

        if exact_matches == len(terms):
            score += 1.5

        return score

    def _normalize(self, text: str) -> str:
        return "".join(re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+", text.lower()))

    def _is_cjk(self, text: str) -> bool:
        return all("\u4e00" <= char <= "\u9fff" for char in text)
