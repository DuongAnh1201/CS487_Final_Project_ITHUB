"""Issue manager and side-effect strategies (DD-ISS-01, US-ISS-01–07)."""

from abc import ABC, abstractmethod
from app.core.clock import Clock
from app.core.exceptions import ValidationRuleError
from app.modules.cls.models import EquipmentCondition
from app.modules.cls.service import ClassroomManager, check_version
from app.modules.iss.models import (
    Issue,
    IssueCategory,
    IssueStatus,
    IssueUpdate,
    Severity,
)
from app.modules.iss.repository import IssueRepository
from app.modules.iss.schemas import (
    IssueCreate,
    IssuePage,
    IssueRead,
    IssueSearch,
    IssueSummary,
    StatusChange,
)
from app.modules.usr.models import User, UserStatus
from app.modules.usr.repository import UserRepository
from app.shared.audit import AuditLog
from app.shared.events import DomainEvent, EventPublisher, EventType


class IssueEffect(ABC):
    """Strategy for issue-triggered changes (SP4 §7)."""

    @abstractmethod
    def on_reported(self, issue: Issue, ctx: "IssueManager", user: User) -> None: ...
    @abstractmethod
    def on_started(self, issue: Issue, ctx: "IssueManager", user: User) -> None: ...
    @abstractmethod
    def on_resolved(
        self,
        issue: Issue,
        condition: EquipmentCondition,
        ctx: "IssueManager",
        user: User,
    ) -> None: ...


class NoEquipmentEffect(IssueEffect):
    """Issues without an equipment/critical-room effect need no extra writes."""

    def on_reported(self, issue: Issue, ctx: "IssueManager", user: User) -> None:
        pass

    def on_started(self, issue: Issue, ctx: "IssueManager", user: User) -> None:
        pass

    def on_resolved(
        self,
        issue: Issue,
        condition: EquipmentCondition,
        ctx: "IssueManager",
        user: User,
    ) -> None:
        pass


class HardwareItemEffect(IssueEffect):
    """Keep hardware condition aligned without overriding other active problems."""

    def _set(
        self,
        issue: Issue,
        condition: EquipmentCondition,
        ctx: "IssueManager",
        user: User,
    ) -> None:
        reported = ctx.classrooms.equipment.get_or_raise(issue.room_equipment_id)
        equipment = ctx.classrooms.equipment.find_installed_by_item(reported.item_id)
        # Installation history remains intact when the same item moves rooms.
        if equipment is not None and equipment.condition != condition:
            ctx.classrooms.set_condition(
                equipment.id,
                condition,
                f"Issue {issue.issue_id}",
                user,
                triggered_by=issue.id,
            )

    def on_reported(self, issue: Issue, ctx: "IssueManager", user: User) -> None:
        """Only a Working item becomes Faulty when reported."""
        equipment = ctx.classrooms.equipment.get_or_raise(issue.room_equipment_id)
        if equipment.condition == EquipmentCondition.WORKING:
            self._set(issue, EquipmentCondition.FAULTY, ctx, user)

    def on_started(self, issue: Issue, ctx: "IssueManager", user: User) -> None:
        self._set(issue, EquipmentCondition.UNDER_REPAIR, ctx, user)

    def on_resolved(
        self,
        issue: Issue,
        condition: EquipmentCondition,
        ctx: "IssueManager",
        user: User,
    ) -> None:
        if not ctx.repository.unresolved_for_equipment(
            issue.room_equipment_id, issue.id
        ):
            self._set(issue, condition, ctx, user)


class CriticalRoomEffect(IssueEffect):
    """Close rooms for unresolved Critical room issues; retain Admin overrides."""

    def _refresh(self, issue: Issue, ctx: "IssueManager", user: User) -> None:
        room = ctx.classrooms.repository.get_or_raise(issue.classroom_id)
        old = {
            "closed_for_maintenance": room.closed_for_maintenance,
            "reason": room.closed_reason,
        }
        ctx.classrooms.refresh_closure(room)
        new = {
            "closed_for_maintenance": room.closed_for_maintenance,
            "reason": room.closed_reason,
        }
        if old != new:
            room.updated_by, room.updated_at = user.id, ctx.clock()
            ctx.classrooms.repository.flush()
            ctx.audit.record(
                user,
                "ISSUE_CLOSURE",
                "Classroom",
                room.id,
                old,
                {**new, "triggered_by": issue.id},
            )

    def on_reported(self, issue: Issue, ctx: "IssueManager", user: User) -> None:
        self._refresh(issue, ctx, user)

    def on_started(self, issue: Issue, ctx: "IssueManager", user: User) -> None:
        self._refresh(issue, ctx, user)

    def on_resolved(
        self,
        issue: Issue,
        condition: EquipmentCondition,
        ctx: "IssueManager",
        user: User,
    ) -> None:
        self._refresh(issue, ctx, user)


class IssueEffectFactory:
    """Select side-effect strategies without exposing category logic to managers."""

    def effects_for(self, issue: Issue) -> list[IssueEffect]:
        """Hardware/item and Critical/no-item rules are independent (DD-ISS-01)."""
        if (
            issue.room_equipment_id is not None
            and issue.category == IssueCategory.HARDWARE
        ):
            return [HardwareItemEffect()]
        if issue.room_equipment_id is None and issue.severity == Severity.CRITICAL:
            return [CriticalRoomEffect()]
        return [NoEquipmentEffect()]


class IssueManager:
    """Coordinate state changes, atomic effects, audit, and Observer events."""

    def __init__(
        self,
        repository: IssueRepository,
        classrooms: ClassroomManager,
        users: UserRepository,
        audit: AuditLog,
        clock: Clock,
        publisher: EventPublisher,
    ) -> None:
        self.repository, self.classrooms, self.users = repository, classrooms, users
        self.audit, self.clock, self.publisher = audit, clock, publisher
        self.effects = IssueEffectFactory()

    def summary(self, issue: Issue, user: User) -> IssueSummary:
        """Expose overdue status and legal role-specific transitions."""
        return IssueSummary(
            **IssueRead.model_validate(issue).model_dump(),
            is_overdue=issue.is_overdue(self.clock().date()),
            allowed_next_statuses=issue.allowed_next_statuses(user),
        )

    def create_issue(self, data: IssueCreate, user: User) -> Issue:
        """Save report, equipment effect and audit before publishing (NFR-ISS-05)."""
        self.classrooms.schedules.active_room(data.classroom_id)
        if data.room_equipment_id is not None:
            equipment = self.classrooms.equipment.get_or_raise(data.room_equipment_id)
            if (
                not equipment.is_installed()
                or equipment.classroom_id != data.classroom_id
            ):
                raise ValidationRuleError("Item is not installed in this classroom.")
        issue = self.repository.add(Issue.create(data.model_dump(), user, self.clock()))
        for effect in self.effects.effects_for(issue):
            effect.on_reported(issue, self, user)
        self.audit.record(
            user,
            "CREATE",
            "Issue",
            issue.id,
            None,
            IssueRead.model_validate(issue).model_dump(mode="json"),
        )
        self.repository.flush()
        self.publisher.publish(
            DomainEvent(
                event_type=EventType.ISSUE_REPORTED,
                message=f"Issue {issue.issue_id} reported: {issue.description}",
                actor_id=user.id,
                related_type="Issue",
                related_id=issue.id,
            )
        )
        return issue

    def _original(self, issue: Issue, original_id: int | None) -> Issue:
        if original_id is None:
            raise ValidationRuleError("Choose the original issue.")
        seen = {issue.id}
        while True:
            if original_id in seen:
                raise ValidationRuleError("Choose the original issue.")
            seen.add(original_id)
            original = self.repository.get(original_id)
            if original is None:
                raise ValidationRuleError("Choose the original issue.")
            if original.duplicate_of_id is None:
                return original
            original_id = original.duplicate_of_id

    def change_status(self, issue_id: int, data: StatusChange, user: User) -> Issue:
        """Apply the fixed state machine and its transactional effects (BR-23)."""
        issue = self.repository.get_or_raise(issue_id)
        check_version(issue, data.version)
        original = (
            self._original(issue, data.original_id)
            if data.status == IssueStatus.DUPLICATE
            else None
        )
        if data.status == IssueStatus.ASSIGNED and data.assignee_id is not None:
            assignee = self.users.get_or_raise(data.assignee_id)
            if assignee.status != UserStatus.ACTIVE:
                raise ValidationRuleError("Assignee must be active.")
        old = IssueRead.model_validate(issue).model_dump(mode="json")
        issue.change_status(
            data.status,
            user,
            self.clock(),
            data.note,
            data.assignee_id,
            original.id if original else None,
        )
        self.repository.flush()
        for effect in self.effects.effects_for(issue):
            if data.status == IssueStatus.IN_PROGRESS:
                effect.on_started(issue, self, user)
            if data.status == IssueStatus.RESOLVED:
                effect.on_resolved(issue, data.new_condition, self, user)
            # Final rejected/duplicate room issues must not leave an automatic closure stuck.
            if data.status in (
                IssueStatus.REJECTED,
                IssueStatus.DUPLICATE,
            ) and isinstance(effect, CriticalRoomEffect):
                effect.on_resolved(issue, data.new_condition, self, user)
        self.audit.record(
            user,
            "STATUS",
            "Issue",
            issue.id,
            old,
            IssueRead.model_validate(issue).model_dump(mode="json"),
        )
        if (
            original
            and not original.is_repeat_problem
            and 1 + self.repository.count_duplicates(original.id) > 3
        ):
            original.is_repeat_problem = True
            self.repository.flush()
            self.audit.record(
                user,
                "REPEAT_PROBLEM",
                "Issue",
                original.id,
                {"is_repeat_problem": False},
                {"is_repeat_problem": True},
            )
            self.publisher.publish(
                DomainEvent(
                    event_type=EventType.REPEAT_PROBLEM,
                    message=f"Repeat problem: {original.issue_id}",
                    actor_id=user.id,
                    related_type="Issue",
                    related_id=original.id,
                )
            )
        return issue

    def resolve_issue(
        self,
        issue_id: int,
        notes: str,
        condition: EquipmentCondition,
        version: int,
        user: User,
    ) -> Issue:
        """Resolve through the same state machine used by general status changes."""
        return self.change_status(
            issue_id,
            StatusChange(
                status=IssueStatus.RESOLVED,
                version=version,
                note=notes,
                new_condition=condition,
            ),
            user,
        )

    def mark_duplicate(
        self, issue_id: int, original_id: int, version: int, user: User
    ) -> Issue:
        """Canonicalize duplicate chains and notify once at report four (FR-ISS-08)."""
        return self.change_status(
            issue_id,
            StatusChange(
                status=IssueStatus.DUPLICATE, version=version, original_id=original_id
            ),
            user,
        )

    def add_comment(self, issue_id: int, text: str, version: int, user: User) -> Issue:
        """Append immutable history; version it against simultaneous edits."""
        issue = self.repository.get_or_raise(issue_id)
        check_version(issue, version)
        issue.add_comment(text, user, self.clock())
        issue.version += 1
        self.repository.flush()
        self.audit.record(
            user, "COMMENT", "Issue", issue.id, None, {"comment": text.strip()}
        )
        return issue

    def find_possible_duplicates(
        self, classroom_id: int, equipment_id: int | None, category: IssueCategory
    ) -> list[Issue]:
        """Offer unresolved matching reports before recording another issue."""
        self.classrooms.repository.get_or_raise(classroom_id)
        return self.repository.possible_duplicates(classroom_id, equipment_id, category)

    def search_issues(self, criteria: IssueSearch, user: User) -> IssuePage:
        """Return a bounded, filtered issue page (FR-ISS-04)."""
        issues, total = self.repository.search(criteria)
        return IssuePage(
            items=[self.summary(issue, user) for issue in issues],
            total=total,
            page=criteria.page,
            page_size=criteria.page_size,
            message=None if issues else "No issues match your filters.",
        )

    def get_history(self, issue_id: int) -> list[IssueUpdate]:
        """Return append-only history in chronological order (US-ISS-07)."""
        return self.repository.get_or_raise(issue_id).history
