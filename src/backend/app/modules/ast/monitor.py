"""Stock Observer subject shared with ORD and NTF (FR-AST-14)."""

import logging

from app.modules.ast.repository import ObserverRepository
from app.shared.events import StockObserver


class StockMonitor:
    """Notify observers at/below threshold; isolate failures from stock saves."""

    def __init__(self, repository: ObserverRepository) -> None:
        self.repository = repository
        self._observers: list[StockObserver] = []

    def attach(self, observer: StockObserver) -> None:
        """Attach once to this request's subject."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: StockObserver) -> None:
        """Detach an observer if present."""
        if observer in self._observers:
            self._observers.remove(observer)

    def check_stock(
        self, asset_id: int, available_quantity: int, reorder_threshold: int
    ) -> None:
        """Notify only when stock is at or below the threshold."""
        if available_quantity > reorder_threshold:
            return
        for observer in tuple(self._observers):
            try:
                self.repository.notify(observer, asset_id, available_quantity)
            except Exception:
                logging.getLogger(__name__).exception(
                    "Stock observer failed for %s", asset_id
                )
