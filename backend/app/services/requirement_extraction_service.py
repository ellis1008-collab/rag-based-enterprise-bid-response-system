from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import run_requirement_extraction_graph
from app.models import AgentRun, RfpProject, RfpRequirement


class RequirementExtractionError(Exception):
    pass


def list_project_requirements(db: Session, project_id: int) -> list[RfpRequirement]:
    return list(
        db.scalars(
            select(RfpRequirement)
            .where(RfpRequirement.project_id == project_id)
            .order_by(RfpRequirement.id.asc())
        )
    )


async def extract_requirements_for_project(db: Session, project_id: int) -> list[RfpRequirement]:
    project = db.get(RfpProject, project_id)
    if project is None:
        raise RequirementExtractionError("RFP project not found.")

    agent_run = AgentRun(
        project_id=project_id,
        run_type="extract_requirements",
        status="running",
        steps_json={
            "graph": "bid_agent",
            "run_type": "extract_requirements",
            "steps": [],
            "langgraph_nodes": [],
            "errors": [],
        },
    )
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    try:
        await run_requirement_extraction_graph(db=db, project_id=project_id, agent_run_id=agent_run.id)
        return list_project_requirements(db, project_id)
    except Exception as exc:
        if isinstance(exc, RequirementExtractionError):
            raise
        raise RequirementExtractionError(str(exc)) from exc
