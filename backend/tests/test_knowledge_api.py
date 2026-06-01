from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.file_samples import make_docx, make_text_pdf, make_xlsx


def test_upload_knowledge_file_creates_chunks(client: TestClient) -> None:
    content = "product documentation " * 80
    response = client.post(
        "/api/knowledge/upload",
        files={"file": ("product.md", content.encode("utf-8"), "text/markdown")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["filename"] == "product.md"
    assert data["content_text"] == content
    assert data["status"] == "uploaded"

    chunks_response = client.get(f"/api/knowledge/files/{data['id']}/chunks")
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    assert len(chunks) > 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["metadata_json"]["filename"] == "product.md"
    assert chunks[0]["metadata_json"]["splitter"] == "TextSplitter"


@pytest.mark.parametrize(
    ("filename", "raw_content", "expected_text"),
    [
        (
            "product.pdf",
            make_text_pdf("PDF product supports private deployment and operation logs"),
            "PDF product supports private deployment",
        ),
        (
            "product.docx",
            make_docx("DOCX product supports private deployment", [["Audit", "Operation logs"]]),
            "Audit\tOperation logs",
        ),
        (
            "product.xlsx",
            make_xlsx("ProductDocs", [["Topic", "Capability"], ["Capacity", "500 concurrent users"]]),
            "Sheet: ProductDocs",
        ),
    ],
    ids=["pdf", "docx", "xlsx"],
)
def test_upload_knowledge_business_file_formats_create_chunks(
    client: TestClient,
    filename: str,
    raw_content: bytes,
    expected_text: str,
) -> None:
    response = client.post(
        "/api/knowledge/upload",
        files={"file": (filename, raw_content, "application/octet-stream")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == filename
    assert expected_text in data["content_text"]

    chunks_response = client.get(f"/api/knowledge/files/{data['id']}/chunks")
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    assert len(chunks) >= 1
    assert chunks[0]["metadata_json"]["filename"] == filename


def test_retrieve_returns_relevant_chunks_for_sample_product_docs(client: TestClient) -> None:
    file_id = upload_sample_product_docs(client)
    chunks = client.get(f"/api/knowledge/files/{file_id}/chunks").json()
    assert len(chunks) > 1

    cases = {
        "私有化部署": "私有化部署",
        "操作日志": "操作日志审计",
        "500 并发": "500 名并发用户",
        "灾难恢复": "灾难恢复",
    }

    for query, expected_text in cases.items():
        response = client.post("/api/knowledge/retrieve", json={"query": query, "top_k": 3})
        assert response.status_code == 200
        results = response.json()
        assert results, query
        assert expected_text in results[0]["content"]
        assert results[0]["score"] > 0
        assert results[0]["metadata"]["filename"] == "product_docs.txt"
        assert results[0]["retriever_type"] == "simple"


def test_retrieve_top_k_limits_results(client: TestClient) -> None:
    upload_sample_product_docs(client)

    response = client.post("/api/knowledge/retrieve", json={"query": "系统 支持", "top_k": 2})

    assert response.status_code == 200
    assert len(response.json()) == 2


def upload_sample_product_docs(client: TestClient) -> int:
    sample_path = Path(__file__).resolve().parents[2] / "sample-data" / "product_docs.txt"
    content = sample_path.read_text(encoding="utf-8")
    response = client.post(
        "/api/knowledge/upload",
        files={"file": ("product_docs.txt", content.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]
