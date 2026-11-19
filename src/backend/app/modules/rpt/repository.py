"""RPT storage."""

from datetime import date, datetime, time, timedelta

from sqlalchemy import or_, select

from app.modules.rpt.models import (
    MonthlySummaryReport,
    Report,
    ReportStatus,
    ReportStatusChange,
    ReportTemplate,
)
from app.shared.repository import BaseRepository


class ReportRepository(BaseRepository[Report]):
    """Reports and their status history."""

    model = Report
    not_found_message = "Report not found."

    def search(self, q: str | None = None, status: ReportStatus | None = None,
               project_id: int | None = None, author_id: int | None = None,
               date_from: date | None = None, date_to: date | None = None,
               report_type: str | None = None) -> list[Report]:
        """Reports matching an id or keyword and every given filter (FR-RPT-08)."""
        stmt = select(Report).order_by(Report.id)
        if q:
            text = q.strip()
            like = f"%{text}%"
            conditions = [Report.title.ilike(like), Report.description.ilike(like)]
            if text.isdigit():
                conditions.append(Report.id == int(text))
            stmt = stmt.where(or_(*conditions))
        if status is not None:
            stmt = stmt.where(Report.status == status)
        if project_id is not None:
            stmt = stmt.where(Report.project_id == project_id)
        if author_id is not None:
            stmt = stmt.where(Report.author_id == author_id)
        if report_type:
            stmt = stmt.where(Report.report_type == report_type.upper())
        if date_from is not None:
            stmt = stmt.where(Report.created_at >= datetime.combine(date_from, time.min))
        if date_to is not None:
            stmt = stmt.where(Report.created_at < datetime.combine(date_to + timedelta(days=1), time.min))
        return list(self.session.scalars(stmt))

    def for_month(self, month: int, year: int) -> list[Report]:
        """Reports created in the month, excluding monthly summaries."""
        start = datetime(year, month, 1)
        end = datetime(year + (month == 12), month % 12 + 1, 1)
        return [r for r in self.search() if start <= r.created_at < end
                and r.report_type != "MONTHLY_SUMMARY"]

    def get_summary(self, month: int, year: int) -> MonthlySummaryReport | None:
        """The monthly summary for the month, if one exists."""
        return self.session.scalar(select(MonthlySummaryReport).where(
            MonthlySummaryReport.month == month, MonthlySummaryReport.year == year))

    def add_change(self, change: ReportStatusChange) -> ReportStatusChange:
        """Store a history row."""
        self.session.add(change)
        self.session.flush()
        return change


class ReportTemplateRepository(BaseRepository[ReportTemplate]):
    """Report templates."""

    model = ReportTemplate
    not_found_message = "Template not found."

    def get_by_name(self, name: str) -> ReportTemplate | None:
        """Find a template by its unique name."""
        return self.session.scalar(select(ReportTemplate).where(ReportTemplate.name == name))
