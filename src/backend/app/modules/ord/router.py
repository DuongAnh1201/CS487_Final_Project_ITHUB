"""ORD routes: /orders. Admins and Student Assistants have the same access (BR-RPT-02)."""

from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.database import get_db
from app.core.deps import get_audit_log, get_clock, get_current_user, get_event_publisher
from app.modules.ord.models import Order, OrderStatus
from app.modules.ord.ports import StockGateway
from app.modules.ord.repository import OrderRepository
from app.modules.ord.schemas import OrderCreate, OrderRead, OrderSummary, ReceiveRequest
from app.modules.ord.service import OrderManager
from app.modules.usr.models import User
from app.shared.audit import AuditLog
from app.shared.events import EventPublisher

router = APIRouter(prefix="/orders", tags=["orders"])


def get_stock_gateway(request: Request) -> StockGateway:
    """The Assets-page gateway (``app.state.stock_gateway``); override to wire AssetManager."""
    return request.app.state.stock_gateway


def get_order_manager(
    db: Session = Depends(get_db),
    stock: StockGateway = Depends(get_stock_gateway),
    audit: AuditLog = Depends(get_audit_log),
    publisher: EventPublisher = Depends(get_event_publisher),
    clock: Clock = Depends(get_clock),
) -> OrderManager:
    """OrderManager for the request."""
    return OrderManager(OrderRepository(db), stock, audit, publisher, clock)


@router.post("", response_model=OrderRead, status_code=201)
def create_order(body: OrderCreate, user: User = Depends(get_current_user),
                 manager: OrderManager = Depends(get_order_manager)) -> Order:
    """Order a consumable (UC-ORD-01)."""
    return manager.create_order(user, body.item_id, body.quantity, body.vendor)


@router.get("", response_model=list[OrderRead])
def search_orders(
    q: str | None = None, status: OrderStatus | None = None, item_id: int | None = None,
    date_from: date | None = None, date_to: date | None = None,
    user: User = Depends(get_current_user), manager: OrderManager = Depends(get_order_manager),
) -> list[Order]:
    """Search by order id or item name; filter by status, item and date (FR-ORD-05)."""
    return manager.search_orders(q, status, item_id, date_from, date_to)


@router.get("/summary", response_model=OrderSummary)
def order_summary(user: User = Depends(get_current_user),
                  manager: OrderManager = Depends(get_order_manager)) -> OrderSummary:
    """Order counts by status (FR-ORD-04)."""
    total, by_status = manager.summary()
    return OrderSummary(total=total, by_status=by_status)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, user: User = Depends(get_current_user),
              manager: OrderManager = Depends(get_order_manager)) -> Order:
    """One order."""
    return manager.find_order(order_id)


@router.post("/{order_id}/place", response_model=OrderRead)
def place_order(order_id: int, user: User = Depends(get_current_user),
                manager: OrderManager = Depends(get_order_manager)) -> Order:
    """Mark a requested order as ordered (UC-ORD-02)."""
    return manager.place_order(user, order_id)


@router.post("/{order_id}/receive", response_model=OrderRead)
def receive_order(order_id: int, body: ReceiveRequest, user: User = Depends(get_current_user),
                  manager: OrderManager = Depends(get_order_manager)) -> Order:
    """Record received quantity; stock is added automatically (UC-ORD-03)."""
    return manager.receive_order(user, order_id, body.quantity)


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_order(order_id: int, user: User = Depends(get_current_user),
                 manager: OrderManager = Depends(get_order_manager)) -> Order:
    """Cancel a requested or ordered order."""
    return manager.cancel_order(user, order_id)
