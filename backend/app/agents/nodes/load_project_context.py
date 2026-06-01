from sqlalchemy import func, select

from app.agents.state import BidAgentState, RequirementState
from app.models import KnowledgeFile, RfpDocument, RfpProject, RfpRequirement


def load_project_context(state: BidAgentState) -> dict:
    db = state["db"]
    project_id = state["project_id"]
    project = db.get(RfpProject, project_id)
    if project is None:
        raise ValueError("RFP project not found.")

    documents = list(
        db.scalars(
            select(RfpDocument)
            .where(RfpDocument.project_id == project_id)
            .order_by(RfpDocument.created_at.asc())
        )
    )
    requirements = list(
        db.scalars(
            select(RfpRequirement)
            .where(RfpRequirement.project_id == project_id)
            .order_by(RfpRequirement.id.asc())
        )
    )
    knowledge_file_count = db.scalar(select(func.count(KnowledgeFile.id))) or 0

    if state["run_type"] == "extract_requirements" and not documents:
        raise ValueError("No RFP documents found for this project.")

    if state["run_type"] == "generate_responses" and not requirements:
        raise ValueError("No RFP requirements found for this project.")

    document_payloads = [
        {
            "id": document.id,
            "filename": document.filename,
            "content_text": document.content_text,
            "created_at": document.created_at.isoformat(),
        }
        for document in documents
    ]
    requirement_payloads: list[RequirementState] = [
        {
            "id": requirement.id,
            "project_id": requirement.project_id,
            "requirement_code": requirement.requirement_code,
            "category": requirement.category,
            "content": requirement.content,
            "priority": requirement.priority,
            "source_page": requirement.source_page,
        }
        for requirement in requirements
    ]

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "customer_name": project.customer_name,
            "status": project.status,
        },
        "rfp_documents": document_payloads,
        "rfp_text": "\n\n".join(document["content_text"] for document in document_payloads),
        "knowledge_file_count": knowledge_file_count,
        "requirements": requirement_payloads,
    }
