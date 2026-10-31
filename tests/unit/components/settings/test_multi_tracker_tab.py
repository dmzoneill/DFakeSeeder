"""
Unit tests for MultiTrackerTab settings collection.

These cover the table-driven collect helpers introduced when splitting the
oversized _collect_settings (too-many-branches): toggle widgets are stored as
booleans under their flat settings keys, integer spins are coerced to int, and
the response-time smoothing value is kept as a float. The shared
``settings_module`` / ``make_settings_tab`` fixtures provide the mocked GTK
import and tab builder.
"""

import importlib
from typing import Any
from unittest.mock import MagicMock

_COLLECT_TOGGLES = "_collect_toggle_settings"
_COLLECT_NUMERIC = "_collect_numeric_settings"
_MODULE = "d_fake_seeder.components.component.settings.multi_tracker_tab"


def test_collect_toggle_records_active_state(settings_module: Any, make_settings_tab: Any) -> None:
    """A present toggle widget's active state is stored under its flat key."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.multi_tracker_tab")
        switch = MagicMock()
        switch.get_active.return_value = True
        tab = make_settings_tab(mod.MultiTrackerTab, {"multi_tracker_enabled": switch})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_TOGGLES)(collected)
        assert collected["protocols.multi_tracker.enabled"] is True


def test_collect_numeric_coerces_int_and_keeps_float(settings_module: Any, make_settings_tab: Any) -> None:
    """Integer spins are coerced to int; smoothing keeps its float value."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.multi_tracker_tab")
        failures = MagicMock()
        failures.get_value.return_value = 7.0
        smoothing = MagicMock()
        smoothing.get_value.return_value = 0.5
        tab = make_settings_tab(
            mod.MultiTrackerTab,
            {"max_consecutive_failures": failures, "response_time_smoothing": smoothing},
        )
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_NUMERIC)(collected)
        failures_value = collected["protocols.multi_tracker.failover.max_consecutive_failures"]
        assert failures_value == 7
        assert isinstance(failures_value, int)
        assert collected["protocols.multi_tracker.health_monitoring.response_time_smoothing"] == 0.5
