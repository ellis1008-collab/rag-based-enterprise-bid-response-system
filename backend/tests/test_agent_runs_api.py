from pathlib import Path

from fastapi.testclient import TestClient


def test_list_project_agent_runs(client: TestClient) -> None:
    project = client.post(
        "/api/rfp/projects",
        json={"name": "AgentRun 项目", "customer_name": "样例客户"},
    ).json()
    project_id = project["id"]
    sample_path = Path(__file__).resolve().parents[2] / "sample-data" / "sample_rfp.txt"
    content = sample_path.read_text(encoding="utf-8")
    client.post(
        f"/api/rfp/projects/{project_id}/documents/upload",
        files={"file": ("sample_rfp.txt", content.encode("utf-8"), "text/plain")},
    )
    client.post(f"/api/rfp/projects/{project_id}/extract-requirements")

    response = client.get(f"/api/rfp/projects/{project_id}/runs")

    assert response.status_code == 200
    runs = response.json()
    assert len(runs) == 1
    assert runs[0]["run_type"] == "extract_requirements"
    assert runs[0]["status"] == "succeeded"
    assert runs[0]["steps_json"]
