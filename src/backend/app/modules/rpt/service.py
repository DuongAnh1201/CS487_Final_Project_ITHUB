"""RPT business rules: ReportManager and SummaryGenerator (US-RPT-01..06, FR-RPT-07)."""

import calendar
from collections import Counter
from datetime import date

from app.core.clock import Clock
from app.core.exceptions import ConflictError, NotFoundError, ValidationRuleError
from app.modules.ord.repository import OrderRepository
from app.modules.rpt.models import (
    DailyReport,
    MonthlySummaryReport,
    Report,
    ReportReviewer,
    ReportStatus,
    ReportStatusChange,
    ReportTemplate,
    ReviewOutcome,
)
from app.modules.rpt.repository import ReportRepository, ReportTemplateRepository
from app.modules.rpt.schemas import ReportCreate, ReportUpdate, TemplateWrite
from app.modules.usr.models import Role, User, UserStatus
from app.modules.usr.repository import UserRepository
from app.shared.audit import AuditLog
from app.shared.events import DomainEvent, EventPublisher, EventType

MSG_NOT_EDITABLE = "Submitted reports cannot be edited."
MSG_TITLE = "Title is required."
MSG_MONTH_END = "The monthly summary can only be generated at the end of the month."
MSG_SUMMARY_EXISTS = "The monthly summary for this month already exists."
MSG_BAD_REVIEWER = "Reviewer must be an active user."
MORNING_CHECKLIST = ("Morning checklist", "Daily morning classroom and equipment check.", [
    "Classroom computers powered on", "Projectors and displays working",
    "Network and Wi-Fi working", "Printers stocked", "Issues found"])


class _Base:
    """Shared dependencies and helpers."""

    def __init__(self, reports: ReportRepository, users: UserRepository, audit: AuditLog,
                 publisher: EventPublisher, clock: Clock) -> None:
        self.reports = reports
        self.users = users
        self.audit = audit
        self.publisher = publisher
        self.clock = clock

    def _active_user(self, user_id: int, message: str = MSG_BAD_REVIEWER) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError(self.users.not_found_message)
        if user.status != UserStatus.ACTIVE:
            raise ValidationRuleError(message)
        return user

    def _record_change(self, report: Report, old: ReportStatus | None, actor_id: int | None,
                       comment: str = "") -> None:
        """History row (US-RPT-06) for a new status."""
        self.reports.add_change(ReportStatusChange(
            report_id=report.id, old_status=old, new_status=report.status,
            changed_by=actor_id, changed_at=self.clock(), comment=comment))


class ReportManager(_Base):
    """Create, edit, submit, review, search and group reports; manage templates."""

    def __init__(self, reports: ReportRepository, templates: ReportTemplateRepository,
                 users: UserRepository, audit: AuditLog, publisher: EventPublisher,
                 clock: Clock) -> None:
        super().__init__(reports, users, audit, publisher, clock)
        self.templates = templates

    # ---- reports ----

    def create_report(self, user: User, data: ReportCreate) -> DailyReport:
        """A Draft daily report, optionally from a template (FR-RPT-01, FR-RPT-05)."""
        now = self.clock()
        if data.template_id is not None:
            template = self.templates.get_or_raise(data.template_id)
            report = template.create_report(user.id, data.shift or "", data.title, now)
            if data.description:
                report.description = data.description
        else:
            if not (data.title and data.title.strip()):
                raise ValidationRuleError(MSG_TITLE)
            report = DailyReport(
                title=data.title.strip(), description=data.description, author_id=user.id,
                status=ReportStatus.DRAFT, created_at=now, updated_at=now,
                shift=data.shift, checklist_answers={})
        report.project_id, report.task_id = data.project_id, data.task_id
        self.reports.add(report)
        self._record_change(report, None, user.id)
        self.audit.record(user, "CREATE", "Report", report.id, None, self._snapshot(report))
        return report

    def update_report(self, user: User, report_id: int, data: ReportUpdate) -> Report:
        """Edit title, description or links while the report is editable."""
        report = self._editable(report_id)
        old = self._snapshot(report)
        for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(report, field, value.strip() if field == "title" else value)
        self._touch(user, report, old)
        return report

    def answer_checklist(self, user: User, report_id: int, answers: dict[str, str]) -> Report:
        """Fill in checklist answers of a daily report."""
        report = self._editable(report_id)
        if not isinstance(report, DailyReport):
            raise ConflictError("Only daily reports have a checklist.")
        unknown = [k for k in answers if report.checklist_answers and k not in report.checklist_answers]
        if unknown:
            raise ValidationRuleError(f"Unknown checklist item: {unknown[0]}.")
        old = self._snapshot(report)
        for item, value in answers.items():
            report.answer(item, value)
        self._touch(user, report, old)
        return report

    def submit_report(self, user: User, report_id: int, reviewer_ids: list[int]) -> Report:
        """Draft / Reviewed -> Submitted and notify the reviewers (FR-RPT-03)."""
        report = self.reports.get_or_raise(report_id)
        reviewers = [self._active_user(i) for i in dict.fromkeys(reviewer_ids)]
        old_status = report.status
        report.submit([u.id for u in reviewers])
        report.submitted_at = report.updated_at = self.clock()
        self.reports.flush()
        self._record_change(report, old_status, user.id)
        self.audit.record(user, "SUBMIT", "Report", report.id, {"status": old_status.value},
                          {"status": report.status.value, "reviewer_ids": report.reviewer_ids})
        self.publisher.publish(DomainEvent(
            EventType.REPORT_SUBMITTED, f"Report #{report.id} '{report.title}' was submitted for review.",
            actor_id=user.id, recipient_ids=tuple(report.reviewer_ids),
            related_type="Report", related_id=report.id))
        return report

    def review_report(self, user: User, report_id: int, outcome: ReviewOutcome,
                      comment: str = "") -> Report:
        """Reviewer sets Reviewed / Rejected / Passed and the author is told (FR-RPT-04)."""
        report = self.reports.get_or_raise(report_id)
        old_status = report.status
        report.review(outcome, user.id, comment)
        report.updated_at = self.clock()
        self.reports.flush()
        self._record_change(report, old_status, user.id, comment.strip())
        self.audit.record(user, "REVIEW", "Report", report.id, {"status": old_status.value},
                          {"status": report.status.value, "comment": comment.strip()})
        if report.author_id is not None:
            self.publisher.publish(DomainEvent(
                EventType.REPORT_REVIEWED, f"Report #{report.id} is now {report.status.value}.",
                actor_id=user.id, recipient_ids=(report.author_id,),
                related_type="Report", related_id=report.id))
        return report

    def find_report(self, report_id: int) -> Report:
        """One report by its unique id."""
        return self.reports.get_or_raise(report_id)

    def history(self, report_id: int) -> list[ReportStatusChange]:
        """Status changes of a report, oldest first (US-RPT-06)."""
        return list(self.reports.get_or_raise(report_id).history)

    def search_reports(self, **filters) -> list[Report]:
        """Search by id or keyword and filter by status, project, author, date (FR-RPT-08)."""
        return self.reports.search(**filters)

    def group_by_project(self) -> list[tuple[int | None, list[Report]]]:
        """Reports grouped by project; unlinked reports form the last group (FR-RPT-02)."""
        groups: dict[int | None, list[Report]] = {}
        for report in self.reports.search():
            groups.setdefault(report.project_id, []).append(report)
        linked = sorted((k, v) for k, v in groups.items() if k is not None)
        return linked + ([(None, groups[None])] if None in groups else [])

    # ---- templates ----

    def create_template(self, user: User, data: TemplateWrite) -> ReportTemplate:
        """A new daily-report template."""
        if self.templates.get_by_name(data.name.strip()):
            raise ConflictError("A template with this name already exists.")
        now = self.clock()
        template = self.templates.add(ReportTemplate(
            name=data.name.strip(), description=data.description,
            checklist_items=list(data.checklist_items), created_by=user.id,
            created_at=now, updated_at=now))
        self.audit.record(user, "CREATE", "ReportTemplate", template.id, None,
                          {"name": template.name, "checklist_items": template.checklist_items})
        return template

    def update_template(self, user: User, template_id: int, data: TemplateWrite) -> ReportTemplate:
        """Replace a template; reports already created from it are unchanged."""
        template = self.templates.get_or_raise(template_id)
        clash = self.templates.get_by_name(data.name.strip())
        if clash is not None and clash.id != template.id:
            raise ConflictError("A template with this name already exists.")
        old = {"name": template.name, "checklist_items": template.checklist_items}
        template.name, template.description = data.name.strip(), data.description
        template.checklist_items = list(data.checklist_items)
        template.updated_at = self.clock()
        self.templates.flush()
        self.audit.record(user, "UPDATE", "ReportTemplate", template.id, old,
                          {"name": template.name, "checklist_items": template.checklist_items})
        return template

    def get_template(self, template_id: int) -> ReportTemplate:
        """One template."""
        return self.templates.get_or_raise(template_id)

    def list_templates(self) -> list[ReportTemplate]:
        """All templates."""
        return self.templates.list()

    def seed_default_templates(self) -> None:
        """Provide the common Morning checklist when no template exists (US-RPT-05)."""
        if not self.templates.list():
            name, description, items = MORNING_CHECKLIST
            now = self.clock()
            self.templates.add(ReportTemplate(
                name=name, description=description, checklist_items=items,
                created_at=now, updated_at=now))

    # ---- internals ----

    def _editable(self, report_id: int) -> Report:
        report = self.reports.get_or_raise(report_id)
        if not report.is_editable():
            raise ConflictError(MSG_NOT_EDITABLE)
        return report

    def _touch(self, user: User, report: Report, old: dict) -> None:
        report.updated_at = self.clock()
        self.reports.flush()
        self.audit.record(user, "UPDATE", "Report", report.id, old, self._snapshot(report))

    @staticmethod
    def _snapshot(report: Report) -> dict:
        data = {"title": report.title, "description": report.description,
                "status": report.status.value, "project_id": report.project_id,
                "task_id": report.task_id}
        if isinstance(report, DailyReport):
            data["checklist_answers"] = dict(report.checklist_answers or {})
        return data


class SummaryGenerator(_Base):
    """Builds the monthly summary of reports and orders (FR-RPT-07, BR-RPT-01)."""

    def __init__(self, reports: ReportRepository, orders: OrderRepository, users: UserRepository,
                 audit: AuditLog, publisher: EventPublisher, clock: Clock) -> None:
        super().__init__(reports, users, audit, publisher, clock)
        self.orders = orders

    @staticmethod
    def is_month_end(day: date) -> bool:
        """True on the last day of a month."""
        return day.day == calendar.monthrange(day.year, day.month)[1]

    def generate_monthly_summary(self, user: User | None, month: int, year: int) -> MonthlySummaryReport:
        """Create the summary once the month has ended, and tell the Admins.

        Allowed on the last day of the month or later. The summary is a Submitted report
        whose reviewers are the active Admins.
        """
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        today = self.clock().date()
        if today < last_day:
            raise ValidationRuleError(MSG_MONTH_END)
        if self.reports.get_summary(month, year) is not None:
            raise ConflictError(MSG_SUMMARY_EXISTS)
        admins = self.users.search(Role.ADMIN, UserStatus.ACTIVE)
        now = self.clock()
        summary = MonthlySummaryReport(
            title=f"Monthly summary {year}-{month:02d}", description="", author_id=None,
            status=ReportStatus.SUBMITTED, created_at=now, submitted_at=now, updated_at=now,
            month=month, year=year, summary_data={
                "reports_by_status": dict(Counter(r.status.value for r in self.reports.for_month(month, year))),
                "orders_by_status": dict(Counter(o.status.value for o in self.orders.for_month(month, year))),
            })
        summary.reviewers = [ReportReviewer(user_id=a.id) for a in admins]
        self.reports.add(summary)
        self._record_change(summary, None, user.id if user else None)
        self.audit.record(user, "CREATE", "Report", summary.id, None,
                          {"title": summary.title, "type": "MONTHLY_SUMMARY"})
        self.publisher.publish(DomainEvent(
            EventType.MONTHLY_SUMMARY, f"{summary.title} is ready.\n{summary.generate_content()}",
            actor_id=user.id if user else None, related_type="Report", related_id=summary.id))
        return summary
