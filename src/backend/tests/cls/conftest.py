"""An in-memory AST adapter exercises the explicit #55 boundary."""

import pytest
from app.core.exceptions import NotFoundError
from app.modules.cls.integrations import AssetItem, AssetLocation, get_asset_gateway


class FakeAssets:
    """Read-only AST contract with test-controlled inventory."""

    def __init__(self):
        self.locations = {
            i: AssetLocation(i, "Main" if i < 3 else "Annex", str(200 + i))
            for i in range(1, 5)
        }
        self.items = {
            1: AssetItem(1, "Desktop", "AVAILABLE"),
            2: AssetItem(2, "Desktop", "AVAILABLE"),
            3: AssetItem(3, "Monitor", "AVAILABLE"),
            4: AssetItem(4, "Laptop", "AVAILABLE"),
            5: AssetItem(5, "Desktop", "RETIRED"),
            6: AssetItem(6, "Desktop", "ON_LOAN"),
        }

    def find_item(self, item_id):
        if item_id not in self.items:
            raise NotFoundError("Item not found.")
        return self.items[item_id]

    def find_location(self, location_id):
        if location_id not in self.locations:
            raise NotFoundError("Location not found.")
        return self.locations[location_id]

    def find_location_by_room(self, building, room):
        return next(
            (
                loc
                for loc in self.locations.values()
                if loc.building == building and loc.room == room
            ),
            None,
        )


@pytest.fixture
def assets(app):
    gateway = FakeAssets()
    app.dependency_overrides[get_asset_gateway] = lambda: gateway
    return gateway


@pytest.fixture
def room(client, admin_headers, assets):
    response = client.post(
        "/classrooms",
        headers=admin_headers,
        json={"location_id": 1, "capacity": 30, "room_type": "COMPUTER_LAB"},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def equipment(client, sa_headers, room):
    response = client.post(
        f"/classrooms/{room['id']}/equipment", headers=sa_headers, json={"item_id": 1}
    )
    assert response.status_code == 201, response.text
    return response.json()
