"""Google sign-in through Firebase Authentication (#102): FR-USR-01, NFR-USR-03/04. No network."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from google.auth.exceptions import GoogleAuthError

from app.core.config import Settings
from app.main import create_app
from app.modules.usr.google import (
    FirebaseIdTokenVerifier,
    GoogleIdTokenVerifier,
    GoogleTokenError,
    GoogleVerifierFactory,
)
from app.modules.usr.models import User
from tests.conftest import SA_EMAIL, auth_header

PROJECT = "it-hub-test"
FIREBASE = dict(firebase_project_id=PROJECT, firebase_api_key="AIza-test-key", firebase_app_id="1:2:web:3")


def claims(**changes) -> dict:
    """Verified Firebase claims for a Google sign-in of the test Student Assistant."""
    data = {
        "iss": f"https://securetoken.google.com/{PROJECT}", "aud": PROJECT, "sub": "firebase-uid-1",
        "email": SA_EMAIL, "email_verified": True, "name": "Sam Assistant",
        "firebase": {"sign_in_provider": "google.com", "identities": {"google.com": ["google-sub-1"]}},
    }
    data.update(changes)
    return data


def make_settings(**changes) -> Settings:
    return Settings(database_url="sqlite://", secret_key="test-secret", bcrypt_rounds=4,
                    admin_email="admin@sfbu.edu", admin_password="TempAdmin123", **{**FIREBASE, **changes})


@pytest.fixture
def settings() -> Settings:
    """Overrides the shared fixture: Firebase sign-in for sfbu.edu."""
    return make_settings(google_hosted_domain="sfbu.edu")


def sign_in(client: TestClient, verified_claims: dict):
    """POST /auth/google with a token that Firebase's key check would accept as ``verified_claims``."""
    with patch("app.modules.usr.google.google_id_token.verify_firebase_token", return_value=verified_claims):
        return client.post("/auth/google", json={"id_token": "firebase-token"})


def test_factory_prefers_firebase_then_client_ids_then_off():
    assert isinstance(GoogleVerifierFactory.from_settings(make_settings()), FirebaseIdTokenVerifier)
    both = make_settings(google_client_ids=["c1"])
    assert isinstance(GoogleVerifierFactory.from_settings(both), FirebaseIdTokenVerifier)
    google_only = make_settings(firebase_project_id=None, google_client_ids=["c1"])
    assert isinstance(GoogleVerifierFactory.from_settings(google_only), GoogleIdTokenVerifier)
    assert GoogleVerifierFactory.from_settings(make_settings(firebase_project_id="", firebase_api_key="")) is None


def test_config_gives_the_login_page_the_public_firebase_settings(client):
    assert client.get("/auth/config").json() == {
        "google_enabled": True, "google_provider": "firebase", "google_client_id": None,
        "firebase": {"api_key": "AIza-test-key", "auth_domain": f"{PROJECT}.firebaseapp.com",
                     "project_id": PROJECT, "app_id": "1:2:web:3"},
    }


def test_existing_user_signs_in_and_is_linked_by_google_account_id(client, sa_headers, db):
    r = sign_in(client, claims())
    assert r.status_code == 200, r.text
    me = client.get("/auth/me", headers=auth_header(r.json()["access_token"]))
    assert me.json()["email"] == SA_EMAIL
    user = db.query(User).filter_by(email=SA_EMAIL).one()
    assert user.google_sub == "google-sub-1"  # the Google id, not the Firebase uid


def test_token_is_checked_against_the_project():
    verifier = FirebaseIdTokenVerifier(PROJECT)
    with patch("app.modules.usr.google.google_id_token.verify_firebase_token", return_value=claims()) as call:
        assert verifier.verify("raw").email == SA_EMAIL
    assert call.call_args.kwargs["audience"] == PROJECT
    with patch("app.modules.usr.google.google_id_token.verify_firebase_token",
               side_effect=GoogleAuthError("expired")), pytest.raises(GoogleTokenError):
        verifier.verify("raw")


@pytest.mark.parametrize("bad", [
    {"iss": "https://securetoken.google.com/another-project"},
    {"firebase": {"sign_in_provider": "password", "identities": {"email": [SA_EMAIL]}}},
    {"firebase": {"sign_in_provider": "google.com", "identities": {}}},
], ids=["other-project", "not-google-provider", "no-google-id"])
def test_tokens_from_elsewhere_are_refused(bad):
    with pytest.raises(GoogleTokenError):
        FirebaseIdTokenVerifier(PROJECT).identity_from(claims(**bad))


@pytest.mark.parametrize("bad", [
    {"email_verified": False},
    {"email": "sa@gmail.com"},
    {"email": "nobody@sfbu.edu"},
], ids=["unverified-email", "outside-school-domain", "no-it-hub-account"])
def test_sign_in_is_refused_with_the_generic_message(client, sa_headers, bad):
    r = sign_in(client, claims(**bad))
    assert (r.status_code, r.json()["detail"]) == (401, "Invalid email or password.")


def test_firebase_without_api_key_stays_off():
    app = create_app(make_settings(firebase_api_key=None))
    with TestClient(app) as client:
        assert client.get("/auth/config").json()["google_enabled"] is False
