"""Alembic migration environment for YoctoCollectionCompanion.

- Reads the database location from `ycc.config` (`YCC_DB_PATH`) and takes its
  target schema from `ycc.models`, so migrations and the app always use the same
  env-driven configuration; the static URL in `alembic.ini` must be left blank.
- SQLite batch mode is enabled so future in-place schema changes work, and
- the database's parent directory is created on run.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from ycc import models  # noqa: F401 — imported so every table registers on the metadata
from ycc.config import get_settings
from ycc.models import SQLModel

# The Alembic Config object provides access to values in the .ini file.
config = context.config

# Resolve the database URL from application settings rather than alembic.ini,
# keeping local and NAS deployments differing only in environment values.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Ensure the SQLite database's parent directory exists (SQLite creates the file
# but not missing parent directories).
settings.db_path.parent.mkdir(parents=True, exist_ok=True)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target schema for autogenerate: every SQLModel table registers on this
# shared metadata when ``ycc.models`` is imported above.
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, no live connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (against a live connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # render_as_batch is required for SQLite: it cannot ALTER most table
        # constructs in place, so Alembic rebuilds tables via a batch copy.
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
