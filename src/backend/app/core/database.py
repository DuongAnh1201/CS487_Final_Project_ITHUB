"""SQLAlchemy base, the Database holder and the per-request session dependency."""

from collections.abc import Iterator
from typing import Any

from fastapi import Request
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.migrations import SchemaMigrator


class Base(DeclarativeBase):
    """Declarative base shared by every module's ORM models."""


class Database:
    """Owns the engine and session factory for one app instance.

    SQLite (local development, tests) and PostgreSQL (Supabase in production) are supported.
    """

    def __init__(self, url: str) -> None:
        self.url = make_url(url)
        self.engine = create_engine(url, **self._engine_options())
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    @property
    def is_sqlite(self) -> bool:
        """True for a SQLite file or in-memory database."""
        return self.url.get_backend_name() == "sqlite"

    def _engine_options(self) -> dict[str, Any]:
        if self.is_sqlite:
            options: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
            if self.url.database in (None, "", ":memory:"):
                options["poolclass"] = StaticPool  # one shared in-memory DB
            return options
        return {
            # A hosted database (Supabase) closes idle connections; test each one before use.
            "pool_pre_ping": True,
            "pool_recycle": 300,
            # Supabase's free tier allows few connections; keep the pool small.
            "pool_size": 5,
            "max_overflow": 5,
            # Supabase's transaction pooler (port 6543) cannot keep prepared statements.
            "connect_args": {"prepare_threshold": None},
        }

    def prepare_schema(self) -> None:
        """Bring the schema up to date at startup.

        SQLite creates the tables straight from the models, so local runs and tests stay fast.
        Any other database is upgraded with the Alembic migrations in ``migrations/``.
        """
        if self.is_sqlite:
            self.create_all()
        else:
            SchemaMigrator(self.engine).upgrade()

    def create_all(self) -> None:
        """Create every table registered on ``Base`` (import models first)."""
        Base.metadata.create_all(self.engine)


def get_db(request: Request) -> Iterator[Session]:
    """One transaction per request: commit on success, roll back on any error."""
    session: Session = request.app.state.database.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
