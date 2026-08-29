"""Test that the Alembic migrations reproduce the models' schema.

Running ``alembic upgrade head`` on an empty database must produce the same
tables and columns that ``SQLModel.metadata.create_all`` produces directly from
the models. This guards against the migration history drifting away from the
models.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlmodel import SQLModel

import ycc.models  # noqa: F401 — registers every table on SQLModel.metadata

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _schema_snapshot(engine) -> dict[str, dict[str, str]]:
    """Return {table: {column: type_str}} for every non-Alembic table."""
    inspector = inspect(engine)
    snapshot: dict[str, dict[str, str]] = {}
    for table in inspector.get_table_names():
        if table == "alembic_version":
            continue
        snapshot[table] = {col["name"]: str(col["type"]) for col in inspector.get_columns(table)}
    return snapshot


def test_migrations_match_models(tmp_path, monkeypatch):
    # Point the app (and thus Alembic's env.py) at a throwaway database file.
    db_path = tmp_path / "migrated.db"
    monkeypatch.setenv("YCC_DB_PATH", str(db_path))

    # Build the expected schema straight from the models.
    expected_engine = create_engine(f"sqlite:///{tmp_path / 'expected.db'}")
    SQLModel.metadata.create_all(expected_engine)
    expected = _schema_snapshot(expected_engine)

    # Build the actual schema by running the migrations to head.
    alembic_cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")

    migrated_engine = create_engine(f"sqlite:///{db_path}")
    actual = _schema_snapshot(migrated_engine)

    assert actual == expected


def test_migration_downgrade_is_empty(tmp_path, monkeypatch):
    # Upgrading then downgrading to base must leave no application tables.
    db_path = tmp_path / "roundtrip.db"
    monkeypatch.setenv("YCC_DB_PATH", str(db_path))

    alembic_cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")

    engine = create_engine(f"sqlite:///{db_path}")
    remaining = [t for t in inspect(engine).get_table_names() if t != "alembic_version"]
    assert remaining == []
