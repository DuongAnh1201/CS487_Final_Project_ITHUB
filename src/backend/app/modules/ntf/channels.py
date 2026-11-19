"""Email delivery behind an interface (FR-NTF-07)."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmailChannel(ABC):
    """Sends one email. Raise any exception to report a delivery failure."""

    @abstractmethod
    def send(self, to_address: str, subject: str, body: str) -> None:
        """Deliver the message or raise."""


class LoggingEmailChannel(EmailChannel):
    """Default channel: logs the email instead of sending it (no SMTP configured)."""

    def send(self, to_address: str, subject: str, body: str) -> None:
        """Log the message."""
        logger.info("Email to %s: %s", to_address, subject)
