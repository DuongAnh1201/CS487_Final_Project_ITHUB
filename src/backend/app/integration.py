"""Cross-page wiring (#65): composes AST, CLS, ORD and NTF without changing those pages.

Each page declares small ports (CLS ``AssetGateway``, AST ``RetirementObserver`` and ``StockMonitor``
observers, ORD ``StockGateway``). This module supplies the real implementations and installs them
as FastAPI dependency overrides in ``wire_pages``. A test (or ``app.state``) can still replace any
of them.
"""

from fastapi import Depends, FastAPI, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.database import get_db
from app.core.exceptions import ConflictError
from app.core import deps
from app.core.deps import (
    get_audit_log,
    get_clock,
    get_current_user,
    get_event_publisher,
    get_notification_service,
)
from app.modules.ast import router as ast_router
from app.modules.ast.models import Location
from app.modules.ast.monitor import StockMonitor
from app.modules.ast.repository import (
    CategoryRepository,
    ConsumableRepository,
    ItemRepository,
    LocationRepository,
    ObserverRepository,
)
from app.modules.ast.service import AssetManager, LendingGuard, RetirementObserver, StockManager
from app.modules.cls import integrations as cls_integrations
from app.modules.cls.integrations import AssetGateway, AssetItem, AssetLocation
from app.modules.cls.router import get_classroom_manager
from app.modules.cls.service import ClassroomManager
from app.modules.ord import router as ord_router
from app.modules.ntf.ports import LowStockDetails
from app.modules.ntf.service import NotificationService
from app.modules.ord.ports import StockGateway
from app.modules.ord.repository import OrderRepository
from app.modules.ord.service import OrderManager
from app.modules.usr.models import User
from app.shared.audit import AuditLog
from app.shared.events import EventPublisher


class RoomLocationRepository(LocationRepository):
    """AST locations, plus the building/room lookup CLS needs for registrar imports."""

    def by_room(self, building: str, room: str) -> Location | None:
        """The location for a building and room, if it exists."""
        return self.session.scalar(select(Location).where(
            Location.building == building, Location.room == room))


class AstAssetGateway:
    """CLS's read-only view of AST items and locations (DD-CLS-01)."""

    def __init__(self, items: ItemRepository, categories: CategoryRepository,
                 locations: RoomLocationRepository) -> None:
        self.items = items
        self.categories = categories
        self.locations = locations

    def find_item(self, item_id: int) -> AssetItem:
        """The item with its category name and status."""
        item = self.items.get_or_raise(item_id)
        return AssetItem(item.id, self.categories.get_or_raise(item.category_id).name, item.status.value)

    def find_location(self, location_id: int) -> AssetLocation:
        """A location by id."""
        location = self.locations.get_or_raise(location_id)
        return AssetLocation(location.id, location.building, location.room)

    def find_location_by_room(self, building: str, room: str) -> AssetLocation | None:
        """A location by building and room, or None."""
        location = self.locations.by_room(building, room)
        return AssetLocation(location.id, location.building, location.room) if location else None


class ClassroomRetirementObserver:
    """On retirement, removes the item from its classroom in the same transaction (BR-18)."""

    def __init__(self, classrooms: ClassroomManager, actor: User) -> None:
        self.classrooms = classrooms
        self.actor = actor

    def on_item_retired(self, item_id: int) -> None:
        """Remove the item's installation, if any."""
        self.classrooms.remove_retired_item(item_id, self.actor)


class ClassroomLendingGuard:
    """Blocks lending equipment that is installed in a classroom (DD-CLS-01, US-AST-05)."""

    def __init__(self, classrooms: ClassroomManager) -> None:
        self.classrooms = classrooms

    def check_can_lend(self, item_id: int) -> None:
        """Raise ConflictError while the item is installed."""
        if self.classrooms.is_item_installed(item_id):
            raise ConflictError("Item is installed in a classroom and cannot be lent.")


def get_asset_gateway(request: Request, db: Session = Depends(get_db)) -> AssetGateway:
    """``app.state.asset_gateway`` when set, otherwise the AST-backed adapter."""
    return getattr(request.app.state, "asset_gateway", None) or AstAssetGateway(
        ItemRepository(db), CategoryRepository(db), RoomLocationRepository(db))


def get_retirement_observers(
    user: User = Depends(get_current_user),
    classrooms: ClassroomManager = Depends(get_classroom_manager),
) -> tuple[RetirementObserver, ...]:
    """CLS removes retired equipment from its room (no cycle: CLS reads AST through repositories)."""
    return (ClassroomRetirementObserver(classrooms, user),)


def get_lending_guards(
    classrooms: ClassroomManager = Depends(get_classroom_manager),
) -> tuple[LendingGuard, ...]:
    """CLS blocks lending installed equipment."""
    return (ClassroomLendingGuard(classrooms),)


class StockAndOrderDetails:
    """NTF's low-stock email values: the AST supply and its location, and the ORD open order."""

    def __init__(self, consumables: ConsumableRepository, locations: LocationRepository,
                 orders: OrderRepository) -> None:
        self.consumables = consumables
        self.locations = locations
        self.orders = orders

    def low_stock_details(self, asset_id: int) -> dict:
        """Template values for ``low-stock.html``; {} for an unknown item."""
        item = self.consumables.get(asset_id)
        if item is None:
            return {}
        location = self.locations.get(item.location_id)
        order = self.orders.open_order_for_item(asset_id)
        return {
            "item_name": item.name, "unit": item.unit, "threshold": item.reorder_threshold,
            "location": f"{location.building} {location.room}" if location else "—",
            "order_id": order.id if order else None, "order_no": f"#{order.id}" if order else "",
            "order_qty": order.quantity_ordered if order else "",
            "order_created": bool(order and order.requested_by is None),  # raised by IT HUB itself
        }


def get_low_stock_details(db: Session = Depends(get_db)) -> LowStockDetails:
    """Low-stock email values from AST and ORD."""
    return StockAndOrderDetails(ConsumableRepository(db), RoomLocationRepository(db), OrderRepository(db))


def get_stock_monitor(db: Session = Depends(get_db)) -> StockMonitor:
    """AST's stock monitor, empty: ``get_asset_manager`` attaches ORD first, then NTF."""
    return StockMonitor(ObserverRepository(db))


def get_asset_manager(
    db: Session = Depends(get_db),
    audit: AuditLog = Depends(get_audit_log),
    clock: Clock = Depends(get_clock),
    publisher: EventPublisher = Depends(get_event_publisher),
    stock: StockManager = Depends(ast_router.get_stock_manager),
    observers: tuple = Depends(ast_router.get_retirement_observers),
    notifications: NotificationService = Depends(get_notification_service),
) -> AssetManager:
    """AST's AssetManager with ORD, then NTF, observing its stock monitor.

    Built once per request, so lending, retirement and every stock-in/out route share one
    monitor and a low-stock movement from any of them can create the order (FR-ORD-01).
    ORD goes first so the Admins' low-stock email can name the order it created.
    """
    assets = _build_asset_manager(db, audit, clock, publisher, stock, observers)
    stock.monitor.attach(OrderManager.for_session(db, assets, audit, publisher, clock))
    stock.monitor.attach(notifications)
    return assets


_build_asset_manager = ast_router.get_asset_manager  # AST's own composition, called directly


def get_stock_gateway(request: Request, assets: AssetManager = Depends(ast_router.get_asset_manager)) -> StockGateway:
    """ORD's gateway: ``app.state.stock_gateway`` when set, otherwise the AssetManager."""
    return getattr(request.app.state, "stock_gateway", None) or assets


def wire_pages(app: FastAPI) -> None:
    """Install the cross-page providers."""
    app.dependency_overrides[cls_integrations.get_asset_gateway] = get_asset_gateway
    app.dependency_overrides[ast_router.get_retirement_observers] = get_retirement_observers
    app.dependency_overrides[ast_router.get_asset_manager] = get_asset_manager
    app.dependency_overrides[ast_router.get_lending_guards] = get_lending_guards
    app.dependency_overrides[ord_router.get_stock_gateway] = get_stock_gateway
    app.dependency_overrides[ast_router.get_stock_monitor] = get_stock_monitor
    app.dependency_overrides[deps.get_low_stock_details] = get_low_stock_details
