"""RPT fixtures: these tests jump weeks ahead, so sessions must not idle out."""

import pytest

from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="sqlite://", secret_key="test-secret", bcrypt_rounds=4,
        admin_email="admin@sfbu.edu", admin_password="TempAdmin123",
        session_timeout_minutes=10**6,
    )
