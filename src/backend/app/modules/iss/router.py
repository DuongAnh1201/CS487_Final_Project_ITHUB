"""Thin JSON issue routes, backed by IssueManager (US-ISS-01–07)."""

from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.clock import Clock
from app.core.database import get_db
from app.core.deps import (
    get_audit_log,
    get_clock,
    get_current_user,
    get_event_publisher,
)
from app.modules.cls.router import get_classroom_manager
from app.modules.cls.service import ClassroomManager
from app.modules.iss.models import IssueCategory
from app.modules.iss.repository import IssueRepository
from app.modules.iss.schemas import (
    IssueCreate,
    IssueRead,
    IssueSummary,
    IssueSearch,
    IssuePage,
    StatusChange,
    IssueResolve,
    IssueDuplicate,
    IssueComment,
    IssueUpdateRead,
)
from app.modules.iss.service import IssueManager
from app.modules.usr.models import User
from app.modules.usr.repository import UserRepository
from app.shared.audit import AuditLog
from app.shared.events import EventPublisher

router = APIRouter(prefix="/issues", tags=["issues"])


def get_issue_manager(
    db: Session = Depends(get_db),
    classrooms: ClassroomManager = Depends(get_classroom_manager),
    audit: AuditLog = Depends(get_audit_log),
    clock: Clock = Depends(get_clock),
    publisher: EventPublisher = Depends(get_event_publisher),
) -> IssueManager:
    """Inject the same transaction and publisher into the issue workflow."""
    return IssueManager(
        IssueRepository(db), classrooms, UserRepository(db), audit, clock, publisher
    )


Manager = Annotated[IssueManager, Depends(get_issue_manager)]
Actor = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=IssueRead, status_code=201)
def report(data: IssueCreate, manager: Manager, user: Actor) -> IssueRead:
    """US-ISS-01: record an issue and apply automatic effects."""
    return IssueRead.model_validate(manager.create_issue(data, user))


@router.get("", response_model=IssuePage)
def search(
    manager: Manager, user: Actor, criteria: Annotated[IssueSearch, Query()]
) -> IssuePage:
    """US-ISS-02: filter and page at fifty rows."""
    return manager.search_issues(criteria, user)


@router.get("/possible-duplicates", response_model=list[IssueRead])
def possible_duplicates(
    classroom_id: int,
    category: IssueCategory,
    manager: Manager,
    user: Actor,
    room_equipment_id: int | None = None,
) -> list[IssueRead]:
    """US-ISS-06: suggest existing reports before saving another."""
    return [
        IssueRead.model_validate(issue)
        for issue in manager.find_possible_duplicates(
            classroom_id, room_equipment_id, category
        )
    ]


@router.get("/{issue_id}", response_model=IssueSummary)
def detail(issue_id: int, manager: Manager, user: Actor) -> IssueSummary:
    """US-ISS-02/03: expose issue detail and legal transitions."""
    return manager.summary(manager.repository.get_or_raise(issue_id), user)


@router.post("/{issue_id}/status", response_model=IssueRead)
def status(
    issue_id: int, data: StatusChange, manager: Manager, user: Actor
) -> IssueRead:
    """US-ISS-03: execute a validated state transition."""
    return IssueRead.model_validate(manager.change_status(issue_id, data, user))


@router.post("/{issue_id}/resolve", response_model=IssueRead)
def resolve(
    issue_id: int, data: IssueResolve, manager: Manager, user: Actor
) -> IssueRead:
    """US-ISS-05: resolve with notes and a chosen equipment condition."""
    return IssueRead.model_validate(
        manager.resolve_issue(
            issue_id, data.notes, data.new_condition, data.version, user
        )
    )


@router.post("/{issue_id}/duplicate", response_model=IssueRead)
def duplicate(
    issue_id: int, data: IssueDuplicate, manager: Manager, user: Actor
) -> IssueRead:
    """US-ISS-06: link to the original and flag repeat problems."""
    return IssueRead.model_validate(
        manager.mark_duplicate(issue_id, data.original_id, data.version, user)
    )


@router.post("/{issue_id}/comments", response_model=IssueRead)
def comment(
    issue_id: int, data: IssueComment, manager: Manager, user: Actor
) -> IssueRead:
    """US-ISS-04: append a progress note."""
    return IssueRead.model_validate(
        manager.add_comment(issue_id, data.text, data.version, user)
    )


@router.get("/{issue_id}/history", response_model=list[IssueUpdateRead])
def history(issue_id: int, manager: Manager, user: Actor) -> list[IssueUpdateRead]:
    """US-ISS-07: read the immutable chronological timeline."""
    return [
        IssueUpdateRead.model_validate(update)
        for update in manager.get_history(issue_id)
    ]
