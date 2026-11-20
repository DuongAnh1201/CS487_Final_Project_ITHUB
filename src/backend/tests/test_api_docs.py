"""API guide (issue #65 part A): OpenAPI completeness and CORS."""

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

PUBLIC = {"/health", "/auth/login", "/auth/google", "/auth/config", "/webhooks/resend"}
ORIGIN = "http://localhost:5173"


@pytest.fixture(scope="module")
def spec() -> dict:
    return create_app(Settings(database_url="sqlite://")).openapi()


def operations(spec: dict):
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            yield path, method.upper(), op


def test_every_route_has_a_readable_summary_and_a_tag(spec):
    for path, method, op in operations(spec):
        assert op["summary"] and not op["summary"].endswith("."), (method, path)
        assert op["summary"] != op["operationId"] and "_" not in op["summary"], (method, path)
        assert op["tags"], (method, path)


def test_tags_are_documented(spec):
    documented = {t["name"] for t in spec["tags"]}
    used = {tag for _, _, op in operations(spec) for tag in op["tags"]}
    assert used <= documented


def test_secured_routes_document_401_and_403(spec):
    for path, method, op in operations(spec):
        if path in PUBLIC:
            continue
        assert op["security"], f"{method} {path} is not marked as needing login"
        assert {"401", "403"} <= set(op["responses"]), (method, path)


def test_routes_with_ids_document_404_and_writes_document_409(spec):
    for path, method, op in operations(spec):
        if "{" in path:
            assert "404" in op["responses"], (method, path)
    assert "409" in spec["paths"]["/users"]["post"]["responses"]
    assert "409" not in spec["paths"]["/auth/login"]["post"]["responses"]


def test_error_responses_use_the_detail_schema(spec):
    ref = spec["paths"]["/users"]["post"]["responses"]["409"]["content"]["application/json"]["schema"]
    assert ref == {"$ref": "#/components/schemas/ErrorResponse"}
    assert spec["components"]["schemas"]["ErrorResponse"]["properties"].keys() == {"detail"}
    assert "401" in spec["paths"]["/auth/login"]["post"]["responses"]


def test_every_request_body_has_an_example(spec):
    for path, method, op in operations(spec):
        body = op.get("requestBody")
        if not body:
            continue
        ref = body["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[1]
        assert spec["components"]["schemas"][ref].get("examples"), f"{method} {path}: {ref} has no example"


def test_public_routes_are_exactly_the_documented_ones(spec):
    open_routes = {path for path, _, op in operations(spec) if not op.get("security")}
    assert open_routes <= PUBLIC


def test_spec_is_valid_json_and_has_metadata(spec):
    assert json.loads(json.dumps(spec))["info"]["title"] == "IT Inventory Tracker API"
    assert "docs/api/README.md" in spec["info"]["description"]


# ---- CORS ----------------------------------------------------------------------------------------

def preflight(client: TestClient, origin: str):
    return client.options("/orders", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type"})


def test_default_origin_is_the_vite_dev_server():
    assert Settings().cors_origins == [ORIGIN]


def test_preflight_from_allowed_origin(client):
    r = preflight(client, ORIGIN)
    assert r.status_code == 200 and r.headers["access-control-allow-origin"] == ORIGIN
    assert "authorization" in r.headers["access-control-allow-headers"].lower()


def test_actual_response_carries_the_cors_header(client):
    r = client.get("/health", headers={"Origin": ORIGIN})
    assert r.headers["access-control-allow-origin"] == ORIGIN


def test_other_origin_is_not_allowed(client):
    r = preflight(client, "https://evil.example")
    assert "access-control-allow-origin" not in r.headers


def test_origins_setting_accepts_comma_or_json(monkeypatch):
    monkeypatch.setenv("ITHUB_CORS_ORIGINS", "http://a.test, https://b.test/")
    assert Settings().cors_origins == ["http://a.test", "https://b.test"]
    monkeypatch.setenv("ITHUB_CORS_ORIGINS", '["http://c.test"]')
    assert Settings().cors_origins == ["http://c.test"]


def test_configured_origin_is_used():
    app = create_app(Settings(database_url="sqlite://", cors_origins=["http://app.test"]))
    with TestClient(app) as client:
        assert preflight(client, "http://app.test").headers["access-control-allow-origin"] == "http://app.test"
        assert "access-control-allow-origin" not in preflight(client, ORIGIN).headers
