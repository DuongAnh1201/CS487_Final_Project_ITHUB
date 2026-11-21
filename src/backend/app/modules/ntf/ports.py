"""Small interfaces NTF needs from other pages, so it never imports them.

PRJ supplies the real implementations; until then the ``No*`` defaults apply.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol


class ProjectMembership(Protocol):
    """Who belongs to a project (BR-16: project events go to members only)."""

    def member_ids(self, project_id: int) -> list[int]:
        """User ids of the project's members."""


class NoProjectMembership:
    """Default: no project has members."""

    def member_ids(self, project_id: int) -> list[int]:
        return []


@dataclass(frozen=True)
class ScheduledWork:
    """One piece of work for a shift summary."""

    id: int
    title: str
    due_date: date
    project: str = ""  # project name, or "" for a standalone task
    priority: str = ""  # e.g. "High"


class ScheduledWorkSource(Protocol):
    """Where a shift summary finds a user's unfinished work (FR-NTF-03)."""

    def open_work_for_user(self, user_id: int, due_on_or_before: date) -> list[ScheduledWork]:
        """Unfinished work assigned to the user and due on or before the date."""


class NoScheduledWork:
    """Default: no scheduled work."""

    def open_work_for_user(self, user_id: int, due_on_or_before: date) -> list[ScheduledWork]:
        return []


class LowStockDetails(Protocol):
    """What a low-stock email shows about the item and its order (FR-ORD-01)."""

    def low_stock_details(self, asset_id: int) -> dict[str, Any]:
        """Item name, unit, location, threshold and the open order, as email template values."""


class NoLowStockDetails:
    """Default: no details, so the low-stock email uses the general design."""

    def low_stock_details(self, asset_id: int) -> dict[str, Any]:
        return {}
