"""First-Admin seeding: no public default password."""

import logging

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.modules.usr.service import check_password_rule

LOGGER = "app.modules.usr.service"


def make_app(**overrides):
    return create_app(Settings(**{"database_url": "sqlite://", "bcrypt_rounds": 4, **overrides}))


def logged_passwords(caplog) -> list[str]:
    return [r.getMessage().split("Initial admin password: ")[1]
            for r in caplog.records if "Initial admin password: " in r.getMessage()]


def test_no_default_admin_password():
    assert Settings().admin_password is None


def test_unset_password_generates_and_logs_a_random_one_once(caplog):
    caplog.set_level(logging.WARNING, logger=LOGGER)
    with TestClient(make_app()) as client:
        (password,) = logged_passwords(caplog)
        check_password_rule(password)  # satisfies BR-USR-03
        assert "ChangeMe12345" not in caplog.text
        login = client.post("/auth/login", json={"email": "admin@sfbu.edu", "password": password})
        assert login.status_code == 200 and login.json()["must_change_password"] is True
        old = client.post("/auth/login", json={"email": "admin@sfbu.edu", "password": "ChangeMe12345"})
        assert old.status_code == 401


def test_generated_passwords_differ_between_installs(caplog):
    caplog.set_level(logging.WARNING, logger=LOGGER)
    for _ in range(2):
        with TestClient(make_app()):
            pass
    first, second = logged_passwords(caplog)
    assert first != second


def test_configured_password_is_used_and_not_logged(caplog):
    caplog.set_level(logging.WARNING, logger=LOGGER)
    with TestClient(make_app(admin_password="Configured123")) as client:
        assert logged_passwords(caplog) == []
        login = client.post("/auth/login", json={"email": "admin@sfbu.edu", "password": "Configured123"})
        assert login.status_code == 200 and login.json()["must_change_password"] is True


def test_nothing_is_logged_when_users_already_exist(caplog, tmp_path):
    url = f"sqlite:///{tmp_path / 'ithub.db'}"
    with TestClient(make_app(database_url=url)):
        pass
    caplog.clear()
    caplog.set_level(logging.WARNING, logger=LOGGER)
    with TestClient(make_app(database_url=url)):
        pass
    assert logged_passwords(caplog) == []
