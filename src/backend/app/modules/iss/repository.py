"""ISS SQL and optimistic locking (FR-ISS-04/08/09)."""

from datetime import datetime, time
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import StaleDataError
from app.core.exceptions import ConflictError
from app.modules.cls.models import RoomEquipment
from app.modules.cls.repository import CONCURRENT
from app.modules.iss.models import Issue, IssueCategory, Severity, UNRESOLVED
from app.modules.iss.schemas import IssueSearch
from app.shared.repository import BaseRepository


class IssueRepository(BaseRepository[Issue]):
    """Issue aggregate storage; no deletion or historical update operations."""

    model = Issue
    not_found_message = "Issue not found."

    def flush(self) -> None:
        """Expose the documented stale-record conflict."""
        try:
            super().flush()
        except StaleDataError as exc:
            raise ConflictError(CONCURRENT) from exc

    def unresolved_for_equipment(self, equipment_id: int, exclude_id: int) -> int:
        """Count other active problems on the same item across installations (FR-ISS-09)."""
        return (
            self.session.scalar(
                select(func.count())
                .select_from(Issue)
                .where(
                    Issue.room_equipment_id.in_(
                        select(RoomEquipment.id).where(
                            RoomEquipment.item_id
                            == select(RoomEquipment.item_id)
                            .where(RoomEquipment.id == equipment_id)
                            .scalar_subquery()
                        )
                    ),
                    Issue.id != exclude_id,
                    Issue.status.in_(UNRESOLVED),
                )
            )
            or 0
        )

    def has_critical_room_issue(self, classroom_id: int) -> bool:
        """Critical room issues keep a room closed until all are resolved."""
        return bool(
            self.session.scalar(
                select(func.count())
                .select_from(Issue)
                .where(
                    Issue.classroom_id == classroom_id,
                    Issue.room_equipment_id.is_(None),
                    Issue.severity == Severity.CRITICAL,
                    Issue.status.in_(UNRESOLVED),
                )
            )
        )

    def count_duplicates(self, original_id: int) -> int:
        """Count reports linked to the canonical original (FR-ISS-08)."""
        return (
            self.session.scalar(
                select(func.count())
                .select_from(Issue)
                .where(Issue.duplicate_of_id == original_id)
            )
            or 0
        )

    def possible_duplicates(
        self, classroom_id: int, equipment_id: int | None, category: IssueCategory
    ) -> list[Issue]:
        """Find unresolved reports on the same item or room/category."""
        query = select(Issue).where(Issue.status.in_(UNRESOLVED))
        if equipment_id is not None:
            query = query.where(
                Issue.room_equipment_id.in_(
                    select(RoomEquipment.id).where(
                        RoomEquipment.item_id
                        == select(RoomEquipment.item_id)
                        .where(RoomEquipment.id == equipment_id)
                        .scalar_subquery()
                    )
                )
            )
        else:
            query = query.where(
                Issue.classroom_id == classroom_id, Issue.category == category
            )
        return list(
            self.session.scalars(
                query.order_by(Issue.created_at.desc(), Issue.id.desc())
            )
        )

    def search(self, criteria: IssueSearch) -> tuple[list[Issue], int]:
        """Filter in SQL and page at most fifty issues (NFR-ISS-02)."""
        query = select(Issue)
        for field in ("status", "classroom_id", "category", "severity"):
            value = getattr(criteria, field)
            if value is not None:
                query = query.where(getattr(Issue, field) == value)
        if criteria.item_id is not None:
            query = query.join(
                RoomEquipment, Issue.room_equipment_id == RoomEquipment.id
            ).where(RoomEquipment.item_id == criteria.item_id)
        if criteria.date_from:
            query = query.where(
                Issue.created_at >= datetime.combine(criteria.date_from, time.min)
            )
        if criteria.date_to:
            query = query.where(
                Issue.created_at <= datetime.combine(criteria.date_to, time.max)
            )
        total = (
            self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        )
        query = (
            query.options(selectinload(Issue.history))
            .order_by(Issue.created_at.desc(), Issue.id.desc())
            .offset((criteria.page - 1) * criteria.page_size)
            .limit(criteria.page_size)
        )
        return list(self.session.scalars(query)), total
