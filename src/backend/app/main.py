"""Application factory. Run with ``uvicorn app.main:app --reload`` from src/backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.database import Database
from app.core.exceptions import register_exception_handlers
from app.core.security import PasswordHasher
from app.modules.usr.google import GoogleIdTokenVerifier
from app.modules.usr.repository import SessionRepository, UserRepository
from app.modules.usr.router import auth_router, users_router
from app.modules.usr.service import UserManager
from app.shared.audit import AuditLog

# Each page adds its router(s) to this list (one per line keeps merges clean).
ROUTERS = [
    auth_router,
    users_router,
]


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app: tables, first Admin, routers, error handler."""
    settings = settings or Settings()
    database = Database(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database.create_all()
        with database.SessionLocal() as session:
            manager = UserManager(
                UserRepository(session), SessionRepository(session),
                PasswordHasher(settings.bcrypt_rounds), AuditLog(session, app.state.clock), app.state.clock,
            )
            manager.seed_admin(settings.admin_full_name, settings.admin_email,
                               settings.admin_school_id, settings.admin_password)
            session.commit()
        yield

    app = FastAPI(title="IT Inventory Tracker API", lifespan=lifespan)
    app.state.settings = settings
    app.state.database = database
    app.state.clock = utc_now
    app.state.google_verifier = (
        GoogleIdTokenVerifier(settings.google_client_ids) if settings.google_enabled else None
    )
    register_exception_handlers(app)
    for router in ROUTERS:
        app.include_router(router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        """Liveness check."""
        return {"status": "ok"}

    return app


app = create_app()
