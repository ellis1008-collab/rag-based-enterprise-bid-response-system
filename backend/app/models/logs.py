from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.rfp import RfpProject
from app.models.timestamps import utc_now


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("rfp_projects.id"), index=True, nullable=False)
    run_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    steps_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[RfpProject] = relationship(back_populates="agent_runs")


class LLMCallLog(Base):
    __tablename__ = "llm_call_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_type: Mapped[str] = mapped_column(String(100), nullable=False)
    latency_ms: Mapped[int] = mapped_column(nullable=False)
    success: Mapped[bool] = mapped_column(nullable=False, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
