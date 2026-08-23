"""Application configuration, sourced from environment variables.

All runtime configuration lives here so that local development and the eventual
NAS deployment differ only in environment values, never in code. Every setting
can be overridden with a ``YCC_``-prefixed environment variable or an entry in a
local ``.env`` file (see ``.env.example``).

Settings are added to this module as the features that need them arrive; today
the surface is deliberately minimal.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings resolved from the environment.

    Resolution order (highest priority first): explicit init arguments,
    ``YCC_`` environment variables, values in ``.env``, then these defaults.
    """

    model_config = SettingsConfigDict(
        env_prefix="YCC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Human-readable application name, surfaced in the UI.
    app_name: str = "Yocto Collection Companion"


def get_settings() -> Settings:
    """Return application settings loaded from the current environment."""
    return Settings()
