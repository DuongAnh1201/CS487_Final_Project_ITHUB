"""CLS persistence; SQL stays inside repositories (NFR-CLS-03)."""

from sqlalchemy import select
from sqlalchemy.orm.exc import StaleDataError
from app.core.exceptions import ConflictError
from app.shared.repository import BaseRepository
from app.modules.cls.models import (
    Classroom,
    RoomEquipment,
    RoomCheck,
    ScheduleEntry,
    ScheduleImport,
)

CONCURRENT = "This record was changed by someone else. Reload and try again."


class ClassroomRepository(BaseRepository[Classroom]):
    """Classroom aggregate storage (BR-18)."""

    model = Classroom
    not_found_message = "Classroom not found."

    def find_by_location(self, location_id: int) -> Classroom | None:
        """Find even inactive classrooms, preserving location uniqueness."""
        return self.session.scalar(
            select(Classroom).where(Classroom.location_id == location_id)
        )


class RoomEquipmentRepository(BaseRepository[RoomEquipment]):
    """Current installations and retained installation history."""

    model = RoomEquipment
    not_found_message = "Equipment not found."

    def find_installed_by_item(self, item_id: int) -> RoomEquipment | None:
        """Locate an item's active installation."""
        return self.session.scalar(
            select(RoomEquipment).where(
                RoomEquipment.item_id == item_id, RoomEquipment.removed_at.is_(None)
            )
        )

    def find_all_for_item(self, item_id: int) -> list[RoomEquipment]:
        """Every installation record of an item, current and past."""
        return list(
            self.session.scalars(
                select(RoomEquipment)
                .where(RoomEquipment.item_id == item_id)
                .order_by(RoomEquipment.id)
            )
        )

    def find_installed_by_classroom(self, classroom_id: int) -> list[RoomEquipment]:
        """Load current equipment in a room."""
        return list(
            self.session.scalars(
                select(RoomEquipment)
                .where(
                    RoomEquipment.classroom_id == classroom_id,
                    RoomEquipment.removed_at.is_(None),
                )
                .order_by(RoomEquipment.id)
            )
        )

    def flush(self) -> None:
        """Translate optimistic locking failures to the documented conflict."""
        try:
            super().flush()
        except StaleDataError as exc:
            raise ConflictError(CONCURRENT) from exc


class RoomCheckRepository(BaseRepository[RoomCheck]):
    """Append room-check aggregates."""

    model = RoomCheck


class ScheduleRepository(BaseRepository[ScheduleEntry]):
    """Persist weekly meetings and import summaries."""

    model = ScheduleEntry
    not_found_message = "Schedule entry not found."

    def for_classroom(self, classroom_id: int) -> list[ScheduleEntry]:
        """Load room schedule history."""
        return list(
            self.session.scalars(
                select(ScheduleEntry).where(ScheduleEntry.classroom_id == classroom_id)
            )
        )


class ScheduleImportRepository(BaseRepository[ScheduleImport]):
    """Append import results."""

    model = ScheduleImport
    not_found_message = "Schedule import not found."
