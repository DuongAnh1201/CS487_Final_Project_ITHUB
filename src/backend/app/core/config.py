"""Application settings (pydantic-settings). Override any field with an env var."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the backend."""

    model_config = SettingsConfigDict(env_prefix="ITHUB_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./ithub.db"
    secret_key: str = "change-me-in-production"
    session_timeout_minutes: int = 30  # NFR-USR-02: idle expiry
    max_failed_logins: int = 5  # FR-USR-07
    lockout_minutes: int = 15  # FR-USR-07
    bcrypt_rounds: int = 12

    # First-start Admin account (seeded only when no user exists).
    admin_full_name: str = "System Administrator"
    admin_email: str = "admin@sfbu.edu"
    admin_school_id: str = "ADMIN-0001"
    admin_password: str = "ChangeMe12345"
