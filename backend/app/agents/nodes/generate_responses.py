import json

from app.agents.state import BidAgentState, BidResponseState
from app.llm.service import LLMService
from app.schemas import BidResponseGenerationResult
from app.services.prompt_template_service import PromptTemplateService


async def generate_responses_node(state: BidAgentState) -> dict:
    responses: list[BidResponseState] = []
    requirement_by_id = {
        requirement["id"]: requirement
        for requirement in state.get("requirements", [])
        if requirement.get("id") is not None
    }

    for context in state.get("retrieved_contexts", []):
        requirement = requirement_by_id.get(context["requirement_id"])
        if requirement is None:
            raise ValueError(f"Requirement {context['requirement_id']} not found in graph state.")

        generation_result = await LLMService(state["db"]).invoke_json(
            prompt=build_response_prompt(requirement, context["retrieved_chunks"]),
            output_schema=BidResponseGenerationResult,
            prompt_type="generate_response",
        )
        if not generation_result.responses:
            raise ValueError(f"LLM returned no response for requirement {requirement['id']}.")

        item = generation_result.responses[0]
        responses.append(
            {
                "project_id": state["project_id"],
                "requirement_id": requirement["id"],
                "match_status": item.match_status,
                "response_text": item.response_text,
                "risk_level": item.risk_level,
                "source_chunks": [chunk.model_dump() for chunk in item.source_chunks],
            }
        )

    return {"responses": responses}


def build_response_prompt(requirement: dict, chunks: list[dict]) -> str:
    requirement_payload = {
        "id": requirement["id"],
        "requirement_code": requirement["requirement_code"],
        "category": requirement["category"],
        "content": requirement["content"],
        "priority": requirement["priority"],
        "source_page": requirement.get("source_page"),
    }
    retrieved_chunks_payload = [
        {
            "chunk_id": chunk["chunk_id"],
            "file_id": chunk["file_id"],
            "content": chunk["content"],
            "score": chunk["score"],
            "metadata": chunk["metadata"],
            "retriever_type": chunk["retriever_type"],
        }
        for chunk in chunks
    ]
    return PromptTemplateService().render(
        "generate_response",
        requirement=json.dumps(requirement_payload, ensure_ascii=False),
        retrieved_chunks=json.dumps(retrieved_chunks_payload, ensure_ascii=False),
        output_schema=json.dumps(BidResponseGenerationResult.model_json_schema(), ensure_ascii=False),
    )
