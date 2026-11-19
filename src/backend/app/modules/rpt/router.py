"""RPT routes: /reports, /report-templates, /audit. Admins and SAs have the same access (BR-RPT-02)."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.database import get_db
from app.core.deps import get_audit_log, get_clock, get_current_user, get_event_publisher
from app.modules.ord.repository import OrderRepository
from app.modules.rpt.models import Report, ReportStatus, ReportStatusChange, ReportTemplate
from app.modules.rpt.repository import ReportRepository, ReportTemplateRepository
from app.modules.rpt.schemas import (
    AnswersUpdate,
    AuditRead,
    MonthlySummaryRequest,
    ProjectGroup,
    ReportCreate,
    ReportRead,
    ReportUpdate,
    ReviewRequest,
    StatusChangeRead,
    SubmitRequest,
    TemplateRead,
    TemplateWrite,
)
from app.modules.rpt.service import ReportManager, SummaryGenerator
from app.modules.usr.models import User
from app.modules.usr.repository import UserRepository
from app.shared.audit import AuditLog, AuditRecord
from app.shared.events import EventPublisher

reports_router = APIRouter(prefix="/reports", tags=["reports"])
templates_router = APIRouter(prefix="/report-templates", tags=["report-templates"])
audit_router = APIRouter(prefix="/audit", tags=["audit"])


def get_report_manager(
    db: Session = Depends(get_db), audit: AuditLog = Depends(get_audit_log),
    publisher: EventPublisher = Depends(get_event_publisher), clock: Clock = Depends(get_clock),
) -> ReportManager:
    """ReportManager for the request."""
    return ReportManager(ReportRepository(db), ReportTemplateRepository(db), UserRepository(db),
                         audit, publisher, clock)


def get_summary_generator(
    db: Session = Depends(get_db), audit: AuditLog = Depends(get_audit_log),
    publisher: EventPublisher = Depends(get_event_publisher), clock: Clock = Depends(get_clock),
) -> SummaryGenerator:
    """SummaryGenerator for the request."""
    return SummaryGenerator(ReportRepository(db), OrderRepository(db), UserRepository(db),
                            audit, publisher, clock)


# ---- reports ---------------------------------------------------------------

@reports_router.post("", response_model=ReportRead, status_code=201)
def create_report(body: ReportCreate, user: User = Depends(get_current_user),
                  manager: ReportManager = Depends(get_report_manager)) -> Report:
    """Create a draft report, optionally from a template (FR-RPT-01)."""
    return manager.create_report(user, body)


@reports_router.get("", response_model=list[ReportRead])
def search_reports(
    q: str | None = None, status: ReportStatus | None = None, project_id: int | None = None,
    author_id: int | None = None, date_from: date | None = None, date_to: date | None = None,
    report_type: str | None = None, user: User = Depends(get_current_user),
    manager: ReportManager = Depends(get_report_manager),
) -> list[Report]:
    """Search by id or keyword; filter by status, project, author, type and date (FR-RPT-08)."""
    return manager.search_reports(q=q, status=status, project_id=project_id, author_id=author_id,
                                  date_from=date_from, date_to=date_to, report_type=report_type)


@reports_router.get("/by-project", response_model=list[ProjectGroup])
def reports_by_project(user: User = Depends(get_current_user),
                       manager: ReportManager = Depends(get_report_manager)) -> list[ProjectGroup]:
    """Reports grouped by project; unlinked reports are the last group (FR-RPT-02)."""
    return [ProjectGroup(project_id=pid, reports=[ReportRead.model_validate(r) for r in reports])
            for pid, reports in manager.group_by_project()]


@reports_router.post("/monthly-summary", response_model=ReportRead, status_code=201)
def generate_monthly_summary(body: MonthlySummaryRequest, user: User = Depends(get_current_user),
                             generator: SummaryGenerator = Depends(get_summary_generator)) -> Report:
    """Generate the monthly summary; only at or after the end of the month (BR-RPT-01)."""
    return generator.generate_monthly_summary(user, body.month, body.year)


@reports_router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: int, user: User = Depends(get_current_user),
               manager: ReportManager = Depends(get_report_manager)) -> Report:
    """One report."""
    return manager.find_report(report_id)


@reports_router.patch("/{report_id}", response_model=ReportRead)
def update_report(report_id: int, body: ReportUpdate, user: User = Depends(get_current_user),
                  manager: ReportManager = Depends(get_report_manager)) -> Report:
    """Edit a draft report."""
    return manager.update_report(user, report_id, body)


@reports_router.put("/{report_id}/answers", response_model=ReportRead)
def answer_checklist(report_id: int, body: AnswersUpdate, user: User = Depends(get_current_user),
                     manager: ReportManager = Depends(get_report_manager)) -> Report:
    """Fill in a daily report's checklist."""
    return manager.answer_checklist(user, report_id, body.answers)


@reports_router.post("/{report_id}/submit", response_model=ReportRead)
def submit_report(report_id: int, body: SubmitRequest, user: User = Depends(get_current_user),
                  manager: ReportManager = Depends(get_report_manager)) -> Report:
    """Submit (or resubmit) for review; the reviewers are notified (FR-RPT-03)."""
    return manager.submit_report(user, report_id, body.reviewer_ids)


@reports_router.post("/{report_id}/review", response_model=ReportRead)
def review_report(report_id: int, body: ReviewRequest, user: User = Depends(get_current_user),
                  manager: ReportManager = Depends(get_report_manager)) -> Report:
    """Set Reviewed, Rejected or Passed (FR-RPT-04)."""
    return manager.review_report(user, report_id, body.status, body.comment)


@reports_router.get("/{report_id}/history", response_model=list[StatusChangeRead])
def report_history(report_id: int, user: User = Depends(get_current_user),
                   manager: ReportManager = Depends(get_report_manager)) -> list[ReportStatusChange]:
    """Status history: who changed it, when and why (US-RPT-06)."""
    return manager.history(report_id)


# ---- templates -------------------------------------------------------------

@templates_router.post("", response_model=TemplateRead, status_code=201)
def create_template(body: TemplateWrite, user: User = Depends(get_current_user),
                    manager: ReportManager = Depends(get_report_manager)) -> ReportTemplate:
    """Create a daily-report template."""
    return manager.create_template(user, body)


@templates_router.get("", response_model=list[TemplateRead])
def list_templates(user: User = Depends(get_current_user),
                   manager: ReportManager = Depends(get_report_manager)) -> list[ReportTemplate]:
    """List templates."""
    return manager.list_templates()


@templates_router.get("/{template_id}", response_model=TemplateRead)
def get_template(template_id: int, user: User = Depends(get_current_user),
                 manager: ReportManager = Depends(get_report_manager)) -> ReportTemplate:
    """One template."""
    return manager.get_template(template_id)


@templates_router.put("/{template_id}", response_model=TemplateRead)
def update_template(template_id: int, body: TemplateWrite, user: User = Depends(get_current_user),
                    manager: ReportManager = Depends(get_report_manager)) -> ReportTemplate:
    """Replace a template."""
    return manager.update_template(user, template_id, body)


# ---- audit log (read-only: records are never edited or removed, BR-RPT-03) ------------

@audit_router.get("", response_model=list[AuditRead])
def search_audit(
    user_id: int | None = None, entity_type: str | None = None, entity_id: str | None = None,
    action: str | None = None, date_from: date | None = None, date_to: date | None = None,
    limit: int = 100, offset: int = 0, user: User = Depends(get_current_user),
    audit: AuditLog = Depends(get_audit_log),
) -> list[AuditRecord]:
    """Search and filter audit records, newest first (FR-RPT-08, UC-RPT-04)."""
    return audit.search(user_id, entity_type, entity_id, action, date_from, date_to,
                        min(max(limit, 1), 500), max(offset, 0))


@audit_router.get("/{record_id}", response_model=AuditRead)
def get_audit_record(record_id: int, user: User = Depends(get_current_user),
                     audit: AuditLog = Depends(get_audit_log)) -> AuditRecord:
    """One audit record by its unique id (FR-RPT-09)."""
    return audit.get(record_id)
