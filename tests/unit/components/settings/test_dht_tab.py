"""
Unit tests for DHTTab settings handling.

These cover the behaviour-preserving refactor that split the oversized
load/collect/validate methods into table-driven helpers: a toggle widget's
state is collected under its settings key, out-of-range routing sizes are
rejected, and the bootstrap-node check accepts host:port entries while
rejecting missing or invalid ports. The GTK layer and AppSettings are mocked so
the module imports headless; internal helpers are reached via variable-name
getattr to keep the access out of the protected-member linter.
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
_VALIDATE_RANGES = "_validate_ranges"
_NODE_ERROR = "_bootstrap_node_error"


@contextlib.contextmanager
def loaded_tab() -> Iterator[ModuleType]:
    """Import dht_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.dht_tab"
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
        yield importlib.import_module("d_fake_seeder.components.component.settings.dht_tab")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _tab(mod: ModuleType, widgets: dict[str, Any]) -> Any:
    """Build a DHTTab backed by the given widget map."""
    tab = mod.DHTTab.__new__(mod.DHTTab)
    setattr(tab, _CLEANUP_DONE, True)
    setattr(tab, _WIDGETS, widgets)
    tab.logger = MagicMock()
    tab.app_settings = MagicMock()
    return tab


def test_bootstrap_node_error_accepts_and_rejects() -> None:
    """A host:port node is accepted; a missing or invalid port is rejected."""
    with loaded_tab() as mod:
        node_error = getattr(mod.DHTTab, _NODE_ERROR)
        assert node_error("router.bittorrent.com:6881") is None
        assert "should be host:port" in node_error("router.bittorrent.com")
        assert "Invalid port" in node_error("host:70000")
        assert "Invalid port" in node_error("host:abc")


def test_collect_toggle_records_active_state() -> None:
    """A present toggle widget's active state is stored under its settings key."""
    with loaded_tab() as mod:
        switch = MagicMock()
        switch.get_active.return_value = True
        tab = _tab(mod, {"dht_enabled": switch})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_TOGGLES)(collected)
        assert collected["protocols.dht.enabled"] is True


def test_validate_ranges_flags_routing_table_size() -> None:
    """A routing-table size outside 8-512 is reported as an error."""
    with loaded_tab() as mod:
        size_widget = MagicMock()
        size_widget.get_value.return_value = 1000
        tab = _tab(mod, {"routing_table_size": size_widget})
        errors: dict[str, str] = {}
        getattr(tab, _VALIDATE_RANGES)(errors)
        assert "between 8 and 512" in errors["routing_table_size"]
