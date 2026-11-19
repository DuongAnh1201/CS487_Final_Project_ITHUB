"""OpenAPI documentation: tag metadata and uniform route summaries / error responses.

The generated schema is post-processed once, so pages added later are documented
automatically without touching their routers.
"""

import re
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

API_DESCRIPTION = """
JSON REST API for the IT Inventory Tracker. Log in with `POST /auth/login`, then send
`Authorization: Bearer <access_token>` on every other request. Business-rule errors are always
`{"detail": "<message>"}` with the status codes shown on each route. See `docs/api/README.md`.
"""

TAGS = [
    {"name": "auth", "description": "Log in, log out, change own password (USR)."},
    {"name": "users", "description": "Account administration, Admin only (USR)."},
    {"name": "projects", "description": "Projects, members and projects from templates (PRJ)."},
    {"name": "tasks", "description": "Tasks, assignment, hand-off and progress (PRJ)."},
    {"name": "templates", "description": "Project templates (PRJ). Daily-report checklists are `report-templates`."},
    {"name": "assets", "description": "Equipment, consumable stock, borrowers and lending (AST), under `/ast`."},
    {"name": "classrooms and schedules", "description": "Classrooms, installed equipment, room checks, timetables (CLS)."},
    {"name": "issues", "description": "Classroom issues, status workflow, duplicates (ISS)."},
    {"name": "notifications", "description": "In-app notifications, read state, shift summaries (NTF)."},
    {"name": "orders", "description": "Consumable orders and low-stock ordering (ORD)."},
    {"name": "reports", "description": "Daily reports, review workflow, monthly summary (RPT)."},
    {"name": "report-templates", "description": "Daily-report checklists (RPT)."},
    {"name": "audit", "description": "Read-only audit log (RPT)."},
    {"name": "health", "description": "Liveness check."},
]

ERROR_DESCRIPTIONS = {
    401: "Not logged in, session expired, or invalid credentials.",
    403: "The role is not allowed, or a temporary password must be changed first.",
    404: "The record (or a record it refers to) does not exist.",
    409: "The action conflicts with existing data or the record's current state.",
}
LOGIN_ROUTES = {"/auth/login", "/auth/google"}
# POST routes that cannot conflict with existing data.
NO_CONFLICT_ROUTES = LOGIN_ROUTES | {"/auth/logout", "/notifications/shift-summary", "/reports/monthly-summary"}
_REQUIREMENT_SUFFIX = re.compile(r"\s*\((?:[A-Z]{2,}-[A-Z0-9-]+)(?:, ?[A-Z]{2,}-[A-Z0-9-]+)*\)\.?$")
_ID_PREFIX = re.compile(r"^(?:[A-Z]{2,}-[A-Z]*-?[0-9]+(?:[/,] ?[0-9]+)*(?:\s*[-–]\s*[0-9]+)?:\s*)+")
_ERROR_REF = {"$ref": "#/components/schemas/ErrorResponse"}


class ErrorResponse(BaseModel):
    """Every business-rule error: a status code and ``{"detail": message}``."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"detail": "Invalid email or password."}]})

    detail: str


def _summary(operation: dict[str, Any]) -> str:
    """First docstring line without the trailing period and requirement ids."""
    first = (operation.get("description") or operation["summary"]).strip().splitlines()[0]
    text = _REQUIREMENT_SUFFIX.sub("", _ID_PREFIX.sub("", first)).rstrip(".")
    return text[:1].upper() + text[1:]


def document_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Give every operation a readable summary and its documented error responses."""
    schema.setdefault("components", {}).setdefault("schemas", {})["ErrorResponse"] = (
        ErrorResponse.model_json_schema())
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            operation["summary"] = _summary(operation)
            codes: list[int] = []
            if operation.get("security"):
                codes += [401, 403]
            elif path in LOGIN_ROUTES:
                codes.append(401)
            if "{" in path:
                codes.append(404)
            if method.upper() in {"POST", "PUT", "PATCH"} and path not in NO_CONFLICT_ROUTES:
                codes.append(409)
            for code in codes:
                operation["responses"].setdefault(str(code), {
                    "description": ERROR_DESCRIPTIONS[code],
                    "content": {"application/json": {"schema": _ERROR_REF}},
                })
    return schema


def install_openapi(app: FastAPI) -> None:
    """Make ``app.openapi()`` return the documented schema (built once, then cached)."""
    original = app.openapi

    def documented() -> dict[str, Any]:
        if app.openapi_schema is None:
            document_schema(original())
        return app.openapi_schema

    app.openapi = documented  # type: ignore[method-assign]
