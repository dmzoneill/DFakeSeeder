"""Unit tests for BaseSettingsTab.apply_widget_settings (shared widget loader for settings tabs)."""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

_NAME = "d_fake_seeder.components.component.settings.base_tab"
_MOCKED = [
    "gi",
    "gi.repository",
    "gi.repository.Gtk",
    "gi.repository.Gdk",
    "gi.repository.Gio",
    "gi.repository.GLib",
    "gi.repository.GObject",
    "d_fake_seeder.lib.gi_gtk4",
    "d_fake_seeder.domain.app_settings",
]


@contextlib.contextmanager
def _base_tab() -> Iterator[ModuleType]:
    """Import base_tab with GTK and AppSettings mocked, restoring sys.modules afterwards."""
    saved = {n: sys.modules.get(n) for n in [*_MOCKED, _NAME]}
    for n in _MOCKED:
        sys.modules[n] = MagicMock()
    sys.modules.pop(_NAME, None)
    try:
        yield importlib.import_module(_NAME)
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _stub(widgets: dict, stored: dict) -> SimpleNamespace:
    return SimpleNamespace(_widgets=widgets, app_settings=SimpleNamespace(get=stored.get))


def test_applies_stored_value_or_default_and_skips_none() -> None:
    """Stored values win over defaults; None widgets are skipped."""
    switch, spin = MagicMock(), MagicMock()
    stub = _stub({"switch": switch, "spin": spin, "absent": None}, {"a.key": False})
    with _base_tab() as mod:
        mod.BaseSettingsTab.apply_widget_settings(
            stub, [("switch", "a.key", True), ("absent", "b.key", True)], "set_active"
        )
        mod.BaseSettingsTab.apply_widget_settings(stub, [("spin", "c.key", 42)], "set_value")
    switch.set_active.assert_called_once_with(False)
    spin.set_value.assert_called_once_with(42)


def test_unknown_widget_id_raises_key_error() -> None:
    """Like the per-tab loops it replaces, an unknown widget id raises KeyError for the caller's handler."""
    with _base_tab() as mod, pytest.raises(KeyError):
        mod.BaseSettingsTab.apply_widget_settings(_stub({}, {}), [("missing", "k", 1)], "set_active")
