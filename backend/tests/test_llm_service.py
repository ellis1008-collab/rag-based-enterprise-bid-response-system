import asyncio

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.llm.schemas import RequirementExtractionResult
from app.llm.service import LLMService
from app.models import LLMCallLog


class DemoOutput(BaseModel):
    title: str
    count: int


def test_llm_service_falls_back_to_mock_and_logs_call(db_session: Session) -> None:
    result = asyncio.run(LLMService(db_session).invoke_text("Hello", prompt_type="unit_text"))

    assert result.provider == "mock"
    assert result.model_name == "mock-model"
    assert result.content == "Mock response from BidPilot AI."

    log = db_session.scalar(select(LLMCallLog))
    assert log is not None
    assert log.provider == "mock"
    assert log.model_name == "mock-model"
    assert log.prompt_type == "unit_text"
    assert log.success is True


def test_llm_service_invoke_json_validates_with_pydantic(db_session: Session) -> None:
    result = asyncio.run(
        LLMService(db_session).invoke_json(
            "Return demo output.",
            DemoOutput,
            prompt_type="unit_json",
        )
    )

    assert isinstance(result, DemoOutput)
    assert result.title == "mock_value"
    assert result.count == 0

    log = db_session.scalar(select(LLMCallLog).where(LLMCallLog.prompt_type == "unit_json"))
    assert log is not None
    assert log.success is True


def test_llm_service_passes_business_prompt_type_to_mock(db_session: Session) -> None:
    result = asyncio.run(
        LLMService(db_session).invoke_json(
            "Extract requirements from sample RFP.",
            RequirementExtractionResult,
            prompt_type="extract_requirements",
        )
    )

    assert len(result.requirements) == 8
    assert result.requirements[0].requirement_code == "REQ-001"
