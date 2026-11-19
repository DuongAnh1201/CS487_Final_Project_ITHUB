"""Time source. Storage convention: naive UTC datetimes."""

from collections.abc import Callable
from datetime import UTC, datetime

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    """Current UTC time as a naive datetime."""
    return datetime.now(UTC).replace(tzinfo=None)
