from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents import run_response_matrix_graph
from app.models import AgentRun, BidResponse, RfpProject, RfpRequirement
from app.models.timestamps import utc_now
from app.schemas import BidResponseRead, BidResponseUpdate, RiskReport, RiskReportItem


class BidResponseGenerationError(Exception):
    pass


class BidResponseUpdateError(Exception):
    pass


@dataclass(frozen=True)
class ResponseExportRow:
    requirement_code: str
    category: str
    priority: str
    requirement_content: str
    match_status: str
    risk_level: str
    response_text: str
    source_summary: str
    human_status: str
    human_note: str


def list_project_bid_responses(db: Session, project_id: int) -> list[BidResponseRead]:
    responses = list(
        db.scalars(
            select(BidResponse)
            .where(BidResponse.project_id == project_id)
            .order_by(BidResponse.requirement_id.asc())
        )
    )
    return [to_bid_response_read(response) for response in responses]


def build_response_export_rows(db: Session, project_id: int) -> list[ResponseExportRow]:
    rows: list[ResponseExportRow] = []
    for response, requirement in _list_response_pairs(db, project_id):
        rows.append(
            ResponseExportRow(
                requirement_code=requirement.requirement_code,
                category=requirement.category,
                priority=requirement.priority,
                requirement_content=requirement.content,
                match_status=response.match_status,
                risk_level=response.risk_level,
                response_text=response.response_text,
                source_summary=_source_summary(response.source_chunks_json or []),
                human_status=response.human_status or "pending",
                human_note=response.human_note or "",
            )
        )
    return rows


def build_risk_report(db: Session, project_id: int) -> RiskReport:
    requirements = _list_requirements(db, project_id)
    response_pairs = _list_response_pairs(db, project_id)
    responses = [response for response, _requirement in response_pairs]

    match_counts = Counter(response.match_status for response in responses)
    risk_counts = Counter(response.risk_level for response in responses)
    review_counts = Counter((response.human_status or "pending") for response in responses)
    risk_items: list[RiskReportItem] = []
    pending_confirmation_items: list[RiskReportItem] = []

    for response, requirement in response_pairs:
        item = _risk_report_item(response, requirement)
        if response.match_status in {"partial", "unsupported"} or response.risk_level in {"medium", "high"}:
            risk_items.append(item)
        if not response.source_chunks_json:
            pending_confirmation_items.append(item)

    return RiskReport(
        total_requirements=len(requirements),
        satisfied_count=match_counts["satisfied"],
        partial_count=match_counts["partial"],
        unsupported_count=match_counts["unsupported"],
        low_risk_count=risk_counts["low"],
        medium_risk_count=risk_counts["medium"],
        high_risk_count=risk_counts["high"],
        pending_review_count=review_counts["pending"],
        confirmed_count=review_counts["confirmed"],
        rejected_count=review_counts["rejected"],
        risk_items=risk_items,
        pending_confirmation_items=pending_confirmation_items,
    )


async def generate_bid_responses_for_project(
    db: Session,
    project_id: int,
    top_k: int = 3,
) -> list[BidResponseRead]:
    project = db.get(RfpProject, project_id)
    if project is None:
        raise BidResponseGenerationError("RFP project not found.")

    agent_run = AgentRun(
        project_id=project_id,
        run_type="generate_responses",
        status="running",
        steps_json={
            "graph": "bid_agent",
            "run_type": "generate_responses",
            "steps": [],
            "langgraph_nodes": [],
            "errors": [],
        },
    )
    db.add(agent_run)
    db.commit()
    db.refresh(agent_run)

    try:
        await run_response_matrix_graph(db=db, project_id=project_id, agent_run_id=agent_run.id, top_k=top_k)
        return list_project_bid_responses(db, project_id)
    except Exception as exc:
        if isinstance(exc, BidResponseGenerationError):
            raise
        raise BidResponseGenerationError(str(exc)) from exc


def update_bid_response(
    db: Session,
    project_id: int,
    response_id: int,
    payload: BidResponseUpdate,
) -> BidResponseRead:
    response = db.scalar(
        select(BidResponse).where(
            BidResponse.id == response_id,
            BidResponse.project_id == project_id,
        )
    )
    if response is None:
        raise BidResponseUpdateError("Bid response not found for this project.")

    updates = payload.model_dump(exclude_unset=True)
    if "match_status" in updates:
        response.match_status = updates["match_status"]
    if "response_text" in updates:
        response.response_text = updates["response_text"]
    if "risk_level" in updates:
        response.risk_level = updates["risk_level"]
    if "human_status" in updates:
        response.human_status = updates["human_status"]
    if "human_note" in updates:
        response.human_note = updates["human_note"] or ""

    response.updated_at = utc_now()
    db.commit()
    db.refresh(response)
    return to_bid_response_read(response)


def to_bid_response_read(response: BidResponse) -> BidResponseRead:
    return BidResponseRead(
        id=response.id,
        project_id=response.project_id,
        requirement_id=response.requirement_id,
        match_status=response.match_status,
        response_text=response.response_text,
        risk_level=response.risk_level,
        source_chunks=response.source_chunks_json or [],
        human_status=response.human_status or "pending",
        human_note=response.human_note or "",
        created_at=response.created_at,
        updated_at=response.updated_at or response.created_at,
    )


def _risk_report_item(response: BidResponse, requirement: RfpRequirement) -> RiskReportItem:
    return RiskReportItem(
        requirement_id=requirement.id,
        requirement_code=requirement.requirement_code,
        category=requirement.category,
        requirement_content=requirement.content,
        match_status=response.match_status,
        risk_level=response.risk_level,
        response_text=response.response_text,
        source_chunks=response.source_chunks_json or [],
        human_status=response.human_status or "pending",
        human_note=response.human_note or "",
    )


def _list_response_pairs(db: Session, project_id: int) -> list[tuple[BidResponse, RfpRequirement]]:
    return list(
        db.execute(
            select(BidResponse, RfpRequirement)
            .join(RfpRequirement, BidResponse.requirement_id == RfpRequirement.id)
            .where(BidResponse.project_id == project_id)
            .order_by(RfpRequirement.id.asc())
        )
    )


def _source_summary(source_chunks: list[dict]) -> str:
    summaries = []
    for chunk in source_chunks:
        chunk_id = chunk.get("chunk_id", "-")
        content = str(chunk.get("content", "")).replace("\n", " ").strip()
        summaries.append(f"#{chunk_id}: {content}")
    return " | ".join(summaries)


def _list_requirements(db: Session, project_id: int) -> list[RfpRequirement]:
    return list(
        db.scalars(
            select(RfpRequirement)
            .where(RfpRequirement.project_id == project_id)
            .order_by(RfpRequirement.id.asc())
        )
    )


def _clear_existing_responses(db: Session, project_id: int) -> None:
    existing_responses = list(
        db.scalars(select(BidResponse).where(BidResponse.project_id == project_id))
    )
    for response in existing_responses:
        db.delete(response)
    db.flush()

