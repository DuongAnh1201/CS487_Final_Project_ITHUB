"""The backend serves the static frontend at /app on the same origin as the API (#77)."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def make_client(tmp_path: Path, frontend_dir: Path | None) -> TestClient:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", bcrypt_rounds=4,
                        admin_password="TempAdmin123", frontend_dir=frontend_dir)
    return TestClient(create_app(settings))


def test_frontend_is_served_at_app_and_root_redirects_to_login(tmp_path):
    folder = tmp_path / "frontend"
    folder.mkdir()
    (folder / "login.html").write_text("<!doctype html><title>Sign in</title>")
    with make_client(tmp_path, folder) as client:
        root = client.get("/", follow_redirects=False)
        assert root.status_code == 307
        assert root.headers["location"] == "/app/login.html"
        page = client.get("/app/login.html")
        assert page.status_code == 200
        assert "Sign in" in page.text
        assert client.get("/health").json() == {"status": "ok"}  # the API is unaffected


def test_the_mount_is_off_when_the_folder_is_missing(tmp_path):
    with make_client(tmp_path, tmp_path / "missing") as client:
        assert client.get("/app/login.html").status_code == 404
        assert client.get("/", follow_redirects=False).status_code == 404


def test_the_frontend_is_not_part_of_the_api_schema(tmp_path):
    folder = tmp_path / "frontend"
    folder.mkdir()
    with make_client(tmp_path, folder) as client:
        paths = client.get("/openapi.json").json()["paths"]
        assert "/" not in paths
        assert not any(path.startswith("/app") for path in paths)


def test_the_default_folder_is_the_repository_frontend():
    assert Settings().frontend_dir == Path(__file__).resolve().parents[2] / "frontend"
