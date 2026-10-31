"""
Unit tests for MultiTrackerTab settings collection.

These cover the table-driven collect helpers introduced when splitting the
oversized _collect_settings (too-many-branches): toggle widgets are stored as
booleans under their flat settings keys, integer spins are coerced to int, and
the response-time smoothing value is kept as a float. The GTK layer and
AppSettings are mocked so the module imports headless; internal helpers are
reached via variable-name getattr to keep the access out of the protected-member
linter.
"""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

_CLEANUP_DONE = "_cleanup_done"
_WIDGETS = "_widgets"
_COLLECT_TOGGLES = "_collect_toggle_settings"
_COLLECT_NUMERIC = "_collect_numeric_settings"


@contextlib.contextmanager
def loaded_tab() -> Iterator[ModuleType]:
    """Import multi_tracker_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.multi_tracker_tab"
    gi_names = [
        "gi",
        "gi.repository",
        "gi.repository.Gtk",
        "gi.repository.Gdk",
        "gi.repository.Gio",
        "gi.repository.GLib",
        "gi.repository.GObject",
    ]
    extra = ["d_fake_seeder.lib.gi_gtk4", "d_fake_seeder.domain.app_settings", name]
    saved = {n: sys.modules.get(n) for n in gi_names + extra}
    for n in gi_names:
        sys.modules[n] = MagicMock()
    gi_gtk4 = MagicMock()
    gi_gtk4.GLib.Error = type("GLibError", (Exception,), {})
    sys.modules["d_fake_seeder.lib.gi_gtk4"] = gi_gtk4
    sys.modules["d_fake_seeder.domain.app_settings"] = MagicMock()
    sys.modules.pop(name, None)
    try:
        yield importlib.import_module("d_fake_seeder.components.component.settings.multi_tracker_tab")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _tab(mod: ModuleType, widgets: dict[str, Any]) -> Any:
    """Build a MultiTrackerTab whose widget lookups resolve from ``widgets``."""
    tab = mod.MultiTrackerTab.__new__(mod.MultiTrackerTab)
    setattr(tab, _CLEANUP_DONE, True)
    setattr(tab, _WIDGETS, dict(widgets))
    tab.logger = MagicMock()
    tab.builder = MagicMock()
    tab.builder.get_object.side_effect = widgets.get
    return tab


def test_collect_toggle_records_active_state() -> None:
    """A present toggle widget's active state is stored under its flat key."""
    with loaded_tab() as mod:
        switch = MagicMock()
        switch.get_active.return_value = True
        tab = _tab(mod, {"multi_tracker_enabled": switch})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_TOGGLES)(collected)
        assert collected["protocols.multi_tracker.enabled"] is True


def test_collect_numeric_coerces_int_and_keeps_float() -> None:
    """Integer spins are coerced to int; smoothing keeps its float value."""
    with loaded_tab() as mod:
        failures = MagicMock()
        failures.get_value.return_value = 7.0
        smoothing = MagicMock()
        smoothing.get_value.return_value = 0.5
        tab = _tab(mod, {"max_consecutive_failures": failures, "response_time_smoothing": smoothing})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_NUMERIC)(collected)
        failures_value = collected["protocols.multi_tracker.failover.max_consecutive_failures"]
        assert failures_value == 7
        assert isinstance(failures_value, int)
        assert collected["protocols.multi_tracker.health_monitoring.response_time_smoothing"] == 0.5
