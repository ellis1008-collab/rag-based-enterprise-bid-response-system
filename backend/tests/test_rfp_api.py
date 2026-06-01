import pytest
from fastapi.testclient import TestClient

from tests.file_samples import make_docx, make_text_pdf, make_xlsx


def test_create_project(client: TestClient) -> None:
    response = client.post(
        "/api/rfp/projects",
        json={"name": "智慧园区投标", "customer_name": "示例客户"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "智慧园区投标"
    assert data["customer_name"] == "示例客户"
    assert data["status"] == "draft"


def test_project_crud(client: TestClient) -> None:
    created = client.post(
        "/api/rfp/projects",
        json={"name": "项目 CRUD 测试", "customer_name": "测试客户"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    list_response = client.get("/api/rfp/projects")
    assert list_response.status_code == 200
    assert any(project["id"] == project_id for project in list_response.json())

    get_response = client.get(f"/api/rfp/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "项目 CRUD 测试"

    delete_response = client.delete(f"/api/rfp/projects/{project_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "deleted"}

    missing_response = client.get(f"/api/rfp/projects/{project_id}")
    assert missing_response.status_code == 404


def test_upload_project_document(client: TestClient) -> None:
    project_response = client.post(
        "/api/rfp/projects",
        json={"name": "RFP 文档测试", "customer_name": "测试客户"},
    )
    project_id = project_response.json()["id"]

    upload_response = client.post(
        f"/api/rfp/projects/{project_id}/documents/upload",
        files={"file": ("customer-rfp.txt", b"RFP requirement text", "text/plain")},
    )

    assert upload_response.status_code == 201
    upload_data = upload_response.json()
    assert upload_data["project_id"] == project_id
    assert upload_data["filename"] == "customer-rfp.txt"
    assert upload_data["content_text"] == "RFP requirement text"

    list_response = client.get(f"/api/rfp/projects/{project_id}/documents")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


@pytest.mark.parametrize(
    ("filename", "raw_content", "expected_text"),
    [
        (
            "customer-rfp.pdf",
            make_text_pdf("PDF RFP requires private deployment and audit logs"),
            "PDF RFP requires private deployment",
        ),
        (
            "customer-rfp.docx",
            make_docx("DOCX RFP requires operation logs", [["Requirement", "500 concurrent users"]]),
            "Requirement\t500 concurrent users",
        ),
        (
            "customer-rfp.xlsx",
            make_xlsx("RFP", [["Code", "Requirement"], ["REQ-001", "Private deployment"]]),
            "Sheet: RFP",
        ),
    ],
    ids=["pdf", "docx", "xlsx"],
)
def test_upload_project_document_business_file_formats(
    client: TestClient,
    filename: str,
    raw_content: bytes,
    expected_text: str,
) -> None:
    project_response = client.post(
        "/api/rfp/projects",
        json={"name": "Business file upload", "customer_name": "Sample customer"},
    )
    project_id = project_response.json()["id"]

    upload_response = client.post(
        f"/api/rfp/projects/{project_id}/documents/upload",
        files={"file": (filename, raw_content, "application/octet-stream")},
    )

    assert upload_response.status_code == 201
    upload_data = upload_response.json()
    assert upload_data["filename"] == filename
    assert expected_text in upload_data["content_text"]
