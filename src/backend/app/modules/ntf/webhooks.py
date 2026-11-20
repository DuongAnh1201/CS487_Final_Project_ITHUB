"""Resend webhook signature verification (Svix scheme)."""

import json
from abc import ABC, abstractmethod
from typing import Any

from svix.webhooks import Webhook, WebhookVerificationError

from app.core.exceptions import AuthenticationError

MSG_BAD_SIGNATURE = "Invalid webhook signature."


class WebhookVerifier(ABC):
    """Checks that a webhook really comes from the provider and returns its payload."""

    @abstractmethod
    def verify(self, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
        """Return the parsed payload or raise AuthenticationError."""


class SvixWebhookVerifier(WebhookVerifier):
    """Verifies ``svix-id`` / ``svix-timestamp`` / ``svix-signature`` (5-minute tolerance)."""

    def __init__(self, secret: str) -> None:
        self._secret = secret

    def verify(self, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
        """Return the payload or raise AuthenticationError for a bad, missing or stale signature."""
        try:
            Webhook(self._secret).verify(body, headers)
            return json.loads(body)
        except (WebhookVerificationError, ValueError) as exc:
            raise AuthenticationError(MSG_BAD_SIGNATURE) from exc
