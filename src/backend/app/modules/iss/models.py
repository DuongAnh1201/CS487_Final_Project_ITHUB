"""Issue aggregate, immutable history and state machine (BR-21–23)."""

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Enum as SQLEnum, ForeignKey, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.exceptions import PermissionDeniedError, ValidationRuleError
from app.modules.usr.models import Role, User


class IssueCategory(str, Enum):
    """IssueCategory JSON contract or domain enumeration."""

    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    NETWORK = "NETWORK"
    ROOM_FACILITY = "ROOM_FACILITY"
    OTHER = "OTHER"


class Severity(str, Enum):
    """Severity JSON contract or domain enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    def target_days(self) -> int:
        """Severity resolution targets (BR-22)."""
        return {self.LOW: 14, self.MEDIUM: 7, self.HIGH: 3, self.CRITICAL: 1}[self]


class IssueStatus(str, Enum):
    """IssueStatus JSON contract or domain enumeration."""

    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    DUPLICATE = "DUPLICATE"
    REJECTED = "REJECTED"


class ReporterType(str, Enum):
    """ReporterType JSON contract or domain enumeration."""

    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    STAFF = "STAFF"


TRANSITIONS = {
    IssueStatus.OPEN: (
        IssueStatus.ASSIGNED,
        IssueStatus.REJECTED,
        IssueStatus.DUPLICATE,
    ),
    IssueStatus.ASSIGNED: (
        IssueStatus.IN_PROGRESS,
        IssueStatus.REJECTED,
        IssueStatus.DUPLICATE,
    ),
    IssueStatus.IN_PROGRESS: (IssueStatus.RESOLVED,),
    IssueStatus.RESOLVED: (IssueStatus.IN_PROGRESS, IssueStatus.CLOSED),
}
ADMIN_STATUSES = (IssueStatus.ASSIGNED, IssueStatus.REJECTED, IssueStatus.CLOSED)
UNRESOLVED = (IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS)


class Issue(Base):
    """Reported classroom problem; changes pass through its state machine (BR-23)."""

    __tablename__ = "issues"
    __table_args__ = {"sqlite_autoincrement": True}
    id: Mapped[int] = mapped_column(primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), index=True)
    room_equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("room_equipment.id"), index=True, nullable=True
    )
    category: Mapped[IssueCategory] = mapped_column(SQLEnum(IssueCategory))
    severity: Mapped[Severity] = mapped_column(SQLEnum(Severity))
    description: Mapped[str]
    status: Mapped[IssueStatus] = mapped_column(SQLEnum(IssueStatus), index=True)
    reporter_name: Mapped[str]
    reporter_type: Mapped[ReporterType] = mapped_column(SQLEnum(ReporterType))
    reporter_contact: Mapped[str] = mapped_column(default="")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    target_date: Mapped[date] = mapped_column(Date)
    resolution_notes: Mapped[str] = mapped_column(default="")
    resolved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duplicate_of_id: Mapped[int | None] = mapped_column(
        ForeignKey("issues.id"), nullable=True, index=True
    )
    is_repeat_problem: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(default=1)
    __mapper_args__ = {"version_id_col": version}
    history: Mapped[list["IssueUpdate"]] = relationship(
        foreign_keys="IssueUpdate.issue_id", lazy="selectin", order_by="IssueUpdate.id"
    )

    @property
    def issue_id(self) -> str:
        return f"ISS-{self.id:05d}"

    @staticmethod
    def create(data: dict, user: User, now: datetime) -> "Issue":
        """Build an OPEN issue and calculate its due date (FR-ISS-01–03)."""
        for field in ("description", "reporter_name"):
            if not data[field].strip():
                raise ValidationRuleError(
                    f"{field.replace('_', ' ').capitalize()} is required."
                )
        return Issue(
            **data,
            status=IssueStatus.OPEN,
            created_by=user.id,
            created_at=now,
            target_date=now.date() + timedelta(days=data["severity"].target_days()),
            history=[  # the first timeline entry is the report itself
                IssueUpdate(
                    user_id=user.id,
                    timestamp=now,
                    old_status=None,
                    new_status=IssueStatus.OPEN,
                    comment="Reported",
                )
            ],
        )

    def allowed_next_statuses(self, user: User) -> list[IssueStatus]:
        """Offer only legal role-specific transitions (US-ISS-03)."""
        return [
            s
            for s in TRANSITIONS.get(self.status, ())
            if user.role == Role.ADMIN or s not in ADMIN_STATUSES
        ]

    def change_status(
        self,
        status: IssueStatus,
        user: User,
        now: datetime,
        comment: str = "",
        assignee_id: int | None = None,
        original_id: int | None = None,
    ) -> None:
        """Validate every transition and append its immutable history (BR-23)."""
        if status not in TRANSITIONS.get(self.status, ()):
            raise ValidationRuleError("This status change is not allowed.")
        if status in ADMIN_STATUSES and user.role != Role.ADMIN:
            raise PermissionDeniedError("Not allowed for your role.")
        if status == IssueStatus.ASSIGNED:
            if assignee_id is None:
                raise ValidationRuleError("Assignee is required.")
            self.assigned_to = assignee_id
        if status == IssueStatus.RESOLVED:
            if not comment.strip():
                raise ValidationRuleError("Resolution notes are required.")
            self.resolution_notes, self.resolved_by, self.resolved_at = (
                comment.strip(),
                user.id,
                now,
            )
        if status == IssueStatus.REJECTED and not comment.strip():
            raise ValidationRuleError("Give a reason for rejecting this issue.")
        if status == IssueStatus.DUPLICATE:
            if original_id is None or original_id == self.id:
                raise ValidationRuleError("Choose the original issue.")
            self.duplicate_of_id = original_id
        old = self.status
        self.status = status
        self.history.append(
            IssueUpdate(
                user_id=user.id,
                timestamp=now,
                old_status=old,
                new_status=status,
                comment=comment.strip(),
            )
        )

    def add_comment(self, text: str, user: User, now: datetime) -> None:
        """Append progress notes only while the issue is nonfinal (FR-ISS-06)."""
        if self.is_final():
            raise ValidationRuleError("This issue is closed. Comments are not allowed.")
        if not text.strip():
            raise ValidationRuleError("Comment cannot be empty.")
        self.history.append(
            IssueUpdate(
                user_id=user.id,
                timestamp=now,
                old_status=None,
                new_status=None,
                comment=text.strip(),
            )
        )

    def is_final(self) -> bool:
        """Final statuses admit neither transitions nor comments (BR-23)."""
        return self.status in (
            IssueStatus.CLOSED,
            IssueStatus.REJECTED,
            IssueStatus.DUPLICATE,
        )

    def is_unresolved(self) -> bool:
        """Whether other issues must preserve faulty equipment."""
        return self.status in UNRESOLVED

    def is_overdue(self, today: date) -> bool:
        """Only unresolved issues can be overdue (BR-22)."""
        return self.is_unresolved() and today > self.target_date


class IssueUpdate(Base):
    """Append-only issue timeline (FR-ISS-10, NFR-ISS-04)."""

    __tablename__ = "issue_updates"
    __table_args__ = {"sqlite_autoincrement": True}
    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    old_status: Mapped[IssueStatus | None] = mapped_column(
        SQLEnum(IssueStatus), nullable=True
    )
    new_status: Mapped[IssueStatus | None] = mapped_column(
        SQLEnum(IssueStatus), nullable=True
    )
    comment: Mapped[str]


@event.listens_for(IssueUpdate, "before_update")
@event.listens_for(IssueUpdate, "before_delete")
def protect_history(mapper: Any, connection: Any, target: IssueUpdate) -> None:
    """Refuse ORM mutations to saved issue history (NFR-ISS-04)."""
    raise ValidationRuleError("Issue history cannot be changed.")
