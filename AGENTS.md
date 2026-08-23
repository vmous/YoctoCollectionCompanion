# AGENTS.md

Essential context for AI agents working on `YoctoCollectionCompanion`. This
file evolves as the project evolves — keep it describing the repository's
*current* state, not planned work.

## What this is

A mobile-first web app to catalog and cost-track a personal collection of
nerdy stuff (Magic: The Gathering cards, video games, board games, comics).
It is developed locally and intended to later self-host on a Synology NAS.

## Current state

An early Python package scaffold: environment-driven configuration
(`ycc.config`) with its tests, plus tooling (uv, Ruff, pytest). There is no
web layer, database, or containerization yet — those arrive in later stages.

## Build, test, lint

See `DEVELOPING.md` for prerequisites and detail. The essentials:

```sh
uv sync                      # install deps + editable package
uv run pytest                # run unit tests
uv run ruff check .          # lint
uv run ruff format --check . # verify formatting
```

## Conventions to follow

- **Package layout:** `src/`-layout; the application package is `ycc`.
- **Dependencies:** managed with uv; `uv.lock` is committed. Add a runtime
  dependency only in the stage that first imports it — do not add libraries
  ahead of use.
- **Interpreter:** pinned exactly in `.python-version`; `pyproject.toml`
  declares a compatibility range.
- **Configuration:** environment-driven via `ycc.config.Settings`, `YCC_`
  prefix. Real values go in a git-ignored `.env`; `.env.example` is the
  committed template and must be kept in sync when settings are added.
- **Lint/format:** Ruff, line length 100, rule set in `pyproject.toml`. Keep
  `ruff check` and `ruff format --check` clean.

## Development workflow

- **Staged and incremental.** Work lands in small, self-contained stages. Each
  stage must build green — `uv run pytest` passing and Ruff clean — and is a
  single reviewed commit.
- **Add only what the current stage needs.** Avoid scaffolding for features
  that are not being implemented yet.
- **Commits** follow the template at `~/.git-commit-template`.
- **Do not push.** The maintainer pushes to the remote manually. Agents commit
  locally only.
