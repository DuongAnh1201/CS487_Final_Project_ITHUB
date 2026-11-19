"""RPT entities: Report (abstract) with DailyReport and MonthlySummaryReport, plus templates."""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.exceptions import ConflictError, PermissionDeniedError, ValidationRuleError


class ReportStatus(str, enum.Enum):
    """Report life cycle (SP7): Draft -> Submitted -> Reviewed / Rejected / Passed."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    REVIEWED = "REVIEWED"
    REJECTED = "REJECTED"
    PASSED = "PASSED"


class ReviewOutcome(str, enum.Enum):
    """The statuses a reviewer may set (FR-RPT-04)."""

    REVIEWED = "REVIEWED"
    REJECTED = "REJECTED"
    PASSED = "PASSED"


class ReportTemplate(Base):
    """Reusable checklist for daily reports (FR-RPT-05)."""

    __tablename__ = "report_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    checklist_items: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    def create_report(self, author_id: int, shift: str, title: str | None, now: datetime) -> "DailyReport":
        """Factory method: a Draft DailyReport with this template's checklist pre-filled."""
        return DailyReport(
            title=title or f"{self.name} - {now.date().isoformat()}", description=self.description,
            author_id=author_id, status=ReportStatus.DRAFT, created_at=now, updated_at=now,
            template_id=self.id, shift=shift, checklist_answers={i: "" for i in self.checklist_items},
        )


class ReportReviewer(Base):
    """A user assigned to review a report."""

    __tablename__ = "report_reviewers"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class ReportStatusChange(Base):
    """One entry of a report's history (US-RPT-06): who changed the status, when, and why."""

    __tablename__ = "report_status_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), index=True)
    old_status: Mapped[ReportStatus | None] = mapped_column(Enum(ReportStatus), nullable=True)
    new_status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus))
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime)
    comment: Mapped[str] = mapped_column(Text, default="")


class Report(Base):
    """Abstract report: common data and the review workflow.

    ``render()`` is the Template Method; subclasses supply ``generate_content()``.
    """

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    task_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    reviewers: Mapped[list[ReportReviewer]] = relationship(
        order_by=ReportReviewer.id, cascade="all, delete-orphan")
    history: Mapped[list[ReportStatusChange]] = relationship(order_by=ReportStatusChange.id)

    __mapper_args__ = {"polymorphic_on": "report_type", "polymorphic_abstract": True}

    @property
    def reviewer_ids(self) -> list[int]:
        """Assigned reviewers."""
        return [r.user_id for r in self.reviewers]

    @property
    def content(self) -> str:
        """The report body (see ``generate_content``)."""
        return self.generate_content()

    def generate_content(self) -> str:
        """Subclass hook: the body text of the report."""
        raise NotImplementedError

    def render(self) -> str:
        """Template Method: common header, then the subclass body."""
        return f"{self.title} [{self.status.value}]\n{self.generate_content()}"

    def is_editable(self) -> bool:
        """Only drafts and reports sent back as Reviewed can be edited."""
        return self.status in (ReportStatus.DRAFT, ReportStatus.REVIEWED)

    def can_be_reviewed(self) -> bool:
        """Only a Submitted report is reviewed."""
        return self.status == ReportStatus.SUBMITTED

    def submit(self, reviewer_ids: list[int]) -> None:
        """Draft or Reviewed -> Submitted, needing at least one reviewer."""
        if self.status not in (ReportStatus.DRAFT, ReportStatus.REVIEWED):
            raise ConflictError("Only draft or reviewed reports can be submitted.")
        ids = list(dict.fromkeys(reviewer_ids)) or self.reviewer_ids
        if not ids:
            raise ValidationRuleError("At least one reviewer is required.")
        self.reviewers = [ReportReviewer(user_id=i) for i in ids]
        self.status = ReportStatus.SUBMITTED

    def review(self, outcome: ReviewOutcome, reviewer_id: int, comment: str) -> None:
        """Submitted -> Reviewed / Rejected / Passed by an assigned reviewer."""
        if not self.can_be_reviewed():
            raise ConflictError("Only submitted reports can be reviewed.")
        if reviewer_id not in self.reviewer_ids:
            raise PermissionDeniedError("Only an assigned reviewer can review this report.")
        if outcome != ReviewOutcome.PASSED and not comment.strip():
            raise ValidationRuleError("A comment is required.")
        self.status = ReportStatus(outcome.value)


class DailyReport(Report):
    """Shift report, optionally filled from a template checklist."""

    template_id: Mapped[int | None] = mapped_column(ForeignKey("report_templates.id"), nullable=True)
    shift: Mapped[str | None] = mapped_column(String(30), nullable=True)
    checklist_answers: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "DAILY"}

    def answer(self, item_name: str, value: str) -> None:
        """Answer one checklist item."""
        answers = dict(self.checklist_answers or {})
        answers[item_name] = value
        self.checklist_answers = answers

    def generate_content(self) -> str:
        """Description followed by the checklist answers."""
        lines = [self.description] if self.description else []
        lines += [f"- {item}: {value or '(not answered)'}"
                  for item, value in (self.checklist_answers or {}).items()]
        return "\n".join(lines)


class MonthlySummaryReport(Report):
    """System-generated summary of a month's reports and orders (FR-RPT-07)."""

    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary_data: Mapped[Any] = mapped_column(JSON, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "MONTHLY_SUMMARY"}

    def generate_content(self) -> str:
        """Counts of the month's reports and orders by status."""
        data = self.summary_data or {}
        def block(name: str, counts: dict[str, int]) -> str:
            rows = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "none"
            return f"{name} ({sum(counts.values())}): {rows}"
        return "\n".join([
            f"Summary for {self.year}-{self.month:02d}",
            block("Reports", data.get("reports_by_status", {})),
            block("Orders", data.get("orders_by_status", {})),
        ])
