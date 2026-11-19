"""Small AST boundary until #55 supplies AssetManager (DD-CLS-01)."""

from dataclasses import dataclass
from typing import Protocol
from fastapi import Request
from app.core.exceptions import ConflictError


@dataclass(frozen=True)
class AssetItem:
    """Item information owned by AST; CLS never changes its inventory status."""

    id: int
    category: str
    status: str


@dataclass(frozen=True)
class AssetLocation:
    """AST location information used for classroom names and registrar lookup."""

    id: int
    building: str
    room: str


class AssetGateway(Protocol):
    """Adapt AssetManager lookups; no duplicate shared models or storage."""

    def find_item(self, item_id: int) -> AssetItem: ...
    def find_location(self, location_id: int) -> AssetLocation: ...
    def find_location_by_room(
        self, building: str, room: str
    ) -> AssetLocation | None: ...


class UnavailableAssetGateway:
    """Fail explicitly until the application provides the #55 adapter."""

    def find_item(self, item_id: int) -> AssetItem:
        raise ConflictError("Asset service is not configured.")

    def find_location(self, location_id: int) -> AssetLocation:
        raise ConflictError("Asset service is not configured.")

    def find_location_by_room(self, building: str, room: str) -> AssetLocation | None:
        raise ConflictError("Asset service is not configured.")


def get_asset_gateway(request: Request) -> AssetGateway:
    """Inject an AST adapter via app state or FastAPI dependency override."""
    return (
        getattr(request.app.state, "asset_gateway", None) or UnavailableAssetGateway()
    )
