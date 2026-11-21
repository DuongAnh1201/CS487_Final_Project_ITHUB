"""Google sign-in token verification (kept behind an interface so tests need no network).

Two strategies verify the token the login page sends to ``POST /auth/google``:
Google Identity Services ID tokens (``GoogleIdTokenVerifier``) or Firebase Authentication
ID tokens from its Google provider (``FirebaseIdTokenVerifier``). ``GoogleVerifierFactory``
picks one from the settings.
"""

from abc import ABC, abstractmethod
from typing import Any

from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel

from app.core.config import Settings


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


class FirebaseIdTokenVerifier(GoogleTokenVerifier):
    """Firebase Authentication ID tokens, accepted only for one project and the Google provider."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id

    def verify(self, id_token: str) -> GoogleIdentity:
        """Check signature, expiry and audience with Firebase's public keys, then the claims."""
        try:
            claims = google_id_token.verify_firebase_token(
                id_token, google_requests.Request(), audience=self.project_id)
            return self.identity_from(claims)
        except (ValueError, KeyError, GoogleAuthError) as exc:
            raise GoogleTokenError(str(exc)) from exc

    def identity_from(self, claims: dict[str, Any]) -> GoogleIdentity:
        """Map verified Firebase claims to the identity the sign-in rules use.

        ``sub`` is the Google account id from ``firebase.identities``, not the Firebase uid, so an
        account first linked through Google Identity Services keeps matching. Firebase tokens have
        no ``hd`` claim; the email's domain stands in for it (the email must be verified).
        """
        if claims.get("iss") != f"https://securetoken.google.com/{self.project_id}":
            raise GoogleTokenError("Token was issued for another Firebase project.")
        firebase = claims.get("firebase") or {}
        if firebase.get("sign_in_provider") != "google.com":
            raise GoogleTokenError("Only the Google provider is accepted.")
        google_ids = (firebase.get("identities") or {}).get("google.com") or []
        if not google_ids:
            raise GoogleTokenError("Token has no Google account id.")
        email = claims["email"]
        return GoogleIdentity(
            sub=str(google_ids[0]), email=email,
            email_verified=bool(claims.get("email_verified", False)),
            hd=email.rpartition("@")[2] or None, name=claims.get("name"))


class GoogleVerifierFactory:
    """Chooses the sign-in token verifier from the settings (Factory)."""

    @staticmethod
    def from_settings(settings: Settings) -> GoogleTokenVerifier | None:
        """Firebase when a Firebase project is configured, else Google client ids, else off."""
        if settings.firebase_enabled:
            return FirebaseIdTokenVerifier(settings.firebase_project_id)
        if settings.google_client_ids:
            return GoogleIdTokenVerifier(settings.google_client_ids)
        return None
