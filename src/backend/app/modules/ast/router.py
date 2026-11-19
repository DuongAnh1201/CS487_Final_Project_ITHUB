"""Thin AST JSON routes: validate, invoke manager, serialize response."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.database import get_db
from app.core.deps import (
    get_audit_log,
    get_clock,
    get_current_user,
    get_event_publisher,
    get_notification_service,
    require_role,
)
from app.modules.ast import schemas as s
from app.modules.ast.models import ItemStatus
from app.modules.ast.monitor import StockMonitor
from app.modules.ast.repository import (
    BorrowerRepository,
    CategoryRepository,
    ConsumableRepository,
    IncidentRepository,
    ItemRepository,
    LoanRepository,
    LocationRepository,
    ObserverRepository,
    StockTransactionRepository,
)
from app.modules.ast.service import (
    AssetManager,
    LendingManager,
    RetirementObserver,
    StockManager,
)
from app.modules.ntf.service import NotificationService
from app.modules.usr.models import Role, User
from app.shared.audit import AuditLog
from app.shared.events import EventPublisher

router = APIRouter(
    prefix="/ast", tags=["assets"], dependencies=[Depends(get_current_user)]
)


def get_stock_monitor(
    db: Session = Depends(get_db),
    notifications: NotificationService = Depends(get_notification_service),
) -> StockMonitor:
    """Request-scoped subject; ORD can attach its observer after building assets."""
    monitor = StockMonitor(ObserverRepository(db))
    monitor.attach(notifications)
    return monitor


def get_retirement_observers() -> tuple[RetirementObserver, ...]:
    """CLS injects classroom removal here without a circular module dependency."""
    return ()


def get_stock_manager(
    db: Session = Depends(get_db),
    audit: AuditLog = Depends(get_audit_log),
    clock: Clock = Depends(get_clock),
    publisher: EventPublisher = Depends(get_event_publisher),
    monitor: StockMonitor = Depends(get_stock_monitor),
) -> StockManager:
    """Stock manager shares the request transaction and monitor."""
    return StockManager(
        ConsumableRepository(db),
        StockTransactionRepository(db),
        audit,
        clock,
        publisher,
        monitor,
    )


def get_asset_manager(
    db: Session = Depends(get_db),
    audit: AuditLog = Depends(get_audit_log),
    clock: Clock = Depends(get_clock),
    publisher: EventPublisher = Depends(get_event_publisher),
    stock: StockManager = Depends(get_stock_manager),
    observers: tuple = Depends(get_retirement_observers),
) -> AssetManager:
    """Build the cross-page asset gateway without a dependency cycle."""
    return AssetManager(
        ItemRepository(db),
        CategoryRepository(db),
        LocationRepository(db),
        ConsumableRepository(db),
        IncidentRepository(db),
        stock,
        audit,
        clock,
        publisher,
        observers,
    )


def get_lending_manager(
    db: Session = Depends(get_db),
    audit: AuditLog = Depends(get_audit_log),
    clock: Clock = Depends(get_clock),
    publisher: EventPublisher = Depends(get_event_publisher),
    assets: AssetManager = Depends(get_asset_manager),
) -> LendingManager:
    """Lending and assets use the same request transaction."""
    return LendingManager(
        LoanRepository(db), BorrowerRepository(db), assets, audit, clock, publisher
    )


@router.post("/categories", response_model=s.CategoryRead, status_code=201)
def create_category(
    data: s.CategoryCreate,
    user: User = Depends(require_role(Role.ADMIN)),
    manager: AssetManager = Depends(get_asset_manager),
) -> s.CategoryRead:
    """Provision a category."""
    return s.CategoryRead.model_validate(manager.create_category(data, user))


@router.get("/categories", response_model=list[s.CategoryRead])
def categories(
    manager: AssetManager = Depends(get_asset_manager),
) -> list[s.CategoryRead]:
    """Category lookup."""
    return [s.CategoryRead.model_validate(x) for x in manager.list_categories()]


@router.post("/locations", response_model=s.LocationRead, status_code=201)
def create_location(
    data: s.LocationCreate,
    user: User = Depends(get_current_user),
    manager: AssetManager = Depends(get_asset_manager),
) -> s.LocationRead:
    """Provision a location."""
    return s.LocationRead.model_validate(manager.create_location(data, user))


@router.get("/locations", response_model=list[s.LocationRead])
def locations(
    manager: AssetManager = Depends(get_asset_manager),
) -> list[s.LocationRead]:
    """Location lookup shared with CLS."""
    return [s.LocationRead.model_validate(x) for x in manager.list_locations()]


@router.post("/items", response_model=s.ItemRead, status_code=201)
def register(
    data: s.ItemCreate,
    user: User = Depends(get_current_user),
    manager: AssetManager = Depends(get_asset_manager),
) -> s.ItemRead:
    """US-AST-01: register equipment."""
    return s.ItemRead.model_validate(manager.register(data, user))


@router.get("/items", response_model=list[s.ItemRead])
def search(
    asset_tag: str | None = None,
    serial_number: str | None = None,
    model: str | None = None,
    category_id: int | None = None,
    location_id: int | None = None,
    status: ItemStatus | None = None,
    manager: AssetManager = Depends(get_asset_manager),
) -> list[s.ItemRead]:
    """US-AST-03: conjunctive search and filters."""
    return [
        s.ItemRead.model_validate(x)
        for x in manager.search(
            asset_tag=asset_tag,
            serial_number=serial_number,
            model=model,
            category_id=category_id,
            location_id=location_id,
            status=status,
        )
    ]


@router.get("/items/{item_id}", response_model=s.ItemRead)
def get_item(
    item_id: int, manager: AssetManager = Depends(get_asset_manager)
) -> s.ItemRead:
    """Equipment lookup."""
    return s.ItemRead.model_validate(manager.get_item(item_id))


@router.patch("/items/{item_id}", response_model=s.ItemRead)
def edit(
    item_id: int,
    data: s.ItemUpdate,
    user: User = Depends(get_current_user),
    manager: AssetManager = Depends(get_asset_manager),
) -> s.ItemRead:
    """US-AST-02: edit descriptive fields."""
    return s.ItemRead.model_validate(manager.edit(item_id, data, user))


@router.post(
    "/items/{item_id}/incidents", response_model=s.IncidentRead, status_code=201
)
def incident(
    item_id: int,
    data: s.IncidentCreate,
    user: User = Depends(get_current_user),
    manager: AssetManager = Depends(get_asset_manager),
) -> s.IncidentRead:
    """US-AST-10: report loss or damage."""
    return s.IncidentRead.model_validate(manager.incident(item_id, data, user))


@router.post("/items/{item_id}/retire", response_model=s.IncidentRead, status_code=201)
def retire(
    item_id: int,
    data: s.RetireRequest,
    user: User = Depends(require_role(Role.ADMIN)),
    manager: AssetManager = Depends(get_asset_manager),
) -> s.IncidentRead:
    """US-AST-11: Admin retirement."""
    return s.IncidentRead.model_validate(manager.retire(item_id, data, user))


@router.post("/consumables", response_model=s.ConsumableRead, status_code=201)
def create_consumable(
    data: s.ConsumableCreate,
    user: User = Depends(get_current_user),
    manager: AssetManager = Depends(get_asset_manager),
) -> s.ConsumableRead:
    """Provision supplies with zero stock."""
    return s.ConsumableRead.model_validate(manager.create_consumable(data, user))


@router.get("/consumables", response_model=list[s.ConsumableRead])
def consumables(
    manager: AssetManager = Depends(get_asset_manager),
) -> list[s.ConsumableRead]:
    """Stock lookup."""
    return [s.ConsumableRead.model_validate(x) for x in manager.list_consumables()]


@router.get("/consumables/{item_id}", response_model=s.ConsumableRead)
def get_consumable(
    item_id: int, manager: AssetManager = Depends(get_asset_manager)
) -> s.ConsumableRead:
    """ORD quantity lookup."""
    return s.ConsumableRead.model_validate(manager.get_consumable(item_id))


@router.post("/consumables/{item_id}/stock-in", response_model=s.ConsumableRead)
def stock_in(
    item_id: int,
    data: s.StockChange,
    user: User = Depends(get_current_user),
    manager: AssetManager = Depends(get_asset_manager),
) -> s.ConsumableRead:
    """US-AST-04: receive stock."""
    return s.ConsumableRead.model_validate(manager.stock.stock_in(item_id, data, user))


@router.post("/consumables/{item_id}/stock-out", response_model=s.ConsumableRead)
def stock_out(
    item_id: int,
    data: s.StockChange,
    user: User = Depends(get_current_user),
    manager: AssetManager = Depends(get_asset_manager),
) -> s.ConsumableRead:
    """US-AST-04: issue stock."""
    return s.ConsumableRead.model_validate(manager.stock.stock_out(item_id, data, user))


@router.get(
    "/consumables/{item_id}/transactions", response_model=list[s.StockTransactionRead]
)
def movements(
    item_id: int, manager: StockManager = Depends(get_stock_manager)
) -> list[s.StockTransactionRead]:
    """Stock movement history."""
    return [s.StockTransactionRead.model_validate(x) for x in manager.history(item_id)]


@router.post("/borrowers", response_model=s.BorrowerRead, status_code=201)
def create_borrower(
    data: s.BorrowerCreate,
    user: User = Depends(get_current_user),
    manager: LendingManager = Depends(get_lending_manager),
) -> s.BorrowerRead:
    """Record a new borrower."""
    return s.BorrowerRead.model_validate(manager.create_borrower(data, user))


@router.get("/borrowers", response_model=list[s.BorrowerRead])
def borrowers(
    manager: LendingManager = Depends(get_lending_manager),
) -> list[s.BorrowerRead]:
    """Find a known borrower by school ID in the returned lookup."""
    return [s.BorrowerRead.model_validate(x) for x in manager.list_borrowers()]


@router.post("/loans", response_model=s.LoanRead, status_code=201)
def lend(
    data: s.LoanCreate,
    user: User = Depends(get_current_user),
    manager: LendingManager = Depends(get_lending_manager),
) -> s.LoanRead:
    """US-AST-05: lend available equipment."""
    return s.LoanRead.model_validate(manager.lend(data, user))


@router.post("/items/{item_id}/return", response_model=s.LoanRead)
def return_item(
    item_id: int,
    data: s.LoanReturn,
    user: User = Depends(get_current_user),
    manager: LendingManager = Depends(get_lending_manager),
) -> s.LoanRead:
    """US-AST-06: return equipment."""
    return s.LoanRead.model_validate(manager.return_item(item_id, data, user))


@router.post("/loans/{loan_id}/extend", response_model=s.LoanRead)
def extend(
    loan_id: int,
    data: s.LoanExtend,
    user: User = Depends(get_current_user),
    manager: LendingManager = Depends(get_lending_manager),
) -> s.LoanRead:
    """US-AST-07: one extension."""
    return s.LoanRead.model_validate(manager.extend(loan_id, data, user))


@router.get("/loans", response_model=list[s.LoanRead])
def history(
    item_id: int | None = None,
    borrower_id: int | None = None,
    manager: LendingManager = Depends(get_lending_manager),
) -> list[s.LoanRead]:
    """US-AST-09: current and past loans by item/borrower."""
    return [s.LoanRead.model_validate(x) for x in manager.history(item_id, borrower_id)]


@router.get("/overdue", response_model=list[s.OverdueRead])
def overdue(
    manager: LendingManager = Depends(get_lending_manager),
) -> list[s.OverdueRead]:
    """US-AST-08: unreturned loans past the due date, with borrower contacts."""
    return manager.overdue()
