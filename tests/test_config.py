"""Tests for environment-driven application settings."""

from __future__ import annotations

from ycc.config import Settings, get_settings

# ``_env_file=None`` keeps these hermetic: a developer's local ``.env`` must not
# change the outcome of the defaults assertions.


def test_default_app_name():
    settings = Settings(_env_file=None)
    assert settings.app_name == "Yocto Collection Companion"


def test_env_overrides_app_name(monkeypatch):
    monkeypatch.setenv("YCC_APP_NAME", "My Shelf")
    settings = Settings(_env_file=None)
    assert settings.app_name == "My Shelf"


def test_get_settings_returns_settings_instance():
    assert isinstance(get_settings(), Settings)
