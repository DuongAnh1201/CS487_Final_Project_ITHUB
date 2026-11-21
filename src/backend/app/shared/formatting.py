"""Human-readable values for messages and emails (shared by every page)."""

from datetime import date, datetime
from enum import Enum


def label(value: Enum | str | None) -> str:
    """``PARTIALLY_ARRIVED`` → ``Partially arrived``; empty → ``""``."""
    if value is None:
        return ""
    text = str(value.value if isinstance(value, Enum) else value).replace("_", " ").lower()
    return text[:1].upper() + text[1:]


def human_date(value: date | datetime | None, empty: str = "—") -> str:
    """``Nov 25, 2026``, or ``empty`` when there is no date."""
    if value is None:
        return empty
    return f"{value:%b} {value.day}, {value.year}"


def long_date(value: date) -> str:
    """``Tuesday, November 25, 2026``."""
    return f"{value:%A, %B} {value.day}, {value.year}"


def human_datetime(value: datetime | None, empty: str = "—") -> str:
    """``Nov 25, 2026, 2:05 PM UTC`` (stored times are UTC)."""
    if value is None:
        return empty
    hour = value.hour % 12 or 12
    return f"{human_date(value)}, {hour}:{value:%M} {'AM' if value.hour < 12 else 'PM'} UTC"
