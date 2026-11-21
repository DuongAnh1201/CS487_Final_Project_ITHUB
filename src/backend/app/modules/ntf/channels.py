"""Email delivery behind an interface (FR-NTF-07, NTF-FR-08, BR-12)."""

import logging
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from app.core.config import Settings

logger = logging.getLogger(__name__)
SEND_TIMEOUT_SECONDS = 10


class EmailChannel(ABC):
    """Sends one email. Raise any exception to report a delivery failure."""

    provider = "resend"
    real = True  # False: nothing leaves the server (the notification is marked SKIPPED)

    @abstractmethod
    def send(self, to_address: str, subject: str, body: str, html: str | None = None) -> str | None:
        """Deliver the message and return the provider message id (None if there is none), or raise."""


class LoggingEmailChannel(EmailChannel):
    """Default channel: logs the email instead of sending it (no provider configured)."""

    provider = "log"
    real = False

    def send(self, to_address: str, subject: str, body: str, html: str | None = None) -> str | None:
        """Log the message."""
        logger.info("Email to %s: %s", to_address, subject)
        return None


class ResendEmailChannel(EmailChannel):
    """Sends through the official ``resend`` SDK. The SDK keeps its key in a module global,
    so the key is set under a lock right before each call; it is never logged."""

    _lock = threading.Lock()

    def __init__(self, api_key: str, from_address: str, reply_to: str | None = None,
                 sender: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> None:
        self._api_key = api_key
        self.from_address = from_address
        self.reply_to = reply_to
        self._sender = sender  # tests inject a fake; None => resend.Emails.send

    def send(self, to_address: str, subject: str, body: str, html: str | None = None) -> str | None:
        """Send one email; the SDK raises on any provider error."""
        params: dict[str, Any] = {"from": self.from_address, "to": [to_address], "subject": subject, "text": body}
        if html:
            params["html"] = html
        if self.reply_to:
            params["reply_to"] = self.reply_to
        if self._sender is not None:
            response = self._sender(params)
        else:
            import resend
            from resend.http_client_requests import RequestsClient

            with self._lock:
                resend.api_key = self._api_key
                resend.default_http_client = RequestsClient(timeout=SEND_TIMEOUT_SECONDS)
                response = resend.Emails.send(params)  # type: ignore[arg-type]
        return response.get("id") if response else None


class EmailChannelFactory:
    """Picks the channel from configuration."""

    @staticmethod
    def from_settings(settings: Settings) -> EmailChannel:
        """Resend when the key and sender are set, otherwise the logging channel."""
        if settings.email_enabled:
            assert settings.resend_api_key is not None and settings.email_from is not None
            return ResendEmailChannel(settings.resend_api_key.get_secret_value(), settings.email_from,
                                      settings.email_reply_to)
        return LoggingEmailChannel()
