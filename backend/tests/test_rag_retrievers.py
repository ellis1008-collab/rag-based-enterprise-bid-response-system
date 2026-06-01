from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.session import get_db
from app.main import app
from app.models import KnowledgeChunk, KnowledgeFile
from app.rag import (
    ChromaKnowledgeStore,
    ChromaVectorRetriever,
    MockEmbeddingProvider,
    SimpleKeywordRetriever,
    SimpleKnowledgeStore,
)


def test_simple_keyword_retriever_still_works(db_session: Session) -> None:
    knowledge_file = KnowledgeFile(
        filename="product_docs.txt",
        content_text="系统支持私有化部署。",
        status="uploaded",
    )
    db_session.add(knowledge_file)
    db_session.flush()
    db_session.add(
        KnowledgeChunk(
            file_id=knowledge_file.id,
            chunk_index=0,
            content="系统支持 Docker Compose 和 Kubernetes 私有化部署。",
            metadata_json={"filename": "product_docs.txt"},
        )
    )
    db_session.commit()

    retriever = SimpleKeywordRetriever(SimpleKnowledgeStore(db_session))
    results = retriever.retrieve("私有化部署", top_k=1)

    assert len(results) == 1
    assert results[0].retriever_type == "simple"
    assert "私有化部署" in results[0].content


def test_chroma_vector_retriever_can_initialize(tmp_path: Path) -> None:
    retriever = ChromaVectorRetriever(
        store=ChromaKnowledgeStore(persist_dir=str(tmp_path / "chroma")),
        embedding_provider=MockEmbeddingProvider(),
    )

    assert retriever.retriever_type == "chroma"


def test_chroma_upload_indexes_and_retrieves_sample_product_docs(chroma_client: TestClient) -> None:
    file_id = upload_sample_product_docs(chroma_client)
    chunks_response = chroma_client.get(f"/api/knowledge/files/{file_id}/chunks")

    assert chunks_response.status_code == 200
    assert len(chunks_response.json()) > 1

    cases = {
        "私有化部署": "私有化部署",
        "操作日志": "操作日志审计",
        "500 并发": "500 名并发用户",
    }
    for query, expected_text in cases.items():
        response = chroma_client.post("/api/knowledge/retrieve", json={"query": query, "top_k": 3})
        assert response.status_code == 200
        results = response.json()
        assert results, query
        assert all(item["retriever_type"] == "chroma" for item in results)
        assert any(expected_text in item["content"] for item in results), query


@pytest.fixture
def chroma_client(monkeypatch: pytest.MonkeyPatch, test_engine, tmp_path: Path) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("RAG_RETRIEVER_TYPE", "chroma")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "mock")
    get_settings.cache_clear()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def upload_sample_product_docs(client: TestClient) -> int:
    sample_path = Path(__file__).resolve().parents[2] / "sample-data" / "product_docs.txt"
    content = sample_path.read_text(encoding="utf-8")
    response = client.post(
        "/api/knowledge/upload",
        files={"file": ("product_docs.txt", content.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]
