"""NTF request and response models."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.ntf.models import EmailStatus
from app.modules.ntf.service import ShiftName
from app.shared.events import EventType


class NotificationRead(BaseModel):
    """A notification as shown in the in-app list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_id: int
    event_type: EventType
    message: str
    related_type: str | None
    related_id: int | None
    project_id: int | None
    created_at: datetime
    read_at: datetime | None
    is_read: bool
    email_status: EmailStatus


class ReadStateUpdate(BaseModel):
    """Read or unread (FR-NTF-05)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"read": True}]})

    read: bool


class ShiftSummaryRequest(BaseModel):
    """Roster and shift to summarise (FR-NTF-03)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"shift": "MORNING", "shift_date": "2026-01-05", "user_ids": [2, 3]}]})

    shift: ShiftName
    shift_date: date
    user_ids: list[int] = Field(min_length=1)
