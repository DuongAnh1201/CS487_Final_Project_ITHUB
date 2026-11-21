"""PostgreSQL / Supabase support (#100): URL handling, engine options and the Alembic migrations."""

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

import app.models  # noqa: F401  registers every table
from app.core.config import Settings
from app.core.database import Base, Database
from app.core.migrations import SchemaMigrator
from tests.conftest import TEST_DATABASE_URL

SUPABASE_URL = "postgresql://postgres.abc:secret@aws-0-us-west-1.pooler.supabase.com:5432/postgres"
needs_postgres = pytest.mark.skipif(not TEST_DATABASE_URL, reason="set ITHUB_TEST_DATABASE_URL")


@pytest.mark.parametrize("pasted", [SUPABASE_URL, SUPABASE_URL.replace("postgresql://", "postgres://")])
def test_supabase_url_switches_to_psycopg(pasted):
    """The connection string can be pasted from Supabase as is."""
    assert Settings(database_url=pasted).database_url == SUPABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://")


def test_other_urls_are_kept():
    assert Settings(database_url="sqlite:///./ithub.db").database_url == "sqlite:///./ithub.db"
    url = "postgresql+psycopg://u:p@host/db"
    assert Settings(database_url=url).database_url == url


def test_postgres_engine_is_tuned_for_a_hosted_pooler():
    """Small pool, dead connections replaced, no prepared statements (Supabase pooler)."""
    database = Database(Settings(database_url=SUPABASE_URL).database_url)  # builds lazily, no connection
    assert not database.is_sqlite
    assert database.engine.pool._pre_ping is True
    assert database.engine.pool.size() == 5
    assert database.engine.dialect.driver == "psycopg"


def test_sqlite_still_builds_tables_from_the_models(tmp_path):
    database = Database(f"sqlite:///{tmp_path / 'local.db'}")
    database.prepare_schema()
    assert "users" in inspect(database.engine).get_table_names()
    assert "alembic_version" not in inspect(database.engine).get_table_names()


def _schema_drift(engine) -> list:
    with engine.connect() as connection:
        return compare_metadata(MigrationContext.configure(connection), Base.metadata)


def test_migrations_match_the_models(tmp_path):
    """Every model change needs a migration: upgrading an empty database gives exactly the models.

    If this fails, run ``alembic revision --autogenerate -m "..."`` (see alembic.ini) and review it.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'migrated.db'}")
    SchemaMigrator(engine).upgrade()
    assert _schema_drift(engine) == []


@needs_postgres
def test_postgres_migrations_match_models_and_lock_the_data_api():
    """On PostgreSQL: no drift, row-level security on every table, upgrade twice is a no-op."""
    database = Database(Settings(database_url=TEST_DATABASE_URL).database_url)
    with database.engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    database.prepare_schema()
    database.prepare_schema()
    assert _schema_drift(database.engine) == []
    with database.engine.connect() as connection:
        open_tables = connection.execute(text(
            "SELECT relname FROM pg_class WHERE relnamespace = 'public'::regnamespace "
            "AND relkind = 'r' AND NOT relrowsecurity")).scalars().all()
    assert open_tables == []


@needs_postgres
def test_postgres_partial_indexes_allow_history():
    """One OPEN loan / one current installation per item, but closed rows may repeat."""
    database = Database(Settings(database_url=TEST_DATABASE_URL).database_url)
    with database.engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    database.prepare_schema()
    with database.engine.connect() as connection:
        definitions = dict(connection.execute(text(
            "SELECT indexname, indexdef FROM pg_indexes WHERE indexname IN "
            "('ast_one_open_loan', 'uq_installed_item')")).all())
    assert "WHERE (status = 'OPEN'" in definitions["ast_one_open_loan"]
    assert "WHERE (removed_at IS NULL)" in definitions["uq_installed_item"]
