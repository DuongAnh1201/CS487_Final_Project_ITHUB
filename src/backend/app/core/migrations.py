"""Runs the Alembic migrations in ``src/backend/migrations`` against the app's engine."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine

BACKEND_DIR = Path(__file__).resolve().parents[2]


class SchemaMigrator:
    """Upgrades a database to the latest migration (``alembic upgrade head``)."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def config(self) -> Config:
        """Alembic settings from ``alembic.ini``, bound to this engine instead of a URL."""
        config = Config(str(BACKEND_DIR / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
        return config

    def upgrade(self, revision: str = "head") -> None:
        """Apply every migration the database has not seen yet; safe to run on every start."""
        config = self.config()
        with self.engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, revision)
