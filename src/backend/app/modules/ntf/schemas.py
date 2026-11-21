"""NTF request and response models."""

from datetime import date, datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
    email_attempts: int


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


class EmailConfigRead(BaseModel):
    """Email setup as the Admin sees it (never the API key)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "enabled": True, "provider": "resend",
        "from_address": "IT Inventory Tracker <noreply@example.edu>", "webhook_enabled": True}]})

    enabled: bool
    provider: Literal["resend", "log"]
    from_address: str | None
    webhook_enabled: bool


class EmailTestRequest(BaseModel):
    """Who receives the test email (default: the Admin)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"to": "admin@sfbu.edu"}]})

    to: EmailStr | None = None


class EmailTestResult(BaseModel):
    """Outcome of the test email."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "SENT", "message_id": "49a3999c-0ce1-4ea6"}]})

    status: EmailStatus
    message_id: str | None


class EmailDeliveryRead(BaseModel):
    """One row of the email delivery log."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_id: int
    event_type: EventType
    email_status: EmailStatus
    attempts: int = Field(validation_alias="email_attempts")
    error: str | None = Field(validation_alias="email_error")
    sent_at: datetime | None = Field(validation_alias="email_sent_at")
    created_at: datetime


class WebhookAck(BaseModel):
    """Webhook receipt."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"received": True}]})

    received: bool = True


class EmailTemplateRead(BaseModel):
    """A designed email: its event, template file and a sample subject (#108)."""

    event_type: EventType
    template: str
    subject: str
