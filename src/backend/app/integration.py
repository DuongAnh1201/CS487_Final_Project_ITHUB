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
from app.core.deps import get_audit_log, get_clock, get_current_user, get_event_publisher
from app.modules.ast import router as ast_router
from app.modules.ast.models import Location
from app.modules.ast.repository import CategoryRepository, ItemRepository, LocationRepository
from app.modules.ast.service import AssetManager, RetirementObserver, StockManager
from app.modules.cls import integrations as cls_integrations
from app.modules.cls.integrations import AssetGateway, AssetItem, AssetLocation
from app.modules.cls.router import get_classroom_manager
from app.modules.cls.service import ClassroomManager
from app.modules.ord import router as ord_router
from app.modules.ord.ports import StockGateway
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


def get_asset_manager(
    db: Session = Depends(get_db),
    audit: AuditLog = Depends(get_audit_log),
    clock: Clock = Depends(get_clock),
    publisher: EventPublisher = Depends(get_event_publisher),
    stock: StockManager = Depends(ast_router.get_stock_manager),
    observers: tuple = Depends(ast_router.get_retirement_observers),
) -> AssetManager:
    """AST's AssetManager with ORD attached to its stock monitor (NTF is attached by AST).

    Built once per request, so lending, retirement and every stock-in/out route share one
    monitor and a low-stock movement from any of them can create the order (FR-ORD-01).
    """
    assets = _build_asset_manager(db, audit, clock, publisher, stock, observers)
    stock.monitor.attach(OrderManager.for_session(db, assets, audit, publisher, clock))
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
    app.dependency_overrides[ord_router.get_stock_gateway] = get_stock_gateway
