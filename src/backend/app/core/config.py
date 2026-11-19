"""Application settings (pydantic-settings). Override any field with an env var."""

import json
from typing import Annotated

from pydantic import field_validator
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

    # Google sign-in stays disabled until at least one client id is set.
    # ITHUB_GOOGLE_CLIENT_IDS accepts a comma-separated list or a JSON list.
    google_client_ids: Annotated[list[str], NoDecode] = []
    google_hosted_domain: str | None = None  # e.g. "sfbu.edu"; None accepts any Google account

    # First-start Admin account (seeded only when no user exists).
    admin_full_name: str = "System Administrator"
    admin_email: str = "admin@sfbu.edu"
    admin_school_id: str = "ADMIN-0001"
    admin_password: str = "ChangeMe12345"

    @field_validator("google_client_ids", mode="before")
    @classmethod
    def _split_client_ids(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @field_validator("google_hosted_domain", mode="before")
    @classmethod
    def _blank_domain_is_none(cls, value: object) -> object:
        return value or None

    @property
    def google_enabled(self) -> bool:
        """True when at least one Google client id is configured."""
        return bool(self.google_client_ids)
