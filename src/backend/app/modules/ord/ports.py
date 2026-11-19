"""What ORD needs from the Assets page, as structural protocols (AssetManager satisfies it)."""

from typing import Protocol

from app.modules.usr.models import User


class StockItem(Protocol):
    """A consumable as ORD sees it (AST's ``Consumable``)."""

    id: int
    name: str
    quantity_on_hand: int
    reorder_threshold: int


class StockGateway(Protocol):
    """Consumable lookup and stock-in, implemented by AST's ``AssetManager``."""

    def get_consumable(self, item_id: int) -> StockItem:
        """The consumable, or raise NotFoundError."""

    def add_stock(self, item_id: int, quantity: int, actor: User) -> int:
        """Add received stock; returns the new quantity on hand."""

