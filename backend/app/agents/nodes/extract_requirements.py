import json

from app.agents.state import BidAgentState, RequirementState
from app.llm.service import LLMService
from app.schemas import RequirementExtractionResult
from app.services.prompt_template_service import PromptTemplateService


async def extract_requirements_node(state: BidAgentState) -> dict:
    prompt = build_extraction_prompt(state)
    extraction_result = await LLMService(state["db"]).invoke_json(
        prompt=prompt,
        output_schema=RequirementExtractionResult,
        prompt_type="extract_requirements",
    )
    if not extraction_result.requirements:
        raise ValueError(
            "No requirements were extracted from the RFP. "
            "The model returned an empty requirements list; please check the document text and model output."
        )

    requirements: list[RequirementState] = [
        {
            "project_id": state["project_id"],
            "requirement_code": item.requirement_code,
            "category": item.category,
            "content": item.content,
            "priority": item.priority,
            "source_page": item.source_page,
        }
        for item in extraction_result.requirements
    ]
    return {
        "requirements": requirements,
        "extraction_prompt_chars": len(prompt),
        "extraction_schema": "RequirementExtractionResult",
    }


def build_extraction_prompt(state: BidAgentState) -> str:
    project = state.get("project", {})
    documents = state.get("rfp_documents", [])
    document_sections = "\n\n".join(
        f"文件名：{document['filename']}\n内容：\n{document['content_text']}" for document in documents
    )
    rfp_text = (
        f"项目名称：{project.get('name', '')}\n"
        f"客户名称：{project.get('customer_name', '')}\n\n"
        f"{document_sections}"
    )
    return PromptTemplateService().render(
        "extract_requirements",
        rfp_text=rfp_text,
        output_schema=json.dumps(RequirementExtractionResult.model_json_schema(), ensure_ascii=False),
    )
