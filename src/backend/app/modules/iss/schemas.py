"""ISS request/response contracts (US-ISS-01–07)."""

from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from typing import Self
from app.modules.cls.schemas import ReadModel
from app.modules.cls.models import EquipmentCondition
from app.modules.iss.models import IssueCategory, IssueStatus, ReporterType, Severity


class IssueCreate(BaseModel):
    """IssueCreate JSON contract or domain enumeration."""

    classroom_id: int = Field(gt=0)
    room_equipment_id: int | None = Field(default=None, gt=0)
    category: IssueCategory
    severity: Severity
    description: str = Field(max_length=10000)
    reporter_name: str = Field(max_length=200)
    reporter_type: ReporterType
    reporter_contact: str = Field(default="", max_length=250)

    @field_validator("description", "reporter_name")
    @classmethod
    def required_text(cls, value: str, info: ValidationInfo) -> str:
        """Name required fields in validation errors (NFR-ISS-03)."""
        if not value.strip():
            raise ValueError(
                f"{info.field_name.replace('_', ' ').capitalize()} is required."
            )
        return value.strip()


class IssueRead(ReadModel):
    """IssueRead JSON contract or domain enumeration."""

    id: int
    issue_id: str
    classroom_id: int
    room_equipment_id: int | None
    category: IssueCategory
    severity: Severity
    description: str
    status: IssueStatus
    reporter_name: str
    reporter_type: ReporterType
    reporter_contact: str
    created_by: int
    created_at: datetime
    assigned_to: int | None
    target_date: date
    resolution_notes: str
    resolved_by: int | None
    resolved_at: datetime | None
    duplicate_of_id: int | None
    is_repeat_problem: bool
    version: int


class IssueSummary(IssueRead):
    """IssueSummary JSON contract or domain enumeration."""

    is_overdue: bool
    allowed_next_statuses: list[IssueStatus]


class IssueUpdateRead(ReadModel):
    """IssueUpdateRead JSON contract or domain enumeration."""

    id: int
    issue_id: int
    user_id: int
    timestamp: datetime
    old_status: IssueStatus | None
    new_status: IssueStatus | None
    comment: str


class StatusChange(BaseModel):
    """StatusChange JSON contract or domain enumeration."""

    status: IssueStatus
    version: int = Field(gt=0)
    note: str = Field(default="", max_length=10000)
    assignee_id: int | None = Field(default=None, gt=0)
    original_id: int | None = Field(default=None, gt=0)
    new_condition: EquipmentCondition = EquipmentCondition.WORKING


class IssueResolve(BaseModel):
    """IssueResolve JSON contract or domain enumeration."""

    notes: str = Field(max_length=10000)
    new_condition: EquipmentCondition = EquipmentCondition.WORKING
    version: int = Field(gt=0)


class IssueDuplicate(BaseModel):
    """IssueDuplicate JSON contract or domain enumeration."""

    original_id: int = Field(gt=0)
    version: int = Field(gt=0)


class IssueComment(BaseModel):
    """IssueComment JSON contract or domain enumeration."""

    text: str = Field(max_length=10000)
    version: int = Field(gt=0)


class IssueSearch(BaseModel):
    """IssueSearch JSON contract or domain enumeration."""

    status: IssueStatus | None = None
    classroom_id: int | None = Field(default=None, gt=0)
    item_id: int | None = Field(default=None, gt=0)
    category: IssueCategory | None = None
    severity: Severity | None = None
    date_from: date | None = None
    date_to: date | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=50)

    @model_validator(mode="after")
    def valid_dates(self) -> Self:
        """Reject reversed date filters."""
        if self.date_from and self.date_to and self.date_to < self.date_from:
            raise ValueError("End date must be on or after start date.")
        return self


class IssuePage(BaseModel):
    """IssuePage JSON contract or domain enumeration."""

    items: list[IssueSummary]
    total: int
    page: int
    page_size: int
    message: str | None = None
