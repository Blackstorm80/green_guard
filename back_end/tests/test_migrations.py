"""La migration Alembic doit produire exactement le schéma des modèles (aucune dérive)."""
import os
import tempfile

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from infrastructure.database import Base

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_migrations_sans_derive(monkeypatch):
    url = f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'migration.db')}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(os.path.join(BACKEND, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(BACKEND, "alembic"))

    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as conn:
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []

    command.downgrade(config, "base")
    command.upgrade(config, "head")
    engine.dispose()
