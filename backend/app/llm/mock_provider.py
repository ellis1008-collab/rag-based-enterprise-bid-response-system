import json
from typing import Any

from app.llm.base import BaseLLMProvider
from app.schemas.bid_response import BidResponseGenerationResult, BidResponseItem, SourceChunkItem
from app.llm.schemas import ProviderTextResponse, RequirementExtractionResult


MOCK_REQUIREMENTS = [
    {
        "requirement_code": "REQ-001",
        "category": "权限管理",
        "content": "系统需支持多角色权限管理，不同角色具备不同菜单和数据访问权限。",
        "priority": "high",
        "source_page": 1,
    },
    {
        "requirement_code": "REQ-002",
        "category": "日志审计",
        "content": "系统需支持完整操作日志审计，日志保存时间不少于 180 天。",
        "priority": "high",
        "source_page": 1,
    },
    {
        "requirement_code": "REQ-003",
        "category": "部署架构",
        "content": "系统需支持私有化部署，能够部署在客户内网环境。",
        "priority": "high",
        "source_page": 1,
    },
    {
        "requirement_code": "REQ-004",
        "category": "系统集成",
        "content": "系统需支持通过 API 与第三方系统集成。",
        "priority": "medium",
        "source_page": 1,
    },
    {
        "requirement_code": "REQ-005",
        "category": "安全能力",
        "content": "系统需支持数据加密传输。",
        "priority": "high",
        "source_page": 1,
    },
    {
        "requirement_code": "REQ-006",
        "category": "服务支持",
        "content": "系统需提供实施培训和上线支持服务。",
        "priority": "medium",
        "source_page": 1,
    },
    {
        "requirement_code": "REQ-007",
        "category": "性能容量",
        "content": "系统需支持高并发访问，满足 500 名用户同时在线。",
        "priority": "high",
        "source_page": 1,
    },
    {
        "requirement_code": "REQ-008",
        "category": "备份容灾",
        "content": "系统需支持数据备份和灾难恢复。",
        "priority": "high",
        "source_page": 1,
    },
]


class MockLLMProvider(BaseLLMProvider):
    provider_name = "mock"

    def __init__(self, model_name: str = "mock-model") -> None:
        self.model_name = model_name

    async def invoke_text(self, prompt: str, prompt_type: str = "text") -> ProviderTextResponse:
        if prompt_type == "extract_requirements":
            return ProviderTextResponse(content=self._extract_requirements_json())

        if prompt_type == "generate_response":
            return ProviderTextResponse(content=self._generate_response_json(prompt))

        schema = self._extract_json_schema(prompt)
        if schema is not None:
            content = json.dumps(self._sample_for_schema(schema), ensure_ascii=False)
            return ProviderTextResponse(content=content)

        if "请只回复 OK" in prompt or "only reply OK" in prompt.lower():
            return ProviderTextResponse(content="OK")

        return ProviderTextResponse(content="Mock response from BidPilot AI.")

    def _extract_requirements_json(self) -> str:
        result = RequirementExtractionResult.model_validate({"requirements": MOCK_REQUIREMENTS})
        return result.model_dump_json()

    def _generate_response_json(self, prompt: str) -> str:
        context = self._extract_last_json_block(prompt) or {}
        requirement = context.get("requirement", {})
        chunks = context.get("retrieved_chunks", [])
        requirement_id = int(requirement.get("id") or requirement.get("requirement_id") or 0)
        requirement_content = str(requirement.get("content") or "")
        decision_text = requirement_content or prompt
        source_chunks = self._source_chunks(chunks)

        if self._contains_any(decision_text, ["500", "高并发", "同时在线"]):
            response = BidResponseItem(
                requirement_id=requirement_id,
                match_status="partial",
                response_text=(
                    "当前标准版本支持 300 名并发用户。针对 500 名用户同时在线的要求，"
                    "建议通过集群扩容和性能压测确认最终容量。"
                ),
                risk_level="medium",
                source_chunks=source_chunks,
            )
        elif self._contains_any(decision_text, ["灾难恢复", "容灾", "disaster", "backup"]):
            response = BidResponseItem(
                requirement_id=requirement_id,
                match_status="partial",
                response_text=(
                    "平台支持定时数据备份；灾难恢复能力需要结合客户部署架构、RPO/RTO "
                    "目标和基础设施条件单独设计。"
                ),
                risk_level="medium",
                source_chunks=source_chunks,
            )
        elif self._contains_any(decision_text, ["权限", "rbac"]):
            response = BidResponseItem(
                requirement_id=requirement_id,
                match_status="satisfied",
                response_text="产品支持 RBAC 多角色权限模型，可配置角色、菜单权限和数据权限，满足多角色权限管理要求。",
                risk_level="low",
                source_chunks=source_chunks,
            )
        elif self._contains_any(decision_text, ["日志", "审计", "180"]):
            response = BidResponseItem(
                requirement_id=requirement_id,
                match_status="satisfied",
                response_text="平台提供操作日志审计能力，日志保存周期支持管理员自定义配置，可配置为不少于 180 天。",
                risk_level="low",
                source_chunks=source_chunks,
            )
        elif self._contains_any(decision_text, ["私有化", "内网", "docker", "kubernetes"]):
            response = BidResponseItem(
                requirement_id=requirement_id,
                match_status="satisfied",
                response_text="系统支持 Docker Compose 和 Kubernetes 私有化部署，适用于客户内网、专有云和混合云环境。",
                risk_level="low",
                source_chunks=source_chunks,
            )
        elif self._contains_any(decision_text, ["api", "第三方", "crm", "erp", "oa"]):
            response = BidResponseItem(
                requirement_id=requirement_id,
                match_status="satisfied",
                response_text="平台提供标准 REST API，可与 CRM、ERP、OA 等第三方系统集成。",
                risk_level="low",
                source_chunks=source_chunks,
            )
        elif self._contains_any(decision_text, ["加密", "https"]):
            response = BidResponseItem(
                requirement_id=requirement_id,
                match_status="satisfied",
                response_text="系统支持 HTTPS 加密传输和数据库敏感字段加密，满足数据加密传输要求。",
                risk_level="low",
                source_chunks=source_chunks,
            )
        elif self._contains_any(decision_text, ["培训", "上线", "售后"]):
            response = BidResponseItem(
                requirement_id=requirement_id,
                match_status="satisfied",
                response_text="公司提供实施培训、上线支持和售后服务，可覆盖项目上线阶段的服务要求。",
                risk_level="low",
                source_chunks=source_chunks,
            )
        else:
            response = BidResponseItem(
                requirement_id=requirement_id,
                match_status="partial",
                response_text="Mock Provider 未识别到明确需求类别，建议补充检索内容后再生成正式响应。",
                risk_level="medium",
                source_chunks=source_chunks,
            )

        return BidResponseGenerationResult(responses=[response]).model_dump_json()

    def _extract_last_json_block(self, prompt: str) -> dict[str, Any] | None:
        marker = "```json"
        start = prompt.rfind(marker)
        if start == -1:
            return None
        json_start = start + len(marker)
        json_end = prompt.find("```", json_start)
        if json_end == -1:
            return None
        try:
            parsed = json.loads(prompt[json_start:json_end].strip())
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _source_chunks(self, chunks: list[dict[str, Any]]) -> list[SourceChunkItem]:
        source_chunks: list[SourceChunkItem] = []
        for chunk in chunks[:3]:
            try:
                source_chunks.append(
                    SourceChunkItem(
                        chunk_id=int(chunk["chunk_id"]),
                        content=str(chunk["content"]),
                        score=float(chunk["score"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return source_chunks

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _extract_json_schema(self, prompt: str) -> dict[str, Any] | None:
        marker = "```json"
        start = prompt.find(marker)
        if start == -1:
            return None
        json_start = start + len(marker)
        json_end = prompt.find("```", json_start)
        if json_end == -1:
            return None
        try:
            return json.loads(prompt[json_start:json_end].strip())
        except json.JSONDecodeError:
            return None

    def _sample_for_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        properties = schema.get("properties", {})
        return {name: self._sample_value(field_schema) for name, field_schema in properties.items()}

    def _sample_value(self, schema: dict[str, Any]) -> Any:
        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]

        schema_type = schema.get("type")
        if schema_type == "string":
            return "mock_value"
        if schema_type == "integer":
            return 0
        if schema_type == "number":
            return 0.0
        if schema_type == "boolean":
            return True
        if schema_type == "array":
            return []
        if schema_type == "object":
            nested = schema.get("properties", {})
            return {name: self._sample_value(field_schema) for name, field_schema in nested.items()}

        return None
