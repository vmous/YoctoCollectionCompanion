# Developing `YoctoCollectionCompanion`

How to set up the project, build it, and run its unit tests. This document
grows as the project gains a web layer, a database, containerization, and so
on; for now it covers the Python package scaffold.

## Project layout

```
YoctoCollectionCompanion/
├── pyproject.toml     # project metadata, dependencies, and tool config
├── uv.lock            # pinned dependency versions (committed)
├── .python-version    # exact interpreter pin (3.12.7)
├── .env.example       # documented template for local environment variables
├── alembic.ini        # Alembic configuration (database migrations)
├── alembic/           # migration environment and version scripts
├── src/ycc/           # the application package
└── tests/             # unit tests (one module per source module)
```

## Prerequisites

- **Python 3.12.7** — the exact interpreter is pinned in `.python-version`.
  Any version manager that reads that file works (e.g. [mise](https://mise.jdx.dev/)
  or [pyenv](https://github.com/pyenv/pyenv)).
- **[uv](https://docs.astral.sh/uv/)** — used for dependency resolution,
  virtual-environment management, and running tooling.

## Setup

Install the project and its dependencies (creates a `.venv/` and installs
`ycc` as an editable package):

```sh
uv sync
```

Dependency versions are pinned in the committed `uv.lock`, so `uv sync`
reproduces the same environment everywhere.

## Running the unit tests

```sh
uv run pytest
```

## Database schema and migrations

The schema is defined by the SQLModel classes in `ycc/models.py`. The database
itself is created and evolved by [Alembic](https://alembic.sqlalchemy.org/)
migrations under `alembic/`. Alembic reads the database location from the same
`ycc.config` settings the app uses (`YCC_DB_PATH`), so a migration always
targets the configured database.

Apply all migrations to bring a database up to the current schema:

```sh
uv run alembic upgrade head
```

### Changing the schema

**During pre-release development we keep a single migration**, rather than
adding one per change. There is no real data to preserve yet, so "migrating" is
just "recreate from the latest models". After editing `ycc/models.py`:

1. Regenerate the one initial migration from the models:

   ```sh
   rm alembic/versions/*.py
   YCC_DB_PATH="$(mktemp -d)/autogen.db" \
     uv run alembic revision --autogenerate -m "create initial ledger schema"
   ```

   (A throwaway `YCC_DB_PATH` keeps autogenerate from creating a real local
   database while it diffs the models against an empty schema.)

2. Add `import sqlmodel` to the generated file's imports. Alembic's template
   emits `sqlmodel.sql.sqltypes.*` column types but does not import the module;
   without this the migration fails to run.

3. Confirm the migration reproduces the models exactly:

   ```sh
   uv run pytest tests/test_migrations.py
   ```

**Before the first real data import or NAS deployment**, this single migration
is frozen as the baseline and the project switches to strict *incremental*
migrations: each subsequent schema change adds its own reviewed migration and
history is never squashed again — that is the point at which Alembic starts
protecting real data.

## Linting and formatting

Linting and formatting are handled by [Ruff](https://docs.astral.sh/ruff/):

```sh
uv run ruff check .          # lint
uv run ruff format --check . # verify formatting (drop --check to reformat)
```

## Conventions

- **Dependencies are added in the stage that first needs them.** The package
  starts with a minimal dependency set that grows feature by feature, rather
  than declaring everything up front.
- **Configuration comes from the environment.** Settings live in
  `ycc.config.Settings`, are prefixed with `YCC_`, and can be provided via
  environment variables or a local, git-ignored `.env` file. Copy
  `.env.example` to `.env` to get started.
