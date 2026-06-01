from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.llm.service import LLMService
from app.models import AgentRun, RfpRequirement


def test_extract_requirements_from_sample_rfp(client: TestClient, db_session: Session) -> None:
    project = client.post(
        "/api/rfp/projects",
        json={"name": "样例 RFP 项目", "customer_name": "样例客户"},
    ).json()
    project_id = project["id"]
    upload_sample_rfp(client, project_id)

    extract_response = client.post(f"/api/rfp/projects/{project_id}/extract-requirements")

    assert extract_response.status_code == 200
    extracted = extract_response.json()
    assert len(extracted) >= 5
    assert extracted[0]["requirement_code"] == "REQ-001"
    assert extracted[0]["category"] == "权限管理"

    list_response = client.get(f"/api/rfp/projects/{project_id}/requirements")
    assert list_response.status_code == 200
    requirements = list_response.json()
    assert len(requirements) == len(extracted)

    agent_run = db_session.scalar(
        select(AgentRun)
        .where(AgentRun.project_id == project_id, AgentRun.run_type == "extract_requirements")
        .order_by(AgentRun.id.desc())
    )
    assert agent_run is not None
    assert agent_run.status == "succeeded"
    assert agent_run.finished_at is not None
    assert agent_run.error_message is None
    assert agent_run.steps_json["steps"][-1]["requirement_count"] == len(extracted)


def test_extract_requirements_agent_run_steps_are_observable(client: TestClient, db_session: Session) -> None:
    project = client.post(
        "/api/rfp/projects",
        json={"name": "抽取日志测试", "customer_name": "样例客户"},
    ).json()
    project_id = project["id"]
    upload_sample_rfp(client, project_id)

    client.post(f"/api/rfp/projects/{project_id}/extract-requirements")

    agent_run = db_session.scalar(
        select(AgentRun)
        .where(AgentRun.project_id == project_id, AgentRun.run_type == "extract_requirements")
        .order_by(AgentRun.id.desc())
    )
    assert agent_run is not None
    steps = agent_run.steps_json["steps"]
    assert [step["name"] for step in steps] == [
        "load_rfp_document",
        "build_prompt",
        "call_llm",
        "validate_schema",
        "save_requirements",
    ]
    assert all(step["status"] == "completed" for step in steps)
    assert steps[0]["document_count"] == 1
    assert steps[2]["prompt_type"] == "extract_requirements"
    assert steps[3]["schema"] == "RequirementExtractionResult"


def test_extract_requirements_replaces_existing_requirements(client: TestClient, db_session: Session) -> None:
    project = client.post(
        "/api/rfp/projects",
        json={"name": "重复抽取测试", "customer_name": "样例客户"},
    ).json()
    project_id = project["id"]
    upload_sample_rfp(client, project_id)

    first = client.post(f"/api/rfp/projects/{project_id}/extract-requirements").json()
    second = client.post(f"/api/rfp/projects/{project_id}/extract-requirements").json()

    assert len(first) == len(second)
    stored_count = len(
        list(db_session.scalars(select(RfpRequirement).where(RfpRequirement.project_id == project_id)))
    )
    assert stored_count == len(second)


def test_extract_requirements_empty_model_output_fails_without_deleting_existing(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    project = client.post(
        "/api/rfp/projects",
        json={"name": "Empty extraction guard", "customer_name": "Example customer"},
    ).json()
    project_id = project["id"]
    upload_sample_rfp(client, project_id)
    db_session.add(
        RfpRequirement(
            project_id=project_id,
            requirement_code="REQ-OLD",
            category="Existing",
            content="Existing requirement should remain if extraction fails.",
            priority="low",
        )
    )
    db_session.commit()

    async def fake_invoke_json(self, *args, **kwargs):
        return SimpleNamespace(requirements=[])

    monkeypatch.setattr(LLMService, "invoke_json", fake_invoke_json)

    response = client.post(f"/api/rfp/projects/{project_id}/extract-requirements")

    assert response.status_code == 400
    assert "No requirements were extracted" in response.json()["detail"]
    stored = list(db_session.scalars(select(RfpRequirement).where(RfpRequirement.project_id == project_id)))
    assert [item.requirement_code for item in stored] == ["REQ-OLD"]

    agent_run = db_session.scalar(
        select(AgentRun)
        .where(AgentRun.project_id == project_id, AgentRun.run_type == "extract_requirements")
        .order_by(AgentRun.id.desc())
    )
    assert agent_run is not None
    assert agent_run.status == "failed"
    assert "No requirements were extracted" in (agent_run.error_message or "")


def upload_sample_rfp(client: TestClient, project_id: int) -> None:
    sample_path = Path(__file__).resolve().parents[2] / "sample-data" / "sample_rfp.txt"
    content = sample_path.read_text(encoding="utf-8")
    response = client.post(
        f"/api/rfp/projects/{project_id}/documents/upload",
        files={"file": ("sample_rfp.txt", content.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
