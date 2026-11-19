"""Google ID-token verification (kept behind an interface so tests need no network)."""

from abc import ABC, abstractmethod

from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel


class GoogleTokenError(Exception):
    """The ID token is invalid, expired or not meant for this app."""


class GoogleIdentity(BaseModel):
    """The verified claims we use."""

    sub: str
    email: str
    email_verified: bool = False
    hd: str | None = None
    name: str | None = None

    def is_acceptable(self, hosted_domain: str | None) -> bool:
        """Email is verified and, when a hosted domain is configured, belongs to it."""
        if not self.email_verified:
            return False
        return hosted_domain is None or (self.hd or "").lower() == hosted_domain.lower()


class GoogleTokenVerifier(ABC):
    """Turns a Google ID token into a verified identity."""

    @abstractmethod
    def verify(self, id_token: str) -> GoogleIdentity:
        """Return the identity, or raise GoogleTokenError."""


class GoogleIdTokenVerifier(GoogleTokenVerifier):
    """Real verifier: signature, expiry, issuer and audience via the google-auth SDK."""

    def __init__(self, client_ids: list[str]) -> None:
        self.client_ids = client_ids

    def verify(self, id_token: str) -> GoogleIdentity:
        """Verify with Google's public keys; ``aud`` must be one of the client ids."""
        try:
            claims = google_id_token.verify_oauth2_token(
                id_token, google_requests.Request(), audience=self.client_ids)
            return GoogleIdentity(
                sub=claims["sub"], email=claims["email"],
                email_verified=bool(claims.get("email_verified", False)),
                hd=claims.get("hd"), name=claims.get("name"))
        except (ValueError, KeyError, GoogleAuthError) as exc:
            raise GoogleTokenError(str(exc)) from exc
