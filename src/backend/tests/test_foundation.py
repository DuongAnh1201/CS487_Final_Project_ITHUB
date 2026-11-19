"""Foundation: health, error handler, audit log, repository."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationRuleError,
)
from app.modules.usr.repository import UserRepository
from app.shared.audit import AuditLog, AuditRecord


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("error,status", [
    (NotFoundError, 404), (ConflictError, 409), (PermissionDeniedError, 403),
    (AuthenticationError, 401), (ValidationRuleError, 422),
])
def test_domain_error_status_codes(error: type, status: int) -> None:
    assert error.status_code == status


def test_get_or_raise_missing_user(db: Session) -> None:
    with pytest.raises(NotFoundError, match="User not found."):
        UserRepository(db).get_or_raise(9999)


def test_audit_log_records_entry(db: Session) -> None:
    AuditLog(db).record(None, "TEST", "Thing", 5, {"a": 1}, {"a": 2})
    row = db.query(AuditRecord).filter_by(action="TEST").one()
    assert (row.entity_type, row.entity_id, row.old_value, row.new_value) == (
        "Thing", "5", {"a": 1}, {"a": 2})
    assert row.actor_id is None
