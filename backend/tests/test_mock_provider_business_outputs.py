import asyncio
import json

from app.llm.mock_provider import MockLLMProvider
from app.llm.schemas import RequirementExtractionResult
from app.schemas import BidResponseGenerationResult


def test_mock_provider_returns_requirement_extraction_result() -> None:
    provider = MockLLMProvider()

    response = asyncio.run(provider.invoke_text("extract sample RFP", prompt_type="extract_requirements"))
    result = RequirementExtractionResult.model_validate_json(response.content)

    assert len(result.requirements) == 8
    assert result.requirements[0].requirement_code == "REQ-001"
    assert result.requirements[0].category == "权限管理"
    assert result.requirements[-1].requirement_code == "REQ-008"
    assert result.requirements[-1].category == "备份容灾"


def test_mock_provider_returns_response_generation_result() -> None:
    provider = MockLLMProvider()
    prompt = build_response_prompt(
        requirement_id=7,
        content="系统需支持高并发访问，满足 500 名用户同时在线。",
        chunk_content="当前标准版本支持 300 名并发用户，如需支持 500 名并发用户，需要集群扩容和性能压测。",
    )

    response = asyncio.run(provider.invoke_text(prompt, prompt_type="generate_response"))
    result = BidResponseGenerationResult.model_validate_json(response.content)
    item = result.responses[0]

    assert item.requirement_id == 7
    assert item.match_status == "partial"
    assert item.risk_level == "medium"
    assert "集群扩容" in item.response_text
    assert len(item.source_chunks) == 1


def test_mock_provider_response_output_is_stable() -> None:
    provider = MockLLMProvider()
    prompt = build_response_prompt(
        requirement_id=4,
        content="系统需支持通过 API 与第三方系统集成。",
        chunk_content="平台提供标准 REST API，可与 CRM、ERP、OA 等第三方系统集成。",
    )

    first = asyncio.run(provider.invoke_text(prompt, prompt_type="generate_response"))
    second = asyncio.run(provider.invoke_text(prompt, prompt_type="generate_response"))

    assert first.content == second.content
    result = BidResponseGenerationResult.model_validate_json(first.content)
    item = result.responses[0]
    assert item.match_status == "satisfied"
    assert item.risk_level == "low"


def build_response_prompt(requirement_id: int, content: str, chunk_content: str) -> str:
    payload = {
        "requirement": {"id": requirement_id, "content": content},
        "retrieved_chunks": [
            {
                "chunk_id": 1,
                "file_id": 1,
                "content": chunk_content,
                "score": 10.0,
                "metadata": {"filename": "product_docs.txt"},
            }
        ],
    }
    return f"```json\n{json.dumps(payload, ensure_ascii=False)}\n```"
