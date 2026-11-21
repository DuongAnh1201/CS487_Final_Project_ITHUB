"""Google sign-in (issue #62): FR-USR-01, NFR-USR-03/04, FR-USR-07. No network is used."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from google.auth.exceptions import GoogleAuthError

from app.core.config import Settings
from app.main import create_app
from app.modules.usr.google import (
    GoogleIdentity,
    GoogleIdTokenVerifier,
    GoogleTokenError,
    GoogleTokenVerifier,
)
from app.modules.usr.models import User
from app.shared.audit import AuditRecord
from tests.conftest import SA_EMAIL, FakeClock, auth_header


class FakeGoogleTokenVerifier(GoogleTokenVerifier):
    """Maps a token string to a prepared identity; unknown tokens are invalid."""

    def __init__(self) -> None:
        self.identities: dict[str, GoogleIdentity] = {}

    def add(self, token: str, **claims) -> str:
        data = {"sub": "sub-1", "email": SA_EMAIL, "email_verified": True, "hd": "sfbu.edu", **claims}
        self.identities[token] = GoogleIdentity(**data)
        return token

    def verify(self, id_token: str) -> GoogleIdentity:
        if id_token not in self.identities:
            raise GoogleTokenError("bad token")
        return self.identities[id_token]


@pytest.fixture
def settings() -> Settings:
    """Overrides the shared fixture: Google enabled for sfbu.edu."""
    return Settings(
        database_url="sqlite://", secret_key="test-secret", bcrypt_rounds=4,
        admin_email="admin@sfbu.edu", admin_password="TempAdmin123",
        google_client_ids=["client-1.apps.googleusercontent.com"], google_hosted_domain="sfbu.edu",
    )


@pytest.fixture
def google(app) -> FakeGoogleTokenVerifier:
    fake = FakeGoogleTokenVerifier()
    app.state.google_verifier = fake
    return fake


def sign_in(client: TestClient, token: str):
    return client.post("/auth/google", json={"id_token": token})


def test_disabled_until_client_ids_are_set():
    app = create_app(Settings(database_url="sqlite://", bcrypt_rounds=4))
    with TestClient(app) as client:
        r = sign_in(client, "anything")
        assert (r.status_code, r.json()["detail"]) == (503, "Google sign-in is not configured.")
        assert client.get("/auth/config").json() == {
            "google_enabled": False, "google_provider": None, "google_client_id": None, "firebase": None}


def test_config_when_enabled(client):
    assert client.get("/auth/config").json() == {
        "google_enabled": True, "google_provider": "google",
        "google_client_id": "client-1.apps.googleusercontent.com", "firebase": None}


def test_existing_active_user_gets_a_working_session(client, sa_headers, google):
    r = sign_in(client, google.add("t1"))
    assert r.status_code == 200
    body = r.json()
    assert body["must_change_password"] is False and body["user"]["email"] == SA_EMAIL
    me = client.get("/auth/me", headers=auth_header(body["access_token"]))
    assert me.status_code == 200 and me.json()["email"] == SA_EMAIL


def test_email_match_is_case_insensitive(client, sa_headers, google):
    assert sign_in(client, google.add("t1", email=SA_EMAIL.upper())).status_code == 200


def test_google_session_is_not_blocked_by_a_temporary_password(client, admin_headers, google):
    client.post("/users", headers=admin_headers, json={
        "full_name": "New Person", "email": "new@sfbu.edu", "school_id": "N-1",
        "role": "STUDENT_ASSISTANT", "temporary_password": "TempPass123"})
    token = sign_in(client, google.add("t2", email="new@sfbu.edu", sub="sub-new")).json()["access_token"]
    # past the "change your password" gate: the SA is stopped only by the Admin-only role check
    assert client.get("/users", headers=auth_header(token)).json()["detail"] == "Access denied."
    # the password route still forces the change
    pw = client.post("/auth/login", json={"email": "new@sfbu.edu", "password": "TempPass123"}).json()
    assert pw["must_change_password"] is True
    blocked = client.get("/users", headers=auth_header(pw["access_token"]))
    assert blocked.json()["detail"] == "Password change required."


@pytest.mark.parametrize("claims", [
    {"email": "stranger@sfbu.edu"},
    {"hd": "other.edu"},
    {"hd": None},
    {"email_verified": False},
])
def test_rejected_identities_get_the_generic_message(client, sa_headers, google, claims):
    r = sign_in(client, google.add("t", **claims))
    assert (r.status_code, r.json()["detail"]) == (401, "Invalid email or password.")


def test_invalid_token_gets_the_generic_message(client, sa_headers, google):
    r = sign_in(client, "not-a-real-token")
    assert (r.status_code, r.json()["detail"]) == (401, "Invalid email or password.")


def test_unknown_email_does_not_create_an_account(client, admin_headers, google, db):
    before = db.query(User).count()
    sign_in(client, google.add("t", email="stranger@sfbu.edu"))
    assert db.query(User).count() == before


def test_deactivated_account_is_refused(client, admin_headers, sa_headers, google):
    sa_id = client.get("/auth/me", headers=sa_headers).json()["id"]
    client.patch(f"/users/{sa_id}", headers=admin_headers, json={"status": "INACTIVE"})
    r = sign_in(client, google.add("t"))
    assert (r.status_code, r.json()["detail"]) == (401, "Invalid email or password.")


def test_locked_account_gets_the_lock_message(client, sa_headers, google):
    for _ in range(5):
        client.post("/auth/login", json={"email": SA_EMAIL, "password": "WrongPass123"})
    r = sign_in(client, google.add("t"))
    assert (r.status_code, r.json()["detail"]) == (401, "Account locked. Try again in 15 minutes.")


def test_ended_access_is_refused(client, admin_headers, google, clock: FakeClock):
    client.post("/users", headers=admin_headers, json={
        "full_name": "Temp", "email": "temp@sfbu.edu", "school_id": "T-1", "role": "STUDENT_ASSISTANT",
        "temporary_password": "TempPass123", "access_end_date": "2026-01-06"})
    clock.advance(days=3)
    assert sign_in(client, google.add("t", email="temp@sfbu.edu")).status_code == 401


def test_sub_is_stored_then_must_match(client, sa_headers, google, db):
    assert sign_in(client, google.add("a", sub="sub-A")).status_code == 200
    assert db.query(User).filter_by(email=SA_EMAIL).one().google_sub == "sub-A"
    assert sign_in(client, google.add("b", sub="sub-A")).status_code == 200
    r = sign_in(client, google.add("c", sub="sub-B"))
    assert (r.status_code, r.json()["detail"]) == (401, "Invalid email or password.")


def test_login_is_audited_with_method(client, sa_headers, google, db):
    sign_in(client, google.add("t"))
    methods = [a.new_value["method"] for a in db.query(AuditRecord).filter_by(action="LOGIN")]
    assert "google" in methods and "password" in methods


def test_google_session_expires_like_any_other(client, sa_headers, google, clock: FakeClock):
    token = sign_in(client, google.add("t")).json()["access_token"]
    clock.advance(minutes=31)
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


# ---- the real verifier, with the SDK call patched ------------------------------------

CLAIMS = {"sub": "123", "email": "sa@sfbu.edu", "email_verified": True, "hd": "sfbu.edu", "name": "Sam"}


def test_real_verifier_passes_client_ids_as_audience_and_maps_claims():
    verifier = GoogleIdTokenVerifier(["c1", "c2"])
    with patch("app.modules.usr.google.google_id_token.verify_oauth2_token", return_value=CLAIMS) as call:
        identity = verifier.verify("raw-token")
    assert call.call_args.args[0] == "raw-token" and call.call_args.kwargs["audience"] == ["c1", "c2"]
    assert (identity.sub, identity.email, identity.hd, identity.email_verified) == (
        "123", "sa@sfbu.edu", "sfbu.edu", True)


@pytest.mark.parametrize("error", [ValueError("Token has wrong audience"), GoogleAuthError("x")])
def test_real_verifier_turns_sdk_errors_into_token_errors(error):
    with patch("app.modules.usr.google.google_id_token.verify_oauth2_token", side_effect=error):
        with pytest.raises(GoogleTokenError):
            GoogleIdTokenVerifier(["c1"]).verify("raw-token")


def test_hosted_domain_policy():
    identity = GoogleIdentity(**CLAIMS)
    assert identity.is_acceptable("sfbu.edu") and identity.is_acceptable("SFBU.EDU")
    assert identity.is_acceptable(None)
    assert not identity.is_acceptable("other.edu")
    assert not GoogleIdentity(**{**CLAIMS, "hd": None}).is_acceptable("sfbu.edu")
    assert not GoogleIdentity(**{**CLAIMS, "email_verified": False}).is_acceptable(None)


def test_client_ids_setting_accepts_comma_or_json(monkeypatch):
    monkeypatch.setenv("ITHUB_GOOGLE_CLIENT_IDS", "a.apps, b.apps")
    assert Settings().google_client_ids == ["a.apps", "b.apps"]
    monkeypatch.setenv("ITHUB_GOOGLE_CLIENT_IDS", '["x.apps"]')
    assert Settings().google_client_ids == ["x.apps"]
    monkeypatch.setenv("ITHUB_GOOGLE_CLIENT_IDS", "")
    assert Settings().google_enabled is False
