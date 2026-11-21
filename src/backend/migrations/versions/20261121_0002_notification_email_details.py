"""Notification email details and the account events (#108).

- ``notifications.details`` (JSON, nullable): the values a notification's email template shows,
  kept so a retried email looks the same. Older rows stay NULL and use the general design.
- PostgreSQL enum ``eventtype`` gains ACCOUNT_CREATED and PASSWORD_RESET (welcome and
  password-reset emails). SQLite stores enums as text, so it needs no change there.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-21 09:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_EVENT_TYPES = ("ACCOUNT_CREATED", "PASSWORD_RESET")


def upgrade() -> None:
    op.add_column("notifications", sa.Column("details", sa.JSON(), nullable=True))
    if op.get_bind().dialect.name == "postgresql":
        for value in NEW_EVENT_TYPES:
            op.execute(sa.text(f"ALTER TYPE eventtype ADD VALUE IF NOT EXISTS '{value}'"))


def downgrade() -> None:
    # PostgreSQL cannot drop enum values; the two extra labels stay harmless after a downgrade.
    op.drop_column("notifications", "details")
