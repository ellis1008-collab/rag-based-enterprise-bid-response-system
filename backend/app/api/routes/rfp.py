import csv
import io
import re
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AgentRun, RfpDocument, RfpProject
from app.schemas import (
    AgentRunRead,
    BidResponseRead,
    BidResponseUpdate,
    DeleteResponse,
    RiskReport,
    RfpDocumentRead,
    RfpProjectCreate,
    RfpProjectRead,
    RfpRequirementRead,
)
from app.services import (
    BidResponseGenerationError,
    BidResponseUpdateError,
    DOCX_MEDIA_TYPE,
    DeliverableExportError,
    RequirementExtractionError,
    build_response_export_rows,
    build_proposal_docx,
    build_risk_report,
    build_response_matrix_xlsx,
    extract_requirements_for_project,
    FileParserError,
    FileParserService,
    generate_bid_responses_for_project,
    list_project_bid_responses,
    list_project_requirements,
    update_bid_response,
    XLSX_MEDIA_TYPE,
)

router = APIRouter(prefix="/rfp", tags=["rfp"])


def get_project_or_404(db: Session, project_id: int) -> RfpProject:
    project = db.get(RfpProject, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFP project not found.",
        )
    return project


@router.post("/projects", response_model=RfpProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: RfpProjectCreate, db: Session = Depends(get_db)) -> RfpProject:
    project = RfpProject(
        name=payload.name,
        customer_name=payload.customer_name,
        status=payload.status,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[RfpProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[RfpProject]:
    return list(db.scalars(select(RfpProject).order_by(RfpProject.created_at.desc())))


@router.get("/projects/{project_id}", response_model=RfpProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> RfpProject:
    return get_project_or_404(db, project_id)


@router.delete("/projects/{project_id}", response_model=DeleteResponse)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> DeleteResponse:
    project = get_project_or_404(db, project_id)
    db.delete(project)
    db.commit()
    return DeleteResponse(status="deleted")


@router.post(
    "/projects/{project_id}/documents/upload",
    response_model=RfpDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_project_document(
    project_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
) -> RfpDocument:
    get_project_or_404(db, project_id)
    try:
        parsed_file = await FileParserService().parse_upload_file(file)
    except FileParserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    document = RfpDocument(
        project_id=project_id,
        filename=parsed_file.filename,
        content_text=parsed_file.content_text,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/projects/{project_id}/documents", response_model=list[RfpDocumentRead])
def list_project_documents(project_id: int, db: Session = Depends(get_db)) -> list[RfpDocument]:
    get_project_or_404(db, project_id)
    return list(
        db.scalars(
            select(RfpDocument)
            .where(RfpDocument.project_id == project_id)
            .order_by(RfpDocument.created_at.desc())
        )
    )


@router.post(
    "/projects/{project_id}/extract-requirements",
    response_model=list[RfpRequirementRead],
)
async def extract_project_requirements(project_id: int, db: Session = Depends(get_db)):
    get_project_or_404(db, project_id)
    try:
        return await extract_requirements_for_project(db, project_id)
    except RequirementExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/projects/{project_id}/requirements", response_model=list[RfpRequirementRead])
def get_project_requirements(project_id: int, db: Session = Depends(get_db)):
    get_project_or_404(db, project_id)
    return list_project_requirements(db, project_id)


@router.post(
    "/projects/{project_id}/generate-responses",
    response_model=list[BidResponseRead],
)
async def generate_project_responses(project_id: int, db: Session = Depends(get_db)):
    get_project_or_404(db, project_id)
    try:
        return await generate_bid_responses_for_project(db, project_id)
    except BidResponseGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/projects/{project_id}/responses", response_model=list[BidResponseRead])
def get_project_responses(project_id: int, db: Session = Depends(get_db)):
    get_project_or_404(db, project_id)
    return list_project_bid_responses(db, project_id)


@router.patch(
    "/projects/{project_id}/responses/{response_id}",
    response_model=BidResponseRead,
)
def update_project_response(
    project_id: int,
    response_id: int,
    payload: BidResponseUpdate,
    db: Session = Depends(get_db),
) -> BidResponseRead:
    get_project_or_404(db, project_id)
    try:
        return update_bid_response(db, project_id, response_id, payload)
    except BidResponseUpdateError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/projects/{project_id}/responses/export-csv")
def export_project_responses_csv(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = get_project_or_404(db, project_id)
    rows = build_response_export_rows(db, project_id)
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "requirement_code",
            "category",
            "priority",
            "requirement_content",
            "match_status",
            "risk_level",
            "response_text",
            "source_summary",
            "human_status",
            "human_note",
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row.__dict__)

    filename = _csv_filename(project)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/projects/{project_id}/responses/export-xlsx")
def export_project_responses_xlsx(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = get_project_or_404(db, project_id)
    try:
        export = build_response_matrix_xlsx(db, project_id)
    except DeliverableExportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    filename = _export_filename(project, "responses.xlsx")
    return Response(
        content=export.content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/projects/{project_id}/proposal/export-docx")
def export_project_proposal_docx(project_id: int, db: Session = Depends(get_db)) -> Response:
    project = get_project_or_404(db, project_id)
    try:
        export = build_proposal_docx(db, project)
    except DeliverableExportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    filename = _export_filename(project, "proposal.docx")
    return Response(
        content=export.content,
        media_type=DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/projects/{project_id}/risk-report", response_model=RiskReport)
def get_project_risk_report(project_id: int, db: Session = Depends(get_db)) -> RiskReport:
    get_project_or_404(db, project_id)
    return build_risk_report(db, project_id)


@router.get("/projects/{project_id}/runs", response_model=list[AgentRunRead])
def get_project_agent_runs(project_id: int, db: Session = Depends(get_db)):
    get_project_or_404(db, project_id)
    return list(
        db.scalars(
            select(AgentRun)
            .where(AgentRun.project_id == project_id)
            .order_by(AgentRun.created_at.desc())
        )
    )


def _csv_filename(project: RfpProject) -> str:
    safe_name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", project.name).strip("_")
    name_part = safe_name or f"project_{project.id}"
    return f"bidpilot_{project.id}_{name_part}_responses.csv"


def _export_filename(project: RfpProject, suffix: str) -> str:
    safe_name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", project.name).strip("_")
    name_part = safe_name or f"project_{project.id}"
    return f"bidpilot_{project.id}_{name_part}_{suffix}"
