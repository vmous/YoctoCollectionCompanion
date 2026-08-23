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
