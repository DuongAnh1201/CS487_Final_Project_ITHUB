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

    # Browser origins allowed to call the API (CORS). ITHUB_CORS_ORIGINS: comma-separated or JSON list.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    # First-start Admin account (seeded only when no user exists).
    admin_full_name: str = "System Administrator"
    admin_email: str = "admin@sfbu.edu"
    admin_school_id: str = "ADMIN-0001"
    admin_password: str = "ChangeMe12345"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [part.strip().rstrip("/") for part in text.split(",") if part.strip()]
        return value
