"""Thin CLS REST routes; managers enforce domain rules (NFR-CLS-03)."""

from datetime import date
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.clock import Clock
from app.core.database import get_db
from app.core.deps import get_audit_log, get_clock, get_current_user
from app.modules.usr.models import User
from app.modules.cls.integrations import AssetGateway, get_asset_gateway
from app.modules.cls.repository import (
    ClassroomRepository,
    RoomEquipmentRepository,
    RoomCheckRepository,
    ScheduleRepository,
    ScheduleImportRepository,
)
from app.modules.cls.schemas import (
    ClassroomCreate,
    ClassroomUpdate,
    ClassroomRead,
    ClassroomSummary,
    ClassroomSearch,
    ClosureUpdate,
    EquipmentCreate,
    EquipmentRead,
    ConditionUpdate,
    EquipmentMove,
    VersionRequest,
    RoomCheckCreate,
    RoomCheckRead,
    ScheduleCreate,
    ScheduleRead,
    CsvImportCreate,
    ScheduleImportRead,
    Timetable,
)
from app.modules.cls.service import ClassroomManager, ScheduleManager
from app.shared.audit import AuditLog

router = APIRouter(tags=["classrooms and schedules"])


def get_schedule_manager(
    db: Session = Depends(get_db),
    assets: AssetGateway = Depends(get_asset_gateway),
    audit: AuditLog = Depends(get_audit_log),
    clock: Clock = Depends(get_clock),
) -> ScheduleManager:
    """Construct a request-scoped schedule manager."""
    return ScheduleManager(
        ScheduleRepository(db),
        ScheduleImportRepository(db),
        ClassroomRepository(db),
        assets,
        audit,
        clock,
    )


def get_classroom_manager(
    db: Session = Depends(get_db),
    assets: AssetGateway = Depends(get_asset_gateway),
    schedules: ScheduleManager = Depends(get_schedule_manager),
    audit: AuditLog = Depends(get_audit_log),
    clock: Clock = Depends(get_clock),
) -> ClassroomManager:
    """Construct CLS services in the request's shared transaction."""
    from app.modules.iss.repository import IssueRepository

    manager = ClassroomManager(
        ClassroomRepository(db),
        RoomEquipmentRepository(db),
        RoomCheckRepository(db),
        schedules,
        assets,
        audit,
        clock,
        IssueRepository(db).has_critical_room_issue,
    )
    return manager


Manager = Annotated[ClassroomManager, Depends(get_classroom_manager)]
Schedules = Annotated[ScheduleManager, Depends(get_schedule_manager)]
Actor = Annotated[User, Depends(get_current_user)]


@router.post("/classrooms", response_model=ClassroomRead, status_code=201)
def create_classroom(
    data: ClassroomCreate, manager: Manager, user: Actor
) -> ClassroomRead:
    """US-CLS-01: create a classroom."""
    return ClassroomRead.model_validate(manager.add_classroom(data, user))


@router.get("/classrooms", response_model=list[ClassroomSummary])
def list_classrooms(
    manager: Manager, user: Actor, criteria: Annotated[ClassroomSearch, Query()]
) -> list[ClassroomSummary]:
    """US-CLS-04/05: active rooms and combined search criteria."""
    return manager.search(criteria)


@router.get("/classrooms/{classroom_id}", response_model=ClassroomSummary)
def classroom_detail(
    classroom_id: int, manager: Manager, user: Actor
) -> ClassroomSummary:
    """Read a retained classroom and derived status."""
    return manager.summary(manager.repository.get_or_raise(classroom_id))


@router.patch("/classrooms/{classroom_id}", response_model=ClassroomRead)
def update_classroom(
    classroom_id: int, data: ClassroomUpdate, manager: Manager, user: Actor
) -> ClassroomRead:
    """US-CLS-01: edit capacity and type."""
    return ClassroomRead.model_validate(
        manager.update_classroom(classroom_id, data, user)
    )


@router.post("/classrooms/{classroom_id}/deactivate", response_model=ClassroomRead)
def deactivate(classroom_id: int, manager: Manager, user: Actor) -> ClassroomRead:
    """BR-18: deactivate an unused room."""
    return ClassroomRead.model_validate(
        manager.deactivate_classroom(classroom_id, user)
    )


@router.post("/classrooms/{classroom_id}/closure", response_model=ClassroomRead)
def closure(
    classroom_id: int, data: ClosureUpdate, manager: Manager, user: Actor
) -> ClassroomRead:
    """DD-CLS-02: apply or clear an Admin maintenance override."""
    return ClassroomRead.model_validate(
        manager.set_closure(classroom_id, data.closed, data.reason, user)
    )


@router.get("/classrooms/{classroom_id}/equipment", response_model=list[EquipmentRead])
def equipment_list(
    classroom_id: int, manager: Manager, user: Actor
) -> list[EquipmentRead]:
    """Read current installations."""
    manager.repository.get_or_raise(classroom_id)
    return [
        EquipmentRead.model_validate(e)
        for e in manager.equipment.find_installed_by_classroom(classroom_id)
    ]


@router.post(
    "/classrooms/{classroom_id}/equipment",
    response_model=EquipmentRead,
    status_code=201,
)
def install(
    classroom_id: int, data: EquipmentCreate, manager: Manager, user: Actor
) -> EquipmentRead:
    """DD-CLS-01: install an AST Desktop or Monitor."""
    return EquipmentRead.model_validate(
        manager.install_equipment(classroom_id, data.item_id, data.seat_label, user)
    )


@router.post(
    "/classroom-equipment/{equipment_id}/condition", response_model=EquipmentRead
)
def condition(
    equipment_id: int, data: ConditionUpdate, manager: Manager, user: Actor
) -> EquipmentRead:
    """US-CLS-03: change equipment condition with a reason."""
    return EquipmentRead.model_validate(
        manager.set_condition(
            equipment_id, data.condition, data.reason, user, data.version
        )
    )


@router.post("/classroom-equipment/{equipment_id}/move", response_model=EquipmentRead)
def move(
    equipment_id: int, data: EquipmentMove, manager: Manager, user: Actor
) -> EquipmentRead:
    """US-CLS-02: move equipment, keeping installation history."""
    return EquipmentRead.model_validate(
        manager.move_equipment(equipment_id, data.to_classroom_id, user, data.version)
    )


@router.post("/classroom-equipment/{equipment_id}/remove", response_model=EquipmentRead)
def remove(
    equipment_id: int, data: VersionRequest, manager: Manager, user: Actor
) -> EquipmentRead:
    """US-CLS-02: close an installation."""
    return EquipmentRead.model_validate(
        manager.remove_equipment(equipment_id, user, data.version)
    )


@router.post(
    "/classrooms/{classroom_id}/checks", response_model=RoomCheckRead, status_code=201
)
def room_check(
    classroom_id: int, data: RoomCheckCreate, manager: Manager, user: Actor
) -> RoomCheckRead:
    """US-CLS-04: record every installed item's observed condition."""
    return RoomCheckRead.model_validate(
        manager.record_room_check(classroom_id, data, user)
    )


@router.post("/schedule/imports", response_model=ScheduleImportRead, status_code=201)
def import_schedule(
    data: CsvImportCreate, manager: Schedules, user: Actor
) -> ScheduleImportRead:
    """US-CLS-06: accept registrar CSV text as JSON, reporting rejected rows."""
    return ScheduleImportRead.model_validate(
        manager.import_csv(data.file_name, data.content, user)
    )


@router.get("/schedule/imports/{import_id}", response_model=ScheduleImportRead)
def import_result(
    import_id: int, manager: Schedules, user: Actor
) -> ScheduleImportRead:
    """Read a retained schedule-import result."""
    return ScheduleImportRead.model_validate(manager.imports.get_or_raise(import_id))


@router.post("/schedule/entries", response_model=ScheduleRead, status_code=201)
def add_entry(data: ScheduleCreate, manager: Schedules, user: Actor) -> ScheduleRead:
    """US-CLS-07: add a meeting."""
    return ScheduleRead.model_validate(manager.add_entry(data, user))


@router.put("/schedule/entries/{entry_id}", response_model=ScheduleRead)
def edit_entry(
    entry_id: int, data: ScheduleCreate, manager: Schedules, user: Actor
) -> ScheduleRead:
    """US-CLS-07: replace editable meeting fields."""
    return ScheduleRead.model_validate(manager.edit_entry(entry_id, data, user))


@router.post("/schedule/entries/{entry_id}/cancel", response_model=ScheduleRead)
def cancel_entry(entry_id: int, manager: Schedules, user: Actor) -> ScheduleRead:
    """BR-19: cancel while retaining the meeting."""
    return ScheduleRead.model_validate(manager.cancel_entry(entry_id, user))


@router.get("/classrooms/{classroom_id}/timetable", response_model=Timetable)
def timetable(
    classroom_id: int,
    day: date,
    manager: Schedules,
    user: Actor,
    view: Literal["day", "week"] = "day",
) -> Timetable:
    """US-CLS-08: ordered day/week timetable."""
    return manager.get_timetable(classroom_id, day, view)
