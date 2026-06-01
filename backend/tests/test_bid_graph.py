from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentRun


def test_langgraph_extract_requirements_flow(client: TestClient, db_session: Session) -> None:
    project_id = create_project(client)
    upload_sample_rfp(client, project_id)

    response = client.post(f"/api/rfp/projects/{project_id}/extract-requirements")

    assert response.status_code == 200
    assert len(response.json()) == 8
    agent_run = latest_agent_run(db_session, project_id, "extract_requirements")
    steps_json = agent_run.steps_json
    assert steps_json["graph"] == "bid_agent"
    assert_langgraph_node_chain(
        steps_json,
        ["load_project_context", "extract_requirements_node", "save_results_node"],
    )


def test_langgraph_response_matrix_flow(client: TestClient, db_session: Session) -> None:
    project_id = create_project(client)
    upload_sample_rfp(client, project_id)
    upload_sample_product_docs(client)
    client.post(f"/api/rfp/projects/{project_id}/extract-requirements")

    response = client.post(f"/api/rfp/projects/{project_id}/generate-responses")

    assert response.status_code == 200
    responses = response.json()
    assert len(responses) == 8
    assert sum(1 for item in responses if item["risk_level"] == "low") == 6
    assert sum(1 for item in responses if item["risk_level"] == "medium") == 2

    agent_run = latest_agent_run(db_session, project_id, "generate_responses")
    steps_json = agent_run.steps_json
    assert steps_json["generated_response_count"] == 8
    assert steps_json["risk_summary"] == {"low": 6, "medium": 2, "high": 0}
    retrieve_node = next(node for node in steps_json["langgraph_nodes"] if node["node_name"] == "retrieve_knowledge_node")
    assert retrieve_node["output_summary"]["retriever_types"] == ["simple"]
    assert_langgraph_node_chain(
        steps_json,
        [
            "load_project_context",
            "retrieve_knowledge_node",
            "generate_responses_node",
            "assess_risk_node",
            "save_results_node",
        ],
    )


def assert_langgraph_node_chain(steps_json: dict, expected_node_names: list[str]) -> None:
    node_names = [node["node_name"] for node in steps_json["langgraph_nodes"]]
    assert node_names == expected_node_names
    for node in steps_json["langgraph_nodes"]:
        assert node["status"] == "completed"
        assert isinstance(node["input_summary"], dict)
        assert isinstance(node["output_summary"], dict)
        assert isinstance(node["latency_ms"], int)
        assert node["error_message"] is None

    step_node_names = {step["node_name"] for step in steps_json["steps"]}
    assert set(expected_node_names).issubset(step_node_names)


def latest_agent_run(db_session: Session, project_id: int, run_type: str) -> AgentRun:
    agent_run = db_session.scalar(
        select(AgentRun)
        .where(AgentRun.project_id == project_id, AgentRun.run_type == run_type)
        .order_by(AgentRun.id.desc())
    )
    assert agent_run is not None
    assert agent_run.status == "succeeded"
    assert agent_run.finished_at is not None
    return agent_run


def create_project(client: TestClient) -> int:
    response = client.post(
        "/api/rfp/projects",
        json={"name": "LangGraph 测试项目", "customer_name": "示例客户"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def upload_sample_rfp(client: TestClient, project_id: int) -> None:
    sample_path = Path(__file__).resolve().parents[2] / "sample-data" / "sample_rfp.txt"
    content = sample_path.read_text(encoding="utf-8")
    response = client.post(
        f"/api/rfp/projects/{project_id}/documents/upload",
        files={"file": ("sample_rfp.txt", content.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201


def upload_sample_product_docs(client: TestClient) -> None:
    sample_path = Path(__file__).resolve().parents[2] / "sample-data" / "product_docs.txt"
    content = sample_path.read_text(encoding="utf-8")
    response = client.post(
        "/api/knowledge/upload",
        files={"file": ("product_docs.txt", content.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 201
