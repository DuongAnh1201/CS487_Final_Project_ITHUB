"""SQLAlchemy base, the Database holder and the per-request session dependency."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base shared by every module's ORM models."""


class Database:
    """Owns the engine and session factory for one app instance."""

    def __init__(self, url: str) -> None:
        kwargs: dict = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in url or url in ("sqlite://", "sqlite:///"):
                kwargs["poolclass"] = StaticPool  # one shared in-memory DB
        self.engine = create_engine(url, **kwargs)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

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
