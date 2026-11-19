"""USR rules: SP4 §11.1 (Auth Service, User Manager, Access Control) and FR-USR-*."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.usr.models import User, UserStatus
from app.shared.audit import AuditRecord
from tests.conftest import (
    ADMIN_EMAIL, ADMIN_PASSWORD, SA_EMAIL, SA_PASSWORD, FakeClock, auth_header,
)

NEW_USER = {
    "full_name": "Pat Lee", "email": "pat@sfbu.edu", "school_id": "SA-002",
    "role": "STUDENT_ASSISTANT", "temporary_password": "TempPass123",
}


def attempt(client: TestClient, email: str, password: str):
    return client.post("/auth/login", json={"email": email, "password": password})


# ---- US-USR-01 login / logout (Auth Service) -------------------------------

def test_login_success_returns_token_and_updates_last_login(client, sa_headers, db):
    r = attempt(client, SA_EMAIL, SA_PASSWORD)
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["must_change_password"] is False
    assert "password_hash" not in body["user"]
    assert db.query(User).filter_by(email=SA_EMAIL).one().last_login_at is not None


def test_wrong_password_message(client, sa_headers):
    r = attempt(client, SA_EMAIL, "WrongPass123")
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid email or password."}


def test_unknown_email_same_message(client):
    r = attempt(client, "nobody@sfbu.edu", "WrongPass123")
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password."


def test_deactivated_account_gets_generic_message(client, admin_headers, sa_headers):
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    client.patch(f"/users/{sa_id}", headers=admin_headers, json={"status": "INACTIVE"})
    r = attempt(client, SA_EMAIL, SA_PASSWORD)
    assert (r.status_code, r.json()["detail"]) == (401, "Invalid email or password.")


def test_lock_after_five_failures_then_unlock_after_15_minutes(client, sa_headers, clock: FakeClock):
    for _ in range(5):
        assert attempt(client, SA_EMAIL, "WrongPass123").json()["detail"] == "Invalid email or password."
    locked = attempt(client, SA_EMAIL, SA_PASSWORD)  # correct password still refused
    assert (locked.status_code, locked.json()["detail"]) == (
        401, "Account locked. Try again in 15 minutes.")
    clock.advance(minutes=14)
    assert attempt(client, SA_EMAIL, SA_PASSWORD).status_code == 401
    clock.advance(minutes=2)
    assert attempt(client, SA_EMAIL, SA_PASSWORD).status_code == 200


def test_four_failures_do_not_lock_and_success_resets_counter(client, sa_headers):
    for _ in range(4):
        attempt(client, SA_EMAIL, "WrongPass123")
    assert attempt(client, SA_EMAIL, SA_PASSWORD).status_code == 200
    for _ in range(4):
        attempt(client, SA_EMAIL, "WrongPass123")
    assert attempt(client, SA_EMAIL, SA_PASSWORD).status_code == 200


def test_session_expires_after_30_idle_minutes(client, sa_headers, clock: FakeClock):
    clock.advance(minutes=31)
    r = client.get("/auth/me", headers=sa_headers)
    assert (r.status_code, r.json()["detail"]) == (401, "Session expired. Please log in again.")


def test_activity_keeps_session_alive(client, sa_headers, clock: FakeClock):
    for _ in range(3):
        clock.advance(minutes=20)
        assert client.get("/auth/me", headers=sa_headers).status_code == 200


def test_missing_token_requires_login(client):
    r = client.get("/auth/me")
    assert (r.status_code, r.json()["detail"]) == (401, "Please log in to continue.")


def test_logout_ends_session(client, sa_headers):
    assert client.post("/auth/logout", headers=sa_headers).status_code == 200
    assert client.get("/auth/me", headers=sa_headers).status_code == 401


def test_access_end_date_deactivates_account(client, admin_headers, clock: FakeClock, db):
    client.post("/users", headers=admin_headers,
                json={**NEW_USER, "access_end_date": "2026-01-06"})
    clock.advance(days=3)
    assert attempt(client, "pat@sfbu.edu", "TempPass123").status_code == 401
    assert db.query(User).filter_by(email="pat@sfbu.edu").one().status == UserStatus.INACTIVE


# ---- Temporary passwords (FR-USR-09) ---------------------------------------

def test_seeded_admin_exists_and_must_change_password(client, login):
    r = attempt(client, ADMIN_EMAIL, "TempAdmin123")
    assert r.status_code == 200 and r.json()["must_change_password"] is True


def test_temporary_password_blocks_other_endpoints_until_changed(client):
    token = attempt(client, ADMIN_EMAIL, "TempAdmin123").json()["access_token"]
    headers = auth_header(token)
    assert client.get("/users", headers=headers).status_code == 403
    r = client.post("/auth/change-password", headers=headers, json={
        "current_password": "TempAdmin123", "new_password": ADMIN_PASSWORD})
    assert (r.status_code, r.json()["message"]) == (200, "Password changed.")
    assert client.get("/users", headers=headers).status_code == 200


# ---- US-USR-04 create account (User Manager) --------------------------------

def test_admin_creates_active_account_with_forced_change(client, admin_headers):
    r = client.post("/users", headers=admin_headers, json=NEW_USER)
    assert r.status_code == 201
    assert r.json()["status"] == "ACTIVE" and r.json()["must_change_password"] is True
    assert attempt(client, "pat@sfbu.edu", "TempPass123").json()["must_change_password"] is True


def test_duplicate_email_or_school_id_rejected(client, admin_headers):
    client.post("/users", headers=admin_headers, json=NEW_USER)
    msg = "An account with this email or school ID already exists."
    same_email = client.post("/users", headers=admin_headers,
                             json={**NEW_USER, "email": "PAT@sfbu.edu", "school_id": "X"})
    same_id = client.post("/users", headers=admin_headers,
                          json={**NEW_USER, "email": "other@sfbu.edu"})
    assert (same_email.status_code, same_email.json()["detail"]) == (409, msg)
    assert (same_id.status_code, same_id.json()["detail"]) == (409, msg)


def test_password_rule_on_create(client, admin_headers):
    msg = "Password must be at least 10 characters and include letters and digits."
    for bad in ("Short1a", "onlyletterslong", "1234567890123"):
        r = client.post("/users", headers=admin_headers, json={**NEW_USER, "temporary_password": bad})
        assert (r.status_code, r.json()["detail"]) == (422, msg), bad


# ---- US-USR-02 change own password ------------------------------------------

def test_change_own_password(client, sa_headers):
    r = client.post("/auth/change-password", headers=sa_headers,
                    json={"current_password": SA_PASSWORD, "new_password": "NewPassword99"})
    assert r.status_code == 200
    assert attempt(client, SA_EMAIL, SA_PASSWORD).status_code == 401
    assert attempt(client, SA_EMAIL, "NewPassword99").status_code == 200


def test_change_own_password_rules(client, sa_headers):
    weak = client.post("/auth/change-password", headers=sa_headers,
                       json={"current_password": SA_PASSWORD, "new_password": "weak"})
    assert weak.json()["detail"] == (
        "Password must be at least 10 characters and include letters and digits.")
    wrong = client.post("/auth/change-password", headers=sa_headers,
                        json={"current_password": "WrongPass123", "new_password": "NewPassword99"})
    assert (wrong.status_code, wrong.json()["detail"]) == (422, "Current password is incorrect.")


# ---- US-USR-03 reset password ------------------------------------------------

def test_admin_reset_password_forces_change_and_ends_sessions(client, admin_headers, sa_headers):
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    r = client.post(f"/users/{sa_id}/reset-password", headers=admin_headers,
                    json={"temporary_password": "ResetPass123"})
    assert r.status_code == 200 and r.json()["must_change_password"] is True
    assert client.get("/auth/me", headers=sa_headers).status_code == 401
    assert attempt(client, SA_EMAIL, "ResetPass123").json()["must_change_password"] is True


def test_reset_password_rule_and_unknown_user(client, admin_headers, sa_headers):
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    weak = client.post(f"/users/{sa_id}/reset-password", headers=admin_headers,
                       json={"temporary_password": "weak"})
    assert weak.status_code == 422
    missing = client.post("/users/999/reset-password", headers=admin_headers,
                          json={"temporary_password": "ResetPass123"})
    assert (missing.status_code, missing.json()["detail"]) == (404, "User not found.")


# ---- US-USR-05 role / status; BR-USR-06 --------------------------------------

def test_change_role_and_status_and_filter(client, admin_headers, sa_headers):
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    r = client.patch(f"/users/{sa_id}", headers=admin_headers, json={"role": "ADMIN"})
    assert r.json()["role"] == "ADMIN"
    client.patch(f"/users/{sa_id}", headers=admin_headers, json={"status": "INACTIVE"})
    inactive = client.get("/users?status=INACTIVE", headers=admin_headers).json()
    assert [u["id"] for u in inactive] == [sa_id]
    assert len(client.get("/users?role=ADMIN", headers=admin_headers).json()) == 2


def test_deactivation_ends_sessions_and_reactivation_allows_login(client, admin_headers, sa_headers):
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    client.patch(f"/users/{sa_id}", headers=admin_headers, json={"status": "INACTIVE"})
    assert client.get("/auth/me", headers=sa_headers).status_code == 401
    client.patch(f"/users/{sa_id}", headers=admin_headers, json={"status": "ACTIVE"})
    assert attempt(client, SA_EMAIL, SA_PASSWORD).status_code == 200


def test_last_active_admin_cannot_be_demoted_or_deactivated(client, admin_headers):
    admin_id = client.get("/auth/me", headers=admin_headers).json()["id"]
    msg = "At least one active Admin is required."
    for body in ({"role": "STUDENT_ASSISTANT"}, {"status": "INACTIVE"}):
        r = client.patch(f"/users/{admin_id}", headers=admin_headers, json=body)
        assert (r.status_code, r.json()["detail"]) == (409, msg)


def test_admin_can_be_demoted_when_another_active_admin_exists(client, admin_headers, sa_headers):
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    client.patch(f"/users/{sa_id}", headers=admin_headers, json={"role": "ADMIN"})
    admin_id = client.get("/auth/me", headers=admin_headers).json()["id"]
    r = client.patch(f"/users/{admin_id}", headers=admin_headers, json={"role": "STUDENT_ASSISTANT"})
    assert r.status_code == 200


def test_no_delete_endpoint(client, admin_headers):
    assert client.delete("/users/1", headers=admin_headers).status_code == 405


# ---- US-USR-06 Access Control -----------------------------------------------

def test_student_assistant_cannot_manage_users(client, sa_headers):
    for r in (
        client.get("/users", headers=sa_headers),
        client.post("/users", headers=sa_headers, json=NEW_USER),
        client.patch("/users/1", headers=sa_headers, json={"role": "ADMIN"}),
        client.post("/users/1/reset-password", headers=sa_headers,
                    json={"temporary_password": "ResetPass123"}),
    ):
        assert (r.status_code, r.json()["detail"]) == (403, "Access denied.")


def test_user_endpoints_require_login(client):
    assert client.get("/users").json()["detail"] == "Please log in to continue."


# ---- NFR-USR-01 / FR-USR-06 --------------------------------------------------

def test_passwords_are_stored_as_bcrypt_hashes(client, sa_headers, db: Session):
    stored = db.query(User).filter_by(email=SA_EMAIL).one().password_hash
    assert stored.startswith("$2") and SA_PASSWORD not in stored


def test_changes_are_audited_without_secrets(client, admin_headers, sa_headers, db: Session):
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    client.patch(f"/users/{sa_id}", headers=admin_headers, json={"role": "ADMIN"})
    actions = [a.action for a in db.query(AuditRecord).order_by(AuditRecord.id)]
    assert {"CREATE", "UPDATE", "LOGIN", "CHANGE_PASSWORD"} <= set(actions)
    update = db.query(AuditRecord).filter_by(action="UPDATE").one()
    assert update.old_value["role"] == "STUDENT_ASSISTANT" and update.new_value["role"] == "ADMIN"
    assert update.actor_id is not None and update.entity_id == str(sa_id)
    assert all("hash" not in str(a.new_value).lower() and SA_PASSWORD not in str(a.new_value)
               for a in db.query(AuditRecord))


def test_failed_login_is_not_audited(client, sa_headers, db: Session):
    before = db.query(AuditRecord).count()
    attempt(client, SA_EMAIL, "WrongPass123")
    assert db.query(AuditRecord).count() == before
