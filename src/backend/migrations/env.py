"""Alembic environment: uses the app's engine when the app runs it, else ITHUB_DATABASE_URL."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

import app.models  # noqa: F401  registers every table on Base.metadata
from app.core.config import Settings
from app.core.database import Base

config = context.config
if config.config_file_name and "connection" not in config.attributes:
    fileConfig(config.config_file_name)  # CLI run: log to the console

target_metadata = Base.metadata


def run_migrations(connection) -> None:
    """Run the migrations on one open connection."""
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_from_cli() -> None:
    """``alembic upgrade head`` from a shell: connect with the app's settings."""
    engine = create_engine(Settings().database_url)
    with engine.begin() as connection:
        run_migrations(connection)


if context.is_offline_mode():
    raise SystemExit("Offline (--sql) migrations are not supported; run against a database.")
elif "connection" in config.attributes:
    run_migrations(config.attributes["connection"])  # SchemaMigrator passes the app's engine
else:
    run_from_cli()
