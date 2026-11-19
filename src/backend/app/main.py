"""Application factory. Run with ``uvicorn app.main:app --reload`` from src/backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.clock import utc_now
from app.core.config import Settings
from app.core.database import Database
from app.core.exceptions import register_exception_handlers
from app.core.openapi import API_DESCRIPTION, TAGS, install_openapi
from app.core.security import PasswordHasher
from app.modules.ntf.channels import LoggingEmailChannel
from app.modules.ntf.router import router as notifications_router
from app.modules.ord.ports import UnavailableStockGateway
from app.modules.ord.router import router as orders_router
from app.modules.rpt.repository import ReportRepository, ReportTemplateRepository
from app.modules.rpt.router import audit_router, reports_router, templates_router as report_templates_router
from app.modules.rpt.service import ReportManager
from app.modules.usr.repository import SessionRepository, UserRepository
from app.modules.usr.router import auth_router, users_router
from app.modules.usr.service import UserManager
from app.shared.audit import AuditLog
from app.shared.events import EventPublisher

# Each page adds its router(s) to this list (one per line keeps merges clean).
ROUTERS = [
    auth_router,
    users_router,
    notifications_router,
    orders_router,
    reports_router,
    report_templates_router,
    audit_router,
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
            ReportManager(
                ReportRepository(session), ReportTemplateRepository(session), UserRepository(session),
                AuditLog(session, app.state.clock), EventPublisher(session), app.state.clock,
            ).seed_default_templates()
            session.commit()
        yield

    app = FastAPI(title="IT Inventory Tracker API", version="1.0.0", description=API_DESCRIPTION,
                  openapi_tags=TAGS, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"],
        allow_headers=["*"], allow_credentials=False,  # bearer tokens, no cookies
    )
    app.state.settings = settings
    app.state.database = database
    app.state.clock = utc_now
    app.state.email_channel = LoggingEmailChannel()
    app.state.stock_gateway = UnavailableStockGateway()  # replaced when the Assets page is wired in
    register_exception_handlers(app)
    for router in ROUTERS:
        app.include_router(router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        """Liveness check."""
        return {"status": "ok"}

    install_openapi(app)
    return app


app = create_app()
