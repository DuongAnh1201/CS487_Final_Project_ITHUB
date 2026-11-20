"""Application settings (pydantic-settings). Override any field with an env var."""

import json
from pathlib import Path
from typing import Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the backend."""

    model_config = SettingsConfigDict(env_prefix="ITHUB_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./ithub.db"
    secret_key: str = "change-me-in-production"
    session_timeout_minutes: int = 30  # NFR-USR-02: idle expiry
    max_failed_logins: int = 5  # FR-USR-07
    lockout_minutes: int = 15  # FR-USR-07
    bcrypt_rounds: int = 12

    # Browser origins allowed to call the API (CORS). ITHUB_CORS_ORIGINS: comma-separated or JSON list.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    # Google sign-in stays disabled until at least one client id is set.
    # ITHUB_GOOGLE_CLIENT_IDS accepts a comma-separated list or a JSON list.
    google_client_ids: Annotated[list[str], NoDecode] = []
    google_hosted_domain: str | None = None  # e.g. "sfbu.edu"; None accepts any Google account

    # Static frontend served at /app on the same origin as the API (no CORS needed).
    # ITHUB_FRONTEND_DIR overrides it; a folder that does not exist turns the mount off.
    frontend_dir: Path | None = Path(__file__).resolve().parents[3] / "frontend"

    # First-start Admin account (seeded only when no user exists).
    admin_full_name: str = "System Administrator"
    admin_email: str = "admin@sfbu.edu"
    admin_school_id: str = "ADMIN-0001"
    # None => a random temporary password is generated and logged once at first start.
    admin_password: str | None = None

    # Email through Resend stays off until both the API key and the sender are set.
    resend_api_key: SecretStr | None = None  # secret: never logged or returned by the API
    email_from: str | None = None  # e.g. "IT Inventory Tracker <noreply@yourdomain>"
    email_reply_to: str | None = None
    resend_webhook_secret: SecretStr | None = None  # enables POST /webhooks/resend
    app_base_url: str = "http://localhost:5173"  # frontend origin used in email links

    @staticmethod
    def _split_list(value: object, strip_slash: bool = False) -> object:
        """Accept a comma-separated string or a JSON list."""
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            parts = [part.strip() for part in text.split(",") if part.strip()]
            return [p.rstrip("/") for p in parts] if strip_slash else parts
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        return cls._split_list(value, strip_slash=True)

    @field_validator("google_client_ids", mode="before")
    @classmethod
    def _split_client_ids(cls, value: object) -> object:
        return cls._split_list(value)

    @field_validator("google_hosted_domain", mode="before")
    @classmethod
    def _blank_domain_is_none(cls, value: object) -> object:
        return value or None

    @field_validator("resend_api_key", "email_from", "email_reply_to", "resend_webhook_secret", mode="before")
    @classmethod
    def _blank_is_none(cls, value: object) -> object:
        return value or None

    @property
    def email_enabled(self) -> bool:
        """True when Resend has an API key and a sender address."""
        return bool(self.resend_api_key and self.email_from)

    @property
    def google_enabled(self) -> bool:
        """True when at least one Google client id is configured."""
        return bool(self.google_client_ids)
