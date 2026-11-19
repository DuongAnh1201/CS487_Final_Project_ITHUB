"""RPT request and response models."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.rpt.models import ReportStatus, ReviewOutcome


class ReportCreate(BaseModel):
    """New report (US-RPT-01); ``template_id`` pre-fills a daily checklist (US-RPT-05)."""

    title: str | None = Field(default=None, max_length=200)
    description: str = ""
    template_id: int | None = None
    shift: str | None = Field(default=None, max_length=30)
    project_id: int | None = None
    task_id: int | None = None


class ReportUpdate(BaseModel):
    """Edit a draft."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    project_id: int | None = None
    task_id: int | None = None


class AnswersUpdate(BaseModel):
    """Checklist answers for a daily report."""

    answers: dict[str, str]


class SubmitRequest(BaseModel):
    """Reviewers for a submission; may be empty when resubmitting."""

    reviewer_ids: list[int] = []


class ReviewRequest(BaseModel):
    """A reviewer's decision (US-RPT-04)."""

    status: ReviewOutcome
    comment: str = ""


class MonthlySummaryRequest(BaseModel):
    """Month to summarise (BR-RPT-01)."""

    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)


class ReportRead(BaseModel):
    """A report, whichever subclass it is."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: str
    title: str
    description: str
    author_id: int | None
    project_id: int | None
    task_id: int | None
    status: ReportStatus
    reviewer_ids: list[int]
    created_at: datetime
    submitted_at: datetime | None
    updated_at: datetime
    content: str
    template_id: int | None = None
    shift: str | None = None
    checklist_answers: dict[str, str] | None = None
    month: int | None = None
    year: int | None = None


class ProjectGroup(BaseModel):
    """Reports of one project; ``project_id`` None groups unlinked reports (US-RPT-02)."""

    project_id: int | None
    reports: list[ReportRead]


class StatusChangeRead(BaseModel):
    """One history entry (US-RPT-06)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    old_status: ReportStatus | None
    new_status: ReportStatus
    changed_by: int | None
    changed_at: datetime
    comment: str


class TemplateWrite(BaseModel):
    """Create or replace a report template."""

    name: str = Field(min_length=1, max_length=150)
    description: str = ""
    checklist_items: list[str] = Field(min_length=1)


class TemplateRead(TemplateWrite):
    """A stored template."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AuditRead(BaseModel):
    """An audit record (FR-RPT-06/09)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: str
    old_value: Any
    new_value: Any
    status: str
