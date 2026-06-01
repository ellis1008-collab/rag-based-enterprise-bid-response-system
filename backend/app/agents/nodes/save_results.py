from sqlalchemy import select

from app.agents.state import BidAgentState, RequirementState
from app.models import BidResponse, RfpRequirement


def save_results_node(state: BidAgentState) -> dict:
    if state["run_type"] == "extract_requirements":
        return _save_requirements(state)
    if state["run_type"] == "generate_responses":
        return _save_responses(state)
    raise ValueError(f"Unsupported run_type: {state['run_type']}")


def _save_requirements(state: BidAgentState) -> dict:
    db = state["db"]
    project_id = state["project_id"]
    for requirement in list(
        db.scalars(select(RfpRequirement).where(RfpRequirement.project_id == project_id))
    ):
        db.delete(requirement)
    db.flush()

    saved = [
        RfpRequirement(
            project_id=project_id,
            requirement_code=item["requirement_code"],
            category=item["category"],
            content=item["content"],
            priority=item["priority"],
            source_page=item.get("source_page"),
        )
        for item in state.get("requirements", [])
    ]
    db.add_all(saved)
    db.commit()

    requirements: list[RequirementState] = []
    for requirement in saved:
        db.refresh(requirement)
        requirements.append(
            {
                "id": requirement.id,
                "project_id": requirement.project_id,
                "requirement_code": requirement.requirement_code,
                "category": requirement.category,
                "content": requirement.content,
                "priority": requirement.priority,
                "source_page": requirement.source_page,
            }
        )

    return {"requirements": requirements}


def _save_responses(state: BidAgentState) -> dict:
    db = state["db"]
    project_id = state["project_id"]
    for response in list(db.scalars(select(BidResponse).where(BidResponse.project_id == project_id))):
        db.delete(response)
    db.flush()

    saved = [
        BidResponse(
            project_id=project_id,
            requirement_id=item["requirement_id"],
            match_status=item["match_status"],
            response_text=item["response_text"],
            risk_level=item["risk_level"],
            source_chunks_json=item["source_chunks"],
        )
        for item in state.get("responses", [])
    ]
    db.add_all(saved)
    db.commit()
    return {"responses": state.get("responses", [])}
