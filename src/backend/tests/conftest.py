"""Shared fixtures: in-memory app, TestClient, controllable clock, login helpers."""

from collections.abc import Callable, Iterator
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.main import create_app

ADMIN_EMAIL = "admin@sfbu.edu"
ADMIN_PASSWORD = "AdminPass123"  # permanent password set by the fixture
SA_EMAIL = "sa@sfbu.edu"
SA_PASSWORD = "AssistPass123"


class FakeClock:
    """Settable clock so tests can fast-forward time."""

    def __init__(self) -> None:
        self.now = datetime(2026, 1, 5, 9, 0, 0)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs: float) -> None:
        """Move time forward, e.g. ``clock.advance(minutes=31)``."""
        self.now += timedelta(**kwargs)


@pytest.fixture
def settings() -> Settings:
    """In-memory database, fast bcrypt."""
    return Settings(
        database_url="sqlite://", secret_key="test-secret", bcrypt_rounds=4,
        admin_email=ADMIN_EMAIL, admin_password="TempAdmin123",
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    """App with a fake clock."""
    application = create_app(settings)
    application.state.clock = FakeClock()
    return application


@pytest.fixture
def clock(app: FastAPI) -> FakeClock:
    """The app's controllable clock."""
    return app.state.clock


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """TestClient with startup run (tables created, Admin seeded)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db(app: FastAPI, client: TestClient) -> Iterator[Session]:
    """A separate DB session for assertions on stored data."""
    with app.state.database.SessionLocal() as session:
        yield session


def auth_header(token: str) -> dict[str, str]:
    """Authorization header for a token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def login(client: TestClient) -> Callable[[str, str], str]:
    """Return a function that logs in and gives back the token."""

    def _login(email: str, password: str) -> str:
        response = client.post("/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return response.json()["access_token"]

    return _login


@pytest.fixture
def admin_headers(client: TestClient, login: Callable[[str, str], str]) -> dict[str, str]:
    """Headers for the seeded Admin, after the forced password change."""
    token = login(ADMIN_EMAIL, "TempAdmin123")
    response = client.post(
        "/auth/change-password", headers=auth_header(token),
        json={"current_password": "TempAdmin123", "new_password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return auth_header(token)


@pytest.fixture
def sa_headers(
    client: TestClient, admin_headers: dict[str, str], login: Callable[[str, str], str]
) -> dict[str, str]:
    """Headers for a Student Assistant created by the Admin (password already changed)."""
    response = client.post("/users", headers=admin_headers, json={
        "full_name": "Sam Assistant", "email": SA_EMAIL, "school_id": "SA-001",
        "role": "STUDENT_ASSISTANT", "temporary_password": "TempSa12345",
    })
    assert response.status_code == 201, response.text
    token = login(SA_EMAIL, "TempSa12345")
    client.post("/auth/change-password", headers=auth_header(token),
                json={"current_password": "TempSa12345", "new_password": SA_PASSWORD})
    return auth_header(token)
