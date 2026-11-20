"""CLS managers, calculator and polymorphic filters (US-CLS-01–08)."""

import csv
import io
from abc import ABC, abstractmethod
from datetime import date, time, timedelta
from typing import Any
from collections.abc import Callable

from pydantic import ValidationError
from app.core.clock import Clock
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationRuleError,
)
from app.modules.usr.models import Role, User
from app.shared.audit import AuditLog
from app.modules.cls.integrations import AssetGateway
from app.modules.cls.models import (
    Classroom,
    DayOfWeek,
    EntrySource,
    EntryStatus,
    EquipmentCondition,
    RoomCheck,
    RoomCheckResult,
    RoomEquipment,
    RoomStatus,
    RoomType,
    ScheduleEntry,
    ScheduleImport,
)
from app.modules.cls.repository import (
    CONCURRENT,
    ClassroomRepository,
    RoomCheckRepository,
    RoomEquipmentRepository,
    ScheduleImportRepository,
    ScheduleRepository,
)
from app.modules.cls.schemas import (
    ClassroomCreate,
    ClassroomRead,
    ClassroomSearch,
    ClassroomSummary,
    ClassroomUpdate,
    EquipmentHistoryRead,
    RoomCheckCreate,
    ScheduleCreate,
    ScheduleRead,
    Timetable,
    TimetableDay,
)


def require_admin(user: User) -> None:
    """Apply Admin-only business permissions (SP4 §11.3)."""
    if user.role != Role.ADMIN:
        raise PermissionDeniedError("Not allowed for your role.")


def check_version(entity: Any, version: int) -> None:
    """Refuse stale browser edits before changing equipment or issues."""
    if entity.version != version:
        raise ConflictError(CONCURRENT)


class RoomStatusCalculator:
    """Calculate status from active Desktop installations only (DD-CLS-02)."""

    def calculate(
        self, classroom: Classroom, equipment: list[RoomEquipment], assets: AssetGateway
    ) -> RoomStatus:
        """Manual/issue closure overrides the working-PC proportion."""
        if classroom.closed_for_maintenance:
            return RoomStatus.CLOSED
        pcs = [
            e
            for e in equipment
            if e.is_installed()
            and assets.find_item(e.item_id).category.upper() == "DESKTOP"
            and assets.find_item(e.item_id).status.upper() != "RETIRED"
        ]
        working = sum(e.condition == EquipmentCondition.WORKING for e in pcs)
        if not pcs or working == len(pcs):
            return RoomStatus.AVAILABLE
        return RoomStatus.LIMITED if working else RoomStatus.UNUSABLE


class ClassroomFilter(ABC):
    """One search predicate, combined with AND (US-CLS-05)."""

    @abstractmethod
    def matches(self, summary: ClassroomSummary) -> bool: ...


class BuildingFilter(ClassroomFilter):
    """Match an AST building name, ignoring case."""

    def __init__(self, building: str) -> None:
        self.building = building

    def matches(self, summary: ClassroomSummary) -> bool:
        """Test the room's building."""
        return summary.building.casefold() == self.building.casefold()


class RoomTypeFilter(ClassroomFilter):
    """Match a classroom's room type."""

    def __init__(self, room_type: RoomType) -> None:
        self.room_type = room_type

    def matches(self, summary: ClassroomSummary) -> bool:
        """Test the room type."""
        return summary.room_type == self.room_type


class MinCapacityFilter(ClassroomFilter):
    """Match rooms with enough seats."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity

    def matches(self, summary: ClassroomSummary) -> bool:
        """Test the minimum capacity."""
        return summary.capacity >= self.capacity


class StatusFilter(ClassroomFilter):
    """Match the equipment-derived room status."""

    def __init__(self, status: RoomStatus) -> None:
        self.status = status

    def matches(self, summary: ClassroomSummary) -> bool:
        """Test the calculated status."""
        return summary.status == self.status


class FreeSlotFilter(ClassroomFilter):
    """Match rooms whose timetable leaves the requested slot free."""

    def __init__(
        self, schedules: "ScheduleManager", day: date, start: time, end: time
    ) -> None:
        self.schedules, self.day, self.start, self.end = schedules, day, start, end

    def matches(self, summary: ClassroomSummary) -> bool:
        """Test the dated free slot."""
        return self.schedules.is_room_free(summary.id, self.day, self.start, self.end)


class ScheduleManager:
    """Manage imports, manual meetings, and free-slot/timetable queries (BR-19)."""

    HEADER = [
        "course_code",
        "course_title",
        "instructor",
        "building",
        "room",
        "day",
        "start_time",
        "end_time",
        "term_start",
        "term_end",
    ]

    def __init__(
        self,
        repository: ScheduleRepository,
        imports: ScheduleImportRepository,
        classrooms: ClassroomRepository,
        assets: AssetGateway,
        audit: AuditLog,
        clock: Clock,
    ) -> None:
        self.repository, self.imports, self.classrooms = repository, imports, classrooms
        self.assets, self.audit, self.clock = assets, audit, clock

    def active_room(self, classroom_id: int) -> Classroom:
        """Ensure writes target an active room."""
        room = self.classrooms.get_or_raise(classroom_id)
        if not room.is_active:
            raise ValidationRuleError("Classroom is inactive.")
        return room

    def _validate_entry(
        self, entry: ScheduleEntry, exclude_id: int | None = None
    ) -> None:
        entry.validate()
        self.active_room(entry.classroom_id)
        for other in self.repository.for_classroom(entry.classroom_id):
            if other.id != exclude_id and entry.overlaps(other):
                raise ConflictError(
                    f"Overlaps {other.course_code} on {other.day_of_week.value} {other.start_time:%H:%M}–{other.end_time:%H:%M}."
                )

    def add_entry(
        self, data: ScheduleCreate, user: User, import_id: int | None = None
    ) -> ScheduleEntry:
        """Create an audited nonoverlapping meeting (FR-CLS-07)."""
        require_admin(user)
        now = self.clock()
        entry = ScheduleEntry(
            **data.model_dump(),
            status=EntryStatus.ACTIVE,
            source=EntrySource.IMPORT if import_id else EntrySource.MANUAL,
            import_id=import_id,
            created_by=user.id,
            created_at=now,
            updated_by=user.id,
            updated_at=now,
        )
        self._validate_entry(entry)
        self.repository.add(entry)
        self.audit.record(
            user,
            "CREATE",
            "ScheduleEntry",
            entry.id,
            None,
            ScheduleRead.model_validate(entry).model_dump(mode="json"),
        )
        return entry

    def edit_entry(
        self, entry_id: int, data: ScheduleCreate, user: User
    ) -> ScheduleEntry:
        """Validate edits before mutating an existing meeting (US-CLS-07)."""
        require_admin(user)
        entry = self.repository.get_or_raise(entry_id)
        if entry.status != EntryStatus.ACTIVE:
            raise ConflictError("Cancelled schedule entries cannot be edited.")
        candidate = ScheduleEntry(**data.model_dump(), status=EntryStatus.ACTIVE)
        self._validate_entry(candidate, entry.id)
        old = ScheduleRead.model_validate(entry).model_dump(mode="json")
        for key, value in data.model_dump().items():
            setattr(entry, key, value)
        entry.updated_by, entry.updated_at = user.id, self.clock()
        self.repository.flush()
        self.audit.record(
            user,
            "UPDATE",
            "ScheduleEntry",
            entry.id,
            old,
            ScheduleRead.model_validate(entry).model_dump(mode="json"),
        )
        return entry

    def cancel_entry(self, entry_id: int, user: User) -> ScheduleEntry:
        """Cancel instead of deleting a meeting (BR-02/19)."""
        require_admin(user)
        entry = self.repository.get_or_raise(entry_id)
        if entry.status == EntryStatus.CANCELLED:
            raise ValidationRuleError("No change.")
        entry.cancel()
        entry.updated_by, entry.updated_at = user.id, self.clock()
        self.repository.flush()
        self.audit.record(
            user,
            "CANCEL",
            "ScheduleEntry",
            entry.id,
            {"status": "ACTIVE"},
            {"status": "CANCELLED"},
        )
        return entry

    def import_csv(self, file_name: str, content: str, user: User) -> ScheduleImport:
        """Accept valid CSV rows, retaining row-level errors (FR-CLS-06)."""
        require_admin(user)
        reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")), strict=True)
        if not file_name.lower().endswith(".csv") or reader.fieldnames != self.HEADER:
            raise ValidationRuleError("File must be a CSV with the expected columns.")
        result = self.imports.add(
            ScheduleImport(
                file_name=file_name,
                imported_by=user.id,
                imported_at=self.clock(),
                rows_accepted=0,
                rows_rejected=0,
                rejected_rows=[],
            )
        )
        errors = []
        try:
            for row in reader:
                number = reader.line_num
                try:
                    if None in row or any(value is None for value in row.values()):
                        raise ValidationRuleError(
                            "File must be a CSV with the expected columns."
                        )
                    location = self.assets.find_location_by_room(
                        row["building"].strip(), row["room"].strip()
                    )
                    classroom = (
                        self.classrooms.find_by_location(location.id)
                        if location
                        else None
                    )
                    if classroom is None:
                        raise ValidationRuleError(
                            f"Row {number}: room {row['building']} {row['room']} not found."
                        )
                    day = row["day"].strip().upper()
                    full_days = dict(
                        zip(
                            (
                                "MONDAY",
                                "TUESDAY",
                                "WEDNESDAY",
                                "THURSDAY",
                                "FRIDAY",
                                "SATURDAY",
                                "SUNDAY",
                            ),
                            DayOfWeek,
                        )
                    )
                    day = full_days.get(day, day)
                    data = ScheduleCreate(
                        classroom_id=classroom.id,
                        course_code=row["course_code"],
                        course_title=row["course_title"],
                        instructor_name=row["instructor"],
                        day_of_week=day,
                        start_time=row["start_time"],
                        end_time=row["end_time"],
                        term_start=row["term_start"],
                        term_end=row["term_end"],
                    )
                    self._validate_entry(
                        ScheduleEntry(**data.model_dump(), status=EntryStatus.ACTIVE)
                    )
                except (
                    ValidationError,
                    ValidationRuleError,
                    ConflictError,
                    NotFoundError,
                ) as exc:
                    message = (
                        exc.errors()[0]["msg"]
                        if isinstance(exc, ValidationError)
                        else str(exc)
                    )
                    errors.append({"row": number, "reason": message})
                    continue
                # Storage/audit failures must escape: never call a persisted row rejected.
                self.add_entry(data, user, result.id)
                result.rows_accepted += 1
        except csv.Error as exc:
            raise ValidationRuleError(
                "File must be a CSV with the expected columns."
            ) from exc
        result.rows_rejected, result.rejected_rows = len(errors), errors
        self.imports.flush()
        self.audit.record(
            user,
            "IMPORT",
            "ScheduleImport",
            result.id,
            None,
            {
                "rows_accepted": result.rows_accepted,
                "rows_rejected": result.rows_rejected,
                "rejected_rows": errors,
            },
        )
        return result

    def get_timetable(
        self,
        classroom_id: int,
        day: date,
        view: str = "day",
        include_cancelled: bool = False,
    ) -> Timetable:
        """Return ordered day/week meetings; cancelled ones only when asked (US-CLS-08)."""
        self.classrooms.get_or_raise(classroom_id)
        if view not in ("day", "week"):
            raise ValidationRuleError("View must be day or week.")
        first = day if view == "day" else day - timedelta(days=day.weekday())
        entries = self.repository.for_classroom(classroom_id)
        days = []
        for offset in range(1 if view == "day" else 7):
            current = first + timedelta(days=offset)
            matches = sorted(
                (entry for entry in entries if entry.occurs_on(current, include_cancelled)),
                key=lambda entry: entry.start_time,
            )
            days.append(
                TimetableDay(
                    day=current,
                    entries=[ScheduleRead.model_validate(e) for e in matches],
                    message=None if matches else "No classes scheduled.",
                )
            )
        return Timetable(classroom_id=classroom_id, days=days)

    def is_room_free(
        self, classroom_id: int, day: date, start: time, end: time
    ) -> bool:
        """Check a dated slot using actual meetings, not only term ranges."""
        return not any(
            e.occurs_on(day) and e.start_time < end and start < e.end_time
            for e in self.repository.for_classroom(classroom_id)
        )

    def has_future_classes(self, classroom_id: int, today: date) -> bool:
        """Conservatively protect active terms ending today or later (SP4 §9.11)."""
        return any(
            e.status == EntryStatus.ACTIVE and e.term_end >= today
            for e in self.repository.for_classroom(classroom_id)
        )


class ClassroomManager:
    """Own room setup, equipment history, checks and search (BR-18/20)."""

    def __init__(
        self,
        repository: ClassroomRepository,
        equipment: RoomEquipmentRepository,
        checks: RoomCheckRepository,
        schedules: ScheduleManager,
        assets: AssetGateway,
        audit: AuditLog,
        clock: Clock,
        critical_issue_lookup: Callable[[int], bool],
    ) -> None:
        self.critical_issue_lookup = critical_issue_lookup
        self.repository, self.equipment, self.checks, self.schedules = (
            repository,
            equipment,
            checks,
            schedules,
        )
        self.assets, self.audit, self.clock = assets, audit, clock
        self.calculator = RoomStatusCalculator()

    def add_classroom(self, data: ClassroomCreate, user: User) -> Classroom:
        """Create exactly one classroom per AST location (US-CLS-01)."""
        require_admin(user)
        self.assets.find_location(data.location_id)
        if self.repository.find_by_location(data.location_id):
            raise ConflictError("This room already exists as a classroom.")
        now = self.clock()
        room = Classroom(
            **data.model_dump(),
            created_by=user.id,
            created_at=now,
            updated_by=user.id,
            updated_at=now,
        )
        self.repository.add(room)
        self.audit.record(
            user,
            "CREATE",
            "Classroom",
            room.id,
            None,
            ClassroomRead.model_validate(room).model_dump(mode="json"),
        )
        return room

    def update_classroom(
        self, classroom_id: int, data: ClassroomUpdate, user: User
    ) -> Classroom:
        """Update capacity/type with an audit record."""
        require_admin(user)
        room = self.repository.get_or_raise(classroom_id)
        old = ClassroomRead.model_validate(room).model_dump(mode="json")
        room.update(data.capacity, data.room_type)
        room.updated_by, room.updated_at = user.id, self.clock()
        self.repository.flush()
        self.audit.record(
            user,
            "UPDATE",
            "Classroom",
            room.id,
            old,
            ClassroomRead.model_validate(room).model_dump(mode="json"),
        )
        return room

    def deactivate_classroom(self, classroom_id: int, user: User) -> Classroom:
        """Refuse occupied rooms, then retain an inactive record (BR-18)."""
        require_admin(user)
        room = self.repository.get_or_raise(classroom_id)
        room.deactivate(
            bool(self.equipment.find_installed_by_classroom(room.id)),
            self.schedules.has_future_classes(room.id, self.clock().date()),
        )
        room.updated_by, room.updated_at = user.id, self.clock()
        self.repository.flush()
        self.audit.record(
            user,
            "DEACTIVATE",
            "Classroom",
            room.id,
            {"is_active": True},
            {"is_active": False},
        )
        return room

    def set_closure(
        self, classroom_id: int, closed: bool, reason: str, user: User
    ) -> Classroom:
        """Keep an Admin override separate from automatic issue closure (DD-CLS-02)."""
        require_admin(user)
        room = self.repository.get_or_raise(classroom_id)
        if closed and not reason.strip():
            raise ValidationRuleError("Reason is required.")
        old = {"manual_closed": room.manual_closed, "reason": room.manual_closed_reason}
        room.manual_closed, room.manual_closed_reason = closed, (
            reason.strip() if closed else ""
        )
        # IssueManager synchronizes automatic closure; its repository is injected by the provider.
        self.refresh_closure(room)
        room.updated_by, room.updated_at = user.id, self.clock()
        self.repository.flush()
        self.audit.record(
            user,
            "CLOSURE",
            "Classroom",
            room.id,
            old,
            {"manual_closed": closed, "reason": reason},
        )
        return room

    def refresh_closure(self, room: Classroom) -> None:
        """Recompute closure using manual override and unresolved Critical issues."""
        critical = self.critical_issue_lookup(room.id)
        room.closed_for_maintenance = room.manual_closed or critical
        room.closed_reason = (
            room.manual_closed_reason
            if room.manual_closed
            else ("Unresolved Critical room issue." if critical else "")
        )

    def install_equipment(
        self,
        classroom_id: int,
        item_id: int,
        seat_label: str,
        user: User,
        condition: EquipmentCondition = EquipmentCondition.WORKING,
    ) -> RoomEquipment:
        """Install only eligible AST Desktops/Monitors, once at a time."""
        self.schedules.active_room(classroom_id)
        item = self.assets.find_item(item_id)
        if item.category.upper() not in ("DESKTOP", "MONITOR"):
            raise ValidationRuleError(
                "Only Desktop and Monitor items can be installed."
            )
        if item.status.upper().replace(" ", "_") in ("RETIRED", "ON_LOAN", "ONLOAN"):
            raise ConflictError("Retired or on-loan items cannot be installed.")
        existing = self.equipment.find_installed_by_item(item_id)
        if existing:
            raise ConflictError(
                f"This item is already installed in {self.repository.get_or_raise(existing.classroom_id).classroom_id}."
            )
        now = self.clock()
        equipment = self.equipment.add(
            RoomEquipment(
                classroom_id=classroom_id,
                item_id=item_id,
                seat_label=seat_label,
                condition=condition,
                installed_at=now,
                updated_at=now,
                updated_by=user.id,
            )
        )
        self.audit.record(
            user,
            "INSTALL",
            "RoomEquipment",
            equipment.id,
            None,
            {
                "classroom_id": classroom_id,
                "item_id": item_id,
                "condition": condition.value,
            },
        )
        return equipment

    def installed(self, equipment_id: int) -> RoomEquipment:
        """Require a current equipment installation."""
        equipment = self.equipment.get_or_raise(equipment_id)
        if not equipment.is_installed():
            raise ConflictError("Equipment is no longer installed.")
        return equipment

    def set_condition(
        self,
        equipment_id: int,
        condition: EquipmentCondition,
        reason: str,
        user: User,
        version: int | None = None,
        triggered_by: int | None = None,
    ) -> RoomEquipment:
        """Change condition and write its reason/issue link in the same transaction."""
        equipment = self.installed(equipment_id)
        if version is not None:
            check_version(equipment, version)
        old = equipment.set_condition(condition, reason, user.id, self.clock())
        self.equipment.flush()
        self.audit.record(
            user,
            "CONDITION",
            "RoomEquipment",
            equipment.id,
            {"condition": old.value},
            {
                "condition": condition.value,
                "reason": reason,
                "triggered_by": triggered_by,
            },
        )
        return equipment

    def remove_equipment(
        self, equipment_id: int, user: User, version: int | None = None
    ) -> RoomEquipment:
        """Close installation history without changing AST inventory status."""
        equipment = self.installed(equipment_id)
        if version is not None:
            check_version(equipment, version)
        equipment.remove(user.id, self.clock())
        self.equipment.flush()
        self.audit.record(
            user,
            "REMOVE",
            "RoomEquipment",
            equipment.id,
            {"classroom_id": equipment.classroom_id},
            {"removed_at": equipment.removed_at.isoformat()},
        )
        return equipment

    def move_equipment(
        self, equipment_id: int, target_id: int, user: User, version: int
    ) -> RoomEquipment:
        """Retain old placement and create a new placement with the same condition."""
        equipment = self.installed(equipment_id)
        check_version(equipment, version)
        target = self.repository.get_or_raise(target_id)
        if not target.is_active or equipment.classroom_id == target_id:
            raise ValidationRuleError("Choose a different active classroom.")
        self.remove_equipment(equipment.id, user, version)
        return self.install_equipment(
            target_id,
            equipment.item_id,
            equipment.seat_label,
            user,
            equipment.condition,
        )

    def equipment_history(self, equipment_id: int) -> list[EquipmentHistoryRead]:
        """Install, condition, move and removal history of the item behind this record, oldest first."""
        item_id = self.equipment.get_or_raise(equipment_id).item_id
        rows = {e.id: e for e in self.equipment.find_all_for_item(item_id)}
        records = [
            r
            for row_id in rows
            for r in self.audit.search(
                entity_type="RoomEquipment", entity_id=row_id, limit=1000
            )
        ]
        records.sort(key=lambda r: (r.timestamp, r.id))
        return [
            EquipmentHistoryRead(
                timestamp=r.timestamp,
                user_id=r.actor_id,
                action=r.action,
                classroom_id=rows[int(r.entity_id)].classroom_id,
                old_condition=(r.old_value or {}).get("condition"),
                new_condition=(r.new_value or {}).get("condition"),
                reason=(r.new_value or {}).get("reason") or "",
                issue_id=(r.new_value or {}).get("triggered_by"),
            )
            for r in records
        ]

    def is_item_installed(self, item_id: int) -> bool:
        """AST lending guard (DD-CLS-01)."""
        return self.equipment.find_installed_by_item(item_id) is not None

    def remove_retired_item(self, item_id: int, user: User) -> None:
        """AST retirement hook; call within the retirement transaction (BR-18)."""
        equipment = self.equipment.find_installed_by_item(item_id)
        if equipment:
            self.remove_equipment(equipment.id, user)

    def record_room_check(
        self, classroom_id: int, data: RoomCheckCreate, user: User
    ) -> RoomCheck:
        """Require exactly one versioned result for every installed item (US-CLS-04)."""
        room = self.schedules.active_room(classroom_id)
        installed = self.equipment.find_installed_by_classroom(classroom_id)
        ids = [result.room_equipment_id for result in data.results]
        if len(ids) != len(set(ids)) or set(ids) != {e.id for e in installed}:
            raise ValidationRuleError("Provide one result for every installed item.")
        by_id = {e.id: e for e in installed}
        for result in data.results:
            check_version(by_id[result.room_equipment_id], result.version)
        check = self.checks.add(
            RoomCheck(
                classroom_id=classroom_id,
                checked_by=user.id,
                checked_at=self.clock(),
                notes=data.notes,
            )
        )
        for result in data.results:
            equipment = by_id[result.room_equipment_id]
            check.results.append(
                RoomCheckResult(
                    room_equipment_id=equipment.id,
                    observed_condition=result.observed_condition,
                    comment=result.comment,
                )
            )
            if equipment.condition != result.observed_condition:
                self.set_condition(
                    equipment.id,
                    result.observed_condition,
                    f"Room check {check.id}: {result.comment}",
                    user,
                    result.version,
                )
        room.last_checked_at = check.checked_at
        room.updated_by, room.updated_at = user.id, self.clock()
        self.checks.flush()
        self.audit.record(
            user,
            "CHECK",
            "Classroom",
            room.id,
            None,
            {
                "check_id": check.id,
                "notes": data.notes,
                "checked_at": check.checked_at.isoformat(),
            },
        )
        return check

    def get_status(self, classroom_id: int) -> RoomStatus:
        """Derive a room's live equipment status (DD-CLS-02)."""
        room = self.repository.get_or_raise(classroom_id)
        return self.calculator.calculate(
            room, self.equipment.find_installed_by_classroom(classroom_id), self.assets
        )

    def summary(self, room: Classroom) -> ClassroomSummary:
        """Build JSON-safe room metadata and computed status/check flag."""
        location = self.assets.find_location(room.location_id)
        return ClassroomSummary(
            **ClassroomRead.model_validate(room).model_dump(),
            building=location.building,
            room=location.room,
            status=self.get_status(room.id),
            check_overdue=room.is_check_overdue(self.clock().date()),
        )

    def search(self, criteria: ClassroomSearch) -> list[ClassroomSummary]:
        """Combine independent filter strategies with AND (US-CLS-05)."""
        filters: list[ClassroomFilter] = []
        if criteria.building is not None:
            filters.append(BuildingFilter(criteria.building))
        if criteria.room_type is not None:
            filters.append(RoomTypeFilter(criteria.room_type))
        if criteria.min_capacity is not None:
            filters.append(MinCapacityFilter(criteria.min_capacity))
        if criteria.status is not None:
            filters.append(StatusFilter(criteria.status))
        if criteria.slot_date is not None:
            filters.append(
                FreeSlotFilter(
                    self.schedules,
                    criteria.slot_date,
                    criteria.start_time,
                    criteria.end_time,
                )
            )
        summaries = [
            self.summary(room) for room in self.repository.list() if room.is_active
        ]
        return [
            summary for summary in summaries if all(f.matches(summary) for f in filters)
        ]
