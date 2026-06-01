from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.timestamps import utc_now


class RfpProject(Base):
    __tablename__ = "rfp_projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    documents: Mapped[list["RfpDocument"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    requirements: Mapped[list["RfpRequirement"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    responses: Mapped[list["BidResponse"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class RfpDocument(Base):
    __tablename__ = "rfp_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("rfp_projects.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    project: Mapped[RfpProject] = relationship(back_populates="documents")


class RfpRequirement(Base):
    __tablename__ = "rfp_requirements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("rfp_projects.id"), index=True, nullable=False)
    requirement_code: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    source_page: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    project: Mapped[RfpProject] = relationship(back_populates="requirements")
    responses: Mapped[list["BidResponse"]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan",
    )


class BidResponse(Base):
    __tablename__ = "bid_responses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("rfp_projects.id"), index=True, nullable=False)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("rfp_requirements.id"), index=True, nullable=False)
    match_status: Mapped[str] = mapped_column(String(50), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    source_chunks_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    human_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    human_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    project: Mapped[RfpProject] = relationship(back_populates="responses")
    requirement: Mapped[RfpRequirement] = relationship(back_populates="responses")
