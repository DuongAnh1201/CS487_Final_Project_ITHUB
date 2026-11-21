"""CLS entities and value rules (BR-18–20, DD-CLS-01/02)."""

from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    JSON,
    String,
    Time,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.exceptions import ConflictError, ValidationRuleError


class RoomType(str, Enum):
    """RoomType JSON contract or domain enumeration."""

    LECTURE = "LECTURE"
    COMPUTER_LAB = "COMPUTER_LAB"


class EquipmentCondition(str, Enum):
    """EquipmentCondition JSON contract or domain enumeration."""

    WORKING = "WORKING"
    FAULTY = "FAULTY"
    UNDER_REPAIR = "UNDER_REPAIR"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    MISSING = "MISSING"


class RoomStatus(str, Enum):
    """RoomStatus JSON contract or domain enumeration."""

    AVAILABLE = "AVAILABLE"
    LIMITED = "LIMITED"
    UNUSABLE = "UNUSABLE"
    CLOSED = "CLOSED"


class DayOfWeek(str, Enum):
    """DayOfWeek JSON contract or domain enumeration."""

    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class EntryStatus(str, Enum):
    """EntryStatus JSON contract or domain enumeration."""

    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


class EntrySource(str, Enum):
    """EntrySource JSON contract or domain enumeration."""

    IMPORT = "IMPORT"
    MANUAL = "MANUAL"


class Classroom(Base):
    """One retained classroom per AST Location (BR-18, US-CLS-01)."""

    __tablename__ = "classrooms"
    __table_args__ = (CheckConstraint("capacity > 0"), {"sqlite_autoincrement": True})
    id: Mapped[int] = mapped_column(primary_key=True)
    # AST owns locations; references are validated through AssetGateway, not SQL here.
    location_id: Mapped[int] = mapped_column(unique=True)
    capacity: Mapped[int]
    room_type: Mapped[RoomType] = mapped_column(SQLEnum(RoomType))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    closed_for_maintenance: Mapped[bool] = mapped_column(Boolean, default=False)
    closed_reason: Mapped[str] = mapped_column(default="")
    # Keep manual override independent of automatic issue closures.
    manual_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    manual_closed_reason: Mapped[str] = mapped_column(default="")
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    @property
    def classroom_id(self) -> str:
        return f"CLS-{self.id:04d}"

    def update(self, capacity: int, room_type: RoomType) -> None:
        """Update editable fields with a positive capacity."""
        if capacity <= 0:
            raise ValidationRuleError("Capacity must be greater than zero.")
        self.capacity, self.room_type = capacity, room_type

    def deactivate(self, has_equipment: bool, has_future_classes: bool) -> None:
        """Keep history; refuse deactivation while the room is in use (BR-18)."""
        if has_equipment:
            raise ConflictError("Remove the installed equipment first.")
        if has_future_classes:
            raise ConflictError("This classroom has future classes.")
        self.is_active = False

    def is_check_overdue(self, today: date, interval_days: int = 7) -> bool:
        """Never checked and checks older than seven days are overdue (BR-20)."""
        return (
            self.last_checked_at is None
            or (today - self.last_checked_at.date()).days > interval_days
        )


class RoomEquipment(Base):
    """Installation history and condition, separate from AST status (DD-CLS-01)."""

    __tablename__ = "room_equipment"
    __table_args__ = (
        Index(
            "uq_installed_item",
            "item_id",
            unique=True,
            # Partial index: one *current* installation per item; history rows stay (FR-CLS).
            sqlite_where=text("removed_at IS NULL"),
            postgresql_where=text("removed_at IS NULL"),
        ),
        {"sqlite_autoincrement": True},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), index=True)
    item_id: Mapped[int] = mapped_column(index=True)
    seat_label: Mapped[str] = mapped_column(default="")
    condition: Mapped[EquipmentCondition] = mapped_column(
        SQLEnum(EquipmentCondition), default=EquipmentCondition.WORKING
    )
    installed_at: Mapped[datetime] = mapped_column(DateTime)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    version: Mapped[int] = mapped_column(default=1)
    __mapper_args__ = {"version_id_col": version}

    def is_installed(self) -> bool:
        """Whether this installation is current."""
        return self.removed_at is None

    def set_condition(
        self, condition: EquipmentCondition, reason: str, user_id: int, at: datetime
    ) -> EquipmentCondition:
        """Require a reason and an actual change (FR-CLS-03/04)."""
        if not reason.strip():
            raise ValidationRuleError("Reason is required.")
        if condition == self.condition:
            raise ValidationRuleError("No change.")
        old = self.condition
        self.condition, self.updated_by, self.updated_at = condition, user_id, at
        return old

    def remove(self, user_id: int, at: datetime) -> None:
        """Close the installation without deleting it (US-CLS-02)."""
        self.removed_at, self.updated_at, self.updated_by = at, at, user_id


class RoomCheck(Base):
    """A retained room inspection with one result per installation (US-CLS-04)."""

    __tablename__ = "room_checks"
    __table_args__ = {"sqlite_autoincrement": True}
    id: Mapped[int] = mapped_column(primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"))
    checked_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    checked_at: Mapped[datetime] = mapped_column(DateTime)
    notes: Mapped[str]
    results: Mapped[list["RoomCheckResult"]] = relationship(lazy="selectin")


class RoomCheckResult(Base):
    """Observed equipment condition for a single check."""

    __tablename__ = "room_check_results"
    __table_args__ = {"sqlite_autoincrement": True}
    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[int] = mapped_column(ForeignKey("room_checks.id"))
    room_equipment_id: Mapped[int] = mapped_column(ForeignKey("room_equipment.id"))
    observed_condition: Mapped[EquipmentCondition] = mapped_column(
        SQLEnum(EquipmentCondition)
    )
    comment: Mapped[str]


class ScheduleImport(Base):
    """CSV import result including rejected row diagnostics (US-CLS-06)."""

    __tablename__ = "schedule_imports"
    __table_args__ = {"sqlite_autoincrement": True}
    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str]
    imported_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    imported_at: Mapped[datetime] = mapped_column(DateTime)
    rows_accepted: Mapped[int] = mapped_column(default=0)
    rows_rejected: Mapped[int] = mapped_column(default=0)
    rejected_rows: Mapped[list[dict]] = mapped_column(JSON, default=list)


class ScheduleEntry(Base):
    """Weekly class meeting; cancellation preserves history (BR-19)."""

    __tablename__ = "schedule_entries"
    __table_args__ = (
        CheckConstraint("end_time > start_time"),
        CheckConstraint("term_end >= term_start"),
        Index("ix_schedule_room_day_status", "classroom_id", "day_of_week", "status"),
        {"sqlite_autoincrement": True},
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"))
    course_code: Mapped[str]
    course_title: Mapped[str]
    instructor_name: Mapped[str]
    day_of_week: Mapped[DayOfWeek] = mapped_column(SQLEnum(DayOfWeek))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    term_start: Mapped[date] = mapped_column(Date)
    term_end: Mapped[date] = mapped_column(Date)
    status: Mapped[EntryStatus] = mapped_column(
        SQLEnum(EntryStatus), default=EntryStatus.ACTIVE
    )
    source: Mapped[EntrySource] = mapped_column(
        SQLEnum(EntrySource), default=EntrySource.MANUAL
    )
    import_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedule_imports.id"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    def validate(self) -> None:
        """Validate times, dates and mandatory course fields (BR-19)."""
        for field in ("course_code", "course_title", "instructor_name"):
            if not getattr(self, field).strip():
                raise ValidationRuleError(
                    f"{field.replace('_', ' ').capitalize()} is required."
                )
        if self.end_time <= self.start_time:
            raise ValidationRuleError("End time must be after the start time.")
        if self.term_end < self.term_start:
            raise ValidationRuleError("Term end must be on or after term start.")

    def overlaps(self, other: "ScheduleEntry") -> bool:
        """Compare active weekly ranges, allowing adjoining time slots (BR-19)."""
        return (
            self.status == other.status == EntryStatus.ACTIVE
            and self.classroom_id == other.classroom_id
            and self.day_of_week == other.day_of_week
            and self.term_start <= other.term_end
            and other.term_start <= self.term_end
            and self.start_time < other.end_time
            and other.start_time < self.end_time
        )

    def occurs_on(self, day: date, include_cancelled: bool = False) -> bool:
        """Whether this meeting occurs on the given calendar date (cancelled ones only on request)."""
        return (
            (include_cancelled or self.status == EntryStatus.ACTIVE)
            and self.term_start <= day <= self.term_end
            and list(DayOfWeek)[day.weekday()] == self.day_of_week
        )

    def cancel(self) -> None:
        """Retain an entry and exclude it from future timetables."""
        self.status = EntryStatus.CANCELLED
