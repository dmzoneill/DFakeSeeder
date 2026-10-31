"""
Unit tests for the BaseSettingsTab public entry points.

These cover the companion change that adds public ``load_settings`` /
``collect_settings`` / ``populate_language_dropdown`` methods delegating to the
tab-specific protected hooks, so the settings dialog can drive tabs without
reaching into protected members. A minimal concrete subclass implements the
abstract hooks; the shared conftest provides the mocked GTK import and builder.
"""

import importlib
from typing import Any

_MODULE = "d_fake_seeder.components.component.settings.base_tab"
_POPULATE_IMPL = "_populate_language_dropdown"


def _mark_loaded(self: Any) -> None:
    """Record that the protected load hook ran."""
    self.loaded = True


def _canned_settings(self: Any) -> dict:
    """Return canned settings values from the protected collect hook."""
    return {"section.key": 7}


def _concrete_cls(mod: Any) -> Any:
    """Build a concrete BaseSettingsTab subclass implementing the abstract hooks.

    Created with ``type()`` so there is no one-public-method stub class for pylint
    to flag, and no literal subclass of the mock-typed base for mypy to reject.
    """
    return type(
        "_ConcreteTab",
        (mod.BaseSettingsTab,),
        {
            "tab_name": property(lambda self: "concrete"),
            "_init_widgets": lambda self: None,
            "_connect_signals": lambda self: None,
            "_setup_dependencies": lambda self: None,
            "_load_settings": _mark_loaded,
            "_collect_settings": _canned_settings,
        },
    )


def test_load_settings_delegates_to_hook(settings_module: Any, make_settings_tab: Any) -> None:
    """The public load_settings calls the protected _load_settings hook."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.base_tab")
        tab = make_settings_tab(_concrete_cls(mod), {})
        tab.load_settings()
        assert tab.loaded is True


def test_collect_settings_delegates_to_hook(settings_module: Any, make_settings_tab: Any) -> None:
    """The public collect_settings returns the protected _collect_settings result."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.base_tab")
        tab = make_settings_tab(_concrete_cls(mod), {})
        assert tab.collect_settings() == {"section.key": 7}


def test_populate_language_dropdown_noop_without_impl(settings_module: Any, make_settings_tab: Any) -> None:
    """populate_language_dropdown is a safe no-op for tabs without the hook."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.base_tab")
        tab = make_settings_tab(_concrete_cls(mod), {})
        tab.populate_language_dropdown()  # must not raise


def test_populate_language_dropdown_calls_impl(settings_module: Any, make_settings_tab: Any) -> None:
    """populate_language_dropdown invokes a tab's _populate_language_dropdown when present."""
    from unittest.mock import MagicMock

    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.base_tab")
        tab = make_settings_tab(_concrete_cls(mod), {})
        impl = MagicMock()
        setattr(tab, _POPULATE_IMPL, impl)
        tab.populate_language_dropdown()
        impl.assert_called_once_with()
