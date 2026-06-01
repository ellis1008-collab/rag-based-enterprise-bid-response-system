from typing import Any, Literal, TypedDict

from sqlalchemy.orm import Session


RunType = Literal["extract_requirements", "generate_responses"]


class RequirementState(TypedDict, total=False):
    id: int
    project_id: int
    requirement_code: str
    category: str
    content: str
    priority: str
    source_page: int | None


class RetrievedChunkState(TypedDict):
    chunk_id: int
    file_id: int
    content: str
    score: float
    metadata: dict[str, Any]
    retriever_type: str
    content_summary: str


class RetrievedContextState(TypedDict):
    requirement_id: int
    requirement_code: str
    query: str
    retrieved_chunks: list[RetrievedChunkState]


class BidResponseState(TypedDict):
    project_id: int
    requirement_id: int
    match_status: str
    response_text: str
    risk_level: str
    source_chunks: list[dict[str, Any]]


class NodeTrace(TypedDict):
    node_name: str
    status: str
    input_summary: dict[str, Any]
    output_summary: dict[str, Any]
    latency_ms: int
    error_message: str | None


class BidAgentState(TypedDict, total=False):
    db: Session
    project_id: int
    agent_run_id: int
    run_type: RunType
    top_k: int
    project: dict[str, Any]
    rfp_documents: list[dict[str, Any]]
    rfp_text: str
    knowledge_file_count: int
    extraction_prompt_chars: int
    extraction_schema: str
    requirements: list[RequirementState]
    retrieved_contexts: list[RetrievedContextState]
    responses: list[BidResponseState]
    risk_summary: dict[str, Any]
    steps: list[dict[str, Any]]
    langgraph_nodes: list[NodeTrace]
    errors: list[str]


def truncate_text(value: str, limit: int = 160) -> str:
    normalized = value.replace("\n", " ").strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def retrieved_chunk_count(state: BidAgentState) -> int:
    return sum(len(context["retrieved_chunks"]) for context in state.get("retrieved_contexts", []))


def retrieved_chunk_retriever_types(state: BidAgentState) -> list[str]:
    retriever_types = {
        chunk["retriever_type"]
        for context in state.get("retrieved_contexts", [])
        for chunk in context["retrieved_chunks"]
    }
    return sorted(retriever_types)
