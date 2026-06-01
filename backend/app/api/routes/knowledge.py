from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import KnowledgeChunk, KnowledgeFile
from app.rag import RetrieveRequest, RetrievedChunk
from app.schemas import KnowledgeChunkRead, KnowledgeFileRead
from app.services import FileParserError, FileParserService, index_knowledge_chunks, retrieve_knowledge, split_text_by_length

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def get_knowledge_file_or_404(db: Session, file_id: int) -> KnowledgeFile:
    knowledge_file = db.get(KnowledgeFile, file_id)
    if knowledge_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge file not found.",
        )
    return knowledge_file


@router.post("/upload", response_model=KnowledgeFileRead, status_code=status.HTTP_201_CREATED)
async def upload_knowledge_file(file: UploadFile, db: Session = Depends(get_db)) -> KnowledgeFile:
    settings = get_settings()
    try:
        parsed_file = await FileParserService().parse_upload_file(file)
    except FileParserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    knowledge_file = KnowledgeFile(
        filename=parsed_file.filename,
        content_text=parsed_file.content_text,
        status="uploaded",
    )
    db.add(knowledge_file)
    db.flush()

    chunks = split_text_by_length(parsed_file.content_text, settings.knowledge_chunk_size)
    knowledge_chunks: list[KnowledgeChunk] = []
    for chunk_index, chunk_content in enumerate(chunks):
        knowledge_chunk = KnowledgeChunk(
            file_id=knowledge_file.id,
            chunk_index=chunk_index,
            content=chunk_content,
            metadata_json={
                "filename": parsed_file.filename,
                "chunk_size": settings.knowledge_chunk_size,
                "chunk_index": chunk_index,
                "splitter": "TextSplitter",
            },
        )
        db.add(knowledge_chunk)
        knowledge_chunks.append(knowledge_chunk)

    db.commit()
    db.refresh(knowledge_file)
    index_knowledge_chunks(knowledge_chunks)
    return knowledge_file


@router.get("/files", response_model=list[KnowledgeFileRead])
def list_knowledge_files(db: Session = Depends(get_db)) -> list[KnowledgeFile]:
    return list(db.scalars(select(KnowledgeFile).order_by(KnowledgeFile.created_at.desc())))


@router.post("/retrieve", response_model=list[RetrievedChunk])
def retrieve_knowledge_chunks(
    payload: RetrieveRequest,
    db: Session = Depends(get_db),
) -> list[RetrievedChunk]:
    return retrieve_knowledge(db=db, query=payload.query, top_k=payload.top_k)


@router.get("/files/{file_id}", response_model=KnowledgeFileRead)
def get_knowledge_file(file_id: int, db: Session = Depends(get_db)) -> KnowledgeFile:
    return get_knowledge_file_or_404(db, file_id)


@router.get("/files/{file_id}/chunks", response_model=list[KnowledgeChunkRead])
def list_knowledge_chunks(file_id: int, db: Session = Depends(get_db)) -> list[KnowledgeChunk]:
    get_knowledge_file_or_404(db, file_id)
    return list(
        db.scalars(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.file_id == file_id)
            .order_by(KnowledgeChunk.chunk_index.asc())
        )
    )
