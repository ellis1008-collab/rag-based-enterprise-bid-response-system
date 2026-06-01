import inspect
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents.nodes import (
    assess_risk_node,
    extract_requirements_node,
    generate_responses_node,
    load_project_context,
    retrieve_knowledge_node,
    save_results_node,
)
from app.agents.state import BidAgentState, NodeTrace, retrieved_chunk_count, retrieved_chunk_retriever_types
from app.models import AgentRun
from app.models.timestamps import utc_now

NodeCallable = Callable[[BidAgentState], dict[str, Any] | Awaitable[dict[str, Any]]]


async def run_requirement_extraction_graph(
    db: Session,
    project_id: int,
    agent_run_id: int,
) -> BidAgentState:
    graph = build_requirement_extraction_graph()
    return await graph.ainvoke(_initial_state(db, project_id, agent_run_id, "extract_requirements"))


async def run_response_matrix_graph(
    db: Session,
    project_id: int,
    agent_run_id: int,
    top_k: int = 3,
) -> BidAgentState:
    graph = build_response_matrix_graph()
    return await graph.ainvoke(_initial_state(db, project_id, agent_run_id, "generate_responses", top_k=top_k))


def build_requirement_extraction_graph():
    graph = StateGraph(BidAgentState)
    graph.add_node("load_project_context", _instrument_node("load_project_context", load_project_context))
    graph.add_node("extract_requirements_node", _instrument_node("extract_requirements_node", extract_requirements_node))
    graph.add_node("save_results_node", _instrument_node("save_results_node", save_results_node))
    graph.add_edge(START, "load_project_context")
    graph.add_edge("load_project_context", "extract_requirements_node")
    graph.add_edge("extract_requirements_node", "save_results_node")
    graph.add_edge("save_results_node", END)
    return graph.compile()


def build_response_matrix_graph():
    graph = StateGraph(BidAgentState)
    graph.add_node("load_project_context", _instrument_node("load_project_context", load_project_context))
    graph.add_node("retrieve_knowledge_node", _instrument_node("retrieve_knowledge_node", retrieve_knowledge_node))
    graph.add_node("generate_responses_node", _instrument_node("generate_responses_node", generate_responses_node))
    graph.add_node("assess_risk_node", _instrument_node("assess_risk_node", assess_risk_node))
    graph.add_node("save_results_node", _instrument_node("save_results_node", save_results_node))
    graph.add_edge(START, "load_project_context")
    graph.add_edge("load_project_context", "retrieve_knowledge_node")
    graph.add_edge("retrieve_knowledge_node", "generate_responses_node")
    graph.add_edge("generate_responses_node", "assess_risk_node")
    graph.add_edge("assess_risk_node", "save_results_node")
    graph.add_edge("save_results_node", END)
    return graph.compile()


def _initial_state(
    db: Session,
    project_id: int,
    agent_run_id: int,
    run_type: str,
    top_k: int = 3,
) -> BidAgentState:
    return {
        "db": db,
        "project_id": project_id,
        "agent_run_id": agent_run_id,
        "run_type": run_type,
        "top_k": top_k,
        "rfp_text": "",
        "requirements": [],
        "retrieved_contexts": [],
        "responses": [],
        "risk_summary": {},
        "steps": [],
        "langgraph_nodes": [],
        "errors": [],
    }


def _instrument_node(node_name: str, node: NodeCallable):
    async def wrapped(state: BidAgentState) -> dict[str, Any]:
        input_summary = _input_summary(node_name, state)
        started_at = perf_counter()
        try:
            result = node(state)
            update = await result if inspect.isawaitable(result) else result
            next_state: BidAgentState = {**state, **update}
            trace = _node_trace(
                node_name=node_name,
                status="completed",
                input_summary=input_summary,
                output_summary=_output_summary(node_name, next_state),
                started_at=started_at,
            )
            return _finalize_node(state=state, update=update, trace=trace)
        except Exception as exc:
            trace = _node_trace(
                node_name=node_name,
                status="failed",
                input_summary=input_summary,
                output_summary={},
                started_at=started_at,
                error_message=str(exc),
            )
            failed_update = _finalize_node(state=state, update={}, trace=trace, error_message=str(exc))
            _sync_agent_run({**state, **failed_update}, status="failed", error_message=str(exc), finished=True)
            raise

    return wrapped


def _finalize_node(
    state: BidAgentState,
    update: dict[str, Any],
    trace: NodeTrace,
    error_message: str | None = None,
) -> dict[str, Any]:
    next_state: BidAgentState = {**state, **update}
    next_state["langgraph_nodes"] = [*state.get("langgraph_nodes", []), trace]
    next_state["steps"] = [*state.get("steps", []), *_legacy_steps(trace, next_state)]
    if error_message:
        next_state["errors"] = [*state.get("errors", []), error_message]

    status = "succeeded" if trace["node_name"] == "save_results_node" and trace["status"] == "completed" else "running"
    _sync_agent_run(next_state, status=status, finished=status == "succeeded")
    return {**update, "langgraph_nodes": next_state["langgraph_nodes"], "steps": next_state["steps"], "errors": next_state.get("errors", [])}


def _node_trace(
    node_name: str,
    status: str,
    input_summary: dict[str, Any],
    output_summary: dict[str, Any],
    started_at: float,
    error_message: str | None = None,
) -> NodeTrace:
    return {
        "node_name": node_name,
        "status": status,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "latency_ms": max(0, round((perf_counter() - started_at) * 1000)),
        "error_message": error_message,
    }


def _sync_agent_run(
    state: BidAgentState,
    status: str,
    error_message: str | None = None,
    finished: bool = False,
) -> None:
    db = state.get("db")
    agent_run_id = state.get("agent_run_id")
    if db is None or agent_run_id is None:
        return

    agent_run = db.get(AgentRun, agent_run_id)
    if agent_run is None:
        return

    agent_run.status = status
    agent_run.steps_json = _steps_json(state)
    agent_run.error_message = error_message
    if finished:
        agent_run.finished_at = utc_now()
    db.add(agent_run)
    db.commit()


def _steps_json(state: BidAgentState) -> dict[str, Any]:
    risk_level_counts = state.get("risk_summary", {}).get("risk_level_counts", {})
    return {
        "graph": "bid_agent",
        "run_type": state.get("run_type"),
        "requirement_count": len(state.get("requirements", [])),
        "retrieved_chunk_count": retrieved_chunk_count(state),
        "generated_response_count": len(state.get("responses", [])),
        "risk_summary": risk_level_counts,
        "risk_summary_detail": state.get("risk_summary", {}),
        "steps": state.get("steps", []),
        "langgraph_nodes": state.get("langgraph_nodes", []),
        "errors": state.get("errors", []),
    }


def _input_summary(node_name: str, state: BidAgentState) -> dict[str, Any]:
    if node_name == "load_project_context":
        return {"project_id": state.get("project_id"), "run_type": state.get("run_type")}
    if node_name == "extract_requirements_node":
        return {"document_count": len(state.get("rfp_documents", [])), "rfp_chars": len(state.get("rfp_text", ""))}
    if node_name == "retrieve_knowledge_node":
        return {"requirement_count": len(state.get("requirements", [])), "top_k": state.get("top_k", 3)}
    if node_name == "generate_responses_node":
        return {
            "requirement_count": len(state.get("requirements", [])),
            "retrieved_chunk_count": retrieved_chunk_count(state),
        }
    if node_name == "assess_risk_node":
        return {"response_count": len(state.get("responses", []))}
    if node_name == "save_results_node":
        return {
            "run_type": state.get("run_type"),
            "requirement_count": len(state.get("requirements", [])),
            "response_count": len(state.get("responses", [])),
        }
    return {}


def _output_summary(node_name: str, state: BidAgentState) -> dict[str, Any]:
    if node_name == "load_project_context":
        return {
            "document_count": len(state.get("rfp_documents", [])),
            "requirement_count": len(state.get("requirements", [])),
            "knowledge_file_count": state.get("knowledge_file_count", 0),
            "rfp_chars": len(state.get("rfp_text", "")),
        }
    if node_name == "extract_requirements_node":
        return {
            "requirement_count": len(state.get("requirements", [])),
            "schema": state.get("extraction_schema"),
            "prompt_chars": state.get("extraction_prompt_chars"),
        }
    if node_name == "retrieve_knowledge_node":
        return {
            "retrieval_count": len(state.get("retrieved_contexts", [])),
            "retrieved_chunk_count": retrieved_chunk_count(state),
            "retriever_types": retrieved_chunk_retriever_types(state),
        }
    if node_name == "generate_responses_node":
        return {"generated_response_count": len(state.get("responses", []))}
    if node_name == "assess_risk_node":
        return state.get("risk_summary", {})
    if node_name == "save_results_node":
        return {
            "run_type": state.get("run_type"),
            "saved_requirements": len(state.get("requirements", [])) if state.get("run_type") == "extract_requirements" else 0,
            "saved_responses": len(state.get("responses", [])) if state.get("run_type") == "generate_responses" else 0,
        }
    return {}


def _legacy_steps(trace: NodeTrace, state: BidAgentState) -> list[dict[str, Any]]:
    node_name = trace["node_name"]
    if state.get("run_type") == "extract_requirements":
        return _legacy_extraction_steps(node_name, trace, state)
    if state.get("run_type") == "generate_responses":
        return _legacy_response_steps(node_name, trace, state)
    return [_legacy_step(node_name, trace, state)]


def _legacy_extraction_steps(node_name: str, trace: NodeTrace, state: BidAgentState) -> list[dict[str, Any]]:
    if node_name == "load_project_context":
        documents = state.get("rfp_documents", [])
        return [
            _legacy_step(
                "load_rfp_document",
                trace,
                state,
                document_count=len(documents),
                filenames=[document["filename"] for document in documents],
                total_chars=len(state.get("rfp_text", "")),
            )
        ]
    if node_name == "extract_requirements_node":
        return [
            _legacy_step("build_prompt", trace, state, prompt_chars=state.get("extraction_prompt_chars", 0)),
            _legacy_step("call_llm", trace, state, prompt_type="extract_requirements"),
            _legacy_step(
                "validate_schema",
                trace,
                state,
                requirement_count=len(state.get("requirements", [])),
                schema=state.get("extraction_schema", "RequirementExtractionResult"),
            ),
        ]
    if node_name == "save_results_node":
        return [_legacy_step("save_requirements", trace, state, requirement_count=len(state.get("requirements", [])))]
    return [_legacy_step(node_name, trace, state)]


def _legacy_response_steps(node_name: str, trace: NodeTrace, state: BidAgentState) -> list[dict[str, Any]]:
    if node_name == "load_project_context":
        return [_legacy_step("load_requirements", trace, state, requirement_count=len(state.get("requirements", [])))]
    if node_name == "retrieve_knowledge_node":
        return [
            _legacy_step(
                "retrieve_knowledge",
                trace,
                state,
                retrieved_chunk_count=retrieved_chunk_count(state),
                retriever_types=retrieved_chunk_retriever_types(state),
                retrievals=_retrievals_for_log(state),
            )
        ]
    if node_name == "generate_responses_node":
        return [
            _legacy_step(
                "call_llm_for_each_requirement",
                trace,
                state,
                prompt_type="generate_response",
                call_count=len(state.get("requirements", [])),
            ),
            _legacy_step(
                "validate_schema",
                trace,
                state,
                schema="BidResponseGenerationResult",
                generated_response_count=len(state.get("responses", [])),
            ),
        ]
    if node_name == "assess_risk_node":
        return []
    if node_name == "save_results_node":
        risk_summary = state.get("risk_summary", {}).get("risk_level_counts", {})
        risk_trace: NodeTrace = {**trace, "node_name": "assess_risk_node"}
        return [
            _legacy_step("save_bid_responses", trace, state, generated_response_count=len(state.get("responses", []))),
            _legacy_step("build_risk_summary", risk_trace, state, risk_summary=risk_summary),
        ]
    return [_legacy_step(node_name, trace, state)]


def _legacy_step(name: str, trace: NodeTrace, state: BidAgentState, **extra: Any) -> dict[str, Any]:
    return {
        "name": name,
        "node_name": trace["node_name"],
        "status": trace["status"],
        "input_summary": trace["input_summary"],
        "output_summary": trace["output_summary"],
        "latency_ms": trace["latency_ms"],
        "error_message": trace["error_message"],
        **extra,
    }


def _retrievals_for_log(state: BidAgentState) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": context["requirement_id"],
            "requirement_code": context["requirement_code"],
            "query": context["query"],
            "retrieved_chunks": [
                {
                    "chunk_id": chunk["chunk_id"],
                    "file_id": chunk["file_id"],
                    "score": chunk["score"],
                    "retriever_type": chunk["retriever_type"],
                    "content_summary": chunk["content_summary"],
                }
                for chunk in context["retrieved_chunks"]
            ],
        }
        for context in state.get("retrieved_contexts", [])
    ]
