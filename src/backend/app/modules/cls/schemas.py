"""Validated JSON contracts for CLS (US-CLS-01–08)."""

from datetime import date, datetime, time
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.cls.models import (
    DayOfWeek,
    EntrySource,
    EntryStatus,
    EquipmentCondition,
    RoomStatus,
    RoomType,
)


class ReadModel(BaseModel):
    """ReadModel JSON contract or domain enumeration."""

    model_config = ConfigDict(from_attributes=True)


class ClassroomCreate(BaseModel):
    """ClassroomCreate JSON contract or domain enumeration."""

    location_id: int = Field(gt=0)
    capacity: int = Field(gt=0)
    room_type: RoomType


class ClassroomUpdate(BaseModel):
    """ClassroomUpdate JSON contract or domain enumeration."""

    capacity: int = Field(gt=0)
    room_type: RoomType


class ClassroomRead(ReadModel):
    """ClassroomRead JSON contract or domain enumeration."""

    id: int
    classroom_id: str
    location_id: int
    capacity: int
    room_type: RoomType
    is_active: bool
    closed_for_maintenance: bool
    closed_reason: str
    last_checked_at: datetime | None


class ClassroomSummary(ClassroomRead):
    """ClassroomSummary JSON contract or domain enumeration."""

    building: str
    room: str
    status: RoomStatus
    check_overdue: bool


class ClosureUpdate(BaseModel):
    """ClosureUpdate JSON contract or domain enumeration."""

    closed: bool
    reason: str = Field(default="", max_length=2000)


class EquipmentCreate(BaseModel):
    """EquipmentCreate JSON contract or domain enumeration."""

    item_id: int = Field(gt=0)
    seat_label: str = Field(default="", max_length=80)


class EquipmentRead(ReadModel):
    """EquipmentRead JSON contract or domain enumeration."""

    id: int
    classroom_id: int
    item_id: int
    seat_label: str
    condition: EquipmentCondition
    installed_at: datetime
    removed_at: datetime | None
    updated_by: int
    updated_at: datetime
    version: int


class ConditionUpdate(BaseModel):
    """ConditionUpdate JSON contract or domain enumeration."""

    condition: EquipmentCondition
    reason: str = Field(max_length=2000)
    version: int = Field(gt=0)


class EquipmentMove(BaseModel):
    """EquipmentMove JSON contract or domain enumeration."""

    to_classroom_id: int = Field(gt=0)
    version: int = Field(gt=0)


class VersionRequest(BaseModel):
    """VersionRequest JSON contract or domain enumeration."""

    version: int = Field(gt=0)


class CheckResultCreate(BaseModel):
    """CheckResultCreate JSON contract or domain enumeration."""

    room_equipment_id: int = Field(gt=0)
    observed_condition: EquipmentCondition
    comment: str = Field(default="", max_length=2000)
    version: int = Field(gt=0)


class RoomCheckCreate(BaseModel):
    """RoomCheckCreate JSON contract or domain enumeration."""

    notes: str = Field(default="", max_length=4000)
    results: list[CheckResultCreate]


class CheckResultRead(ReadModel):
    """CheckResultRead JSON contract or domain enumeration."""

    id: int
    room_equipment_id: int
    observed_condition: EquipmentCondition
    comment: str


class RoomCheckRead(ReadModel):
    """RoomCheckRead JSON contract or domain enumeration."""

    id: int
    classroom_id: int
    checked_by: int
    checked_at: datetime
    notes: str
    results: list[CheckResultRead]


class ScheduleCreate(BaseModel):
    """ScheduleCreate JSON contract or domain enumeration."""

    classroom_id: int = Field(gt=0)
    course_code: str = Field(min_length=1, max_length=80)
    course_title: str = Field(min_length=1, max_length=250)
    instructor_name: str = Field(min_length=1, max_length=200)
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    term_start: date
    term_end: date

    @field_validator("course_code", "course_title", "instructor_name")
    @classmethod
    def required_text(cls, value: str) -> str:
        """Reject whitespace-only course information."""
        if not value.strip():
            raise ValueError("Field is required.")
        return value.strip()

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def local_time(cls, value: Any) -> Any:
        """Registrar and API times are local 24-hour HH:MM."""
        if isinstance(value, str):
            import re

            if not re.fullmatch(r"\d{2}:\d{2}", value):
                raise ValueError("Invalid time – use HH:MM.")
        if isinstance(value, time) and (
            value.tzinfo is not None or value.second or value.microsecond
        ):
            raise ValueError("Invalid time – use HH:MM.")
        return value

    @model_validator(mode="after")
    def valid_ranges(self) -> Self:
        """Reject invalid class and term intervals (BR-19)."""
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after the start time.")
        if self.term_end < self.term_start:
            raise ValueError("Term end must be on or after term start.")
        return self


class ScheduleRead(ScheduleCreate, ReadModel):
    """ScheduleRead JSON contract or domain enumeration."""

    id: int
    status: EntryStatus
    source: EntrySource
    import_id: int | None
    created_by: int
    created_at: datetime


class CsvImportCreate(BaseModel):
    """CsvImportCreate JSON contract or domain enumeration."""

    file_name: str = Field(min_length=1, max_length=255)
    content: str = Field(max_length=5_000_000)


class RejectedRow(BaseModel):
    """RejectedRow JSON contract or domain enumeration."""

    row: int
    reason: str


class ScheduleImportRead(ReadModel):
    """ScheduleImportRead JSON contract or domain enumeration."""

    id: int
    file_name: str
    imported_by: int
    imported_at: datetime
    rows_accepted: int
    rows_rejected: int
    rejected_rows: list[RejectedRow]


class TimetableDay(BaseModel):
    """TimetableDay JSON contract or domain enumeration."""

    day: date
    entries: list[ScheduleRead]
    message: str | None = None


class Timetable(BaseModel):
    """Timetable JSON contract or domain enumeration."""

    classroom_id: int
    days: list[TimetableDay]


class ClassroomSearch(BaseModel):
    """ClassroomSearch JSON contract or domain enumeration."""

    building: str | None = None
    room_type: RoomType | None = None
    min_capacity: int | None = Field(default=None, ge=0)
    status: RoomStatus | None = None
    slot_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None

    @model_validator(mode="after")
    def complete_slot(self) -> Self:
        """A free-slot filter requires all three parts (US-CLS-05)."""
        values = (self.slot_date, self.start_time, self.end_time)
        if any(v is not None for v in values):
            if not all(v is not None for v in values):
                raise ValueError("Free slot requires date, start time and end time.")
            if self.end_time <= self.start_time:
                raise ValueError("End time must be after the start time.")
            if self.start_time.tzinfo or self.end_time.tzinfo:
                raise ValueError("Invalid time – use HH:MM.")
        return self
