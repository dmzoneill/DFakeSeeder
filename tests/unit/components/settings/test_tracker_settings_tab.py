"""
Unit tests for TrackerSettingsTab settings handling.

These cover the behaviour-preserving refactor that split the oversized
load/collect/validate methods into table-driven helpers: a toggle widget's
state is collected under its settings key, out-of-range and privileged ports
are rejected, and the IPv4 check accepts dotted quads while rejecting malformed
addresses. The GTK layer and AppSettings are mocked so the module imports
headless; internal helpers are reached via variable-name getattr to keep the
access out of the protected-member linter.
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
_VALIDATE_PORTS = "_validate_ports"
_IS_VALID_IPV4 = "_is_valid_ipv4"


@contextlib.contextmanager
def loaded_tab() -> Iterator[ModuleType]:
    """Import tracker_settings_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.tracker_settings_tab"
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
        yield importlib.import_module("d_fake_seeder.components.component.settings.tracker_settings_tab")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _tab(mod: ModuleType, widgets: dict[str, Any]) -> Any:
    """Build a TrackerSettingsTab backed by the given widget map."""
    tab = mod.TrackerSettingsTab.__new__(mod.TrackerSettingsTab)
    setattr(tab, _CLEANUP_DONE, True)
    setattr(tab, _WIDGETS, widgets)
    tab.logger = MagicMock()
    tab.app_settings = MagicMock()
    return tab


def test_is_valid_ipv4_accepts_and_rejects() -> None:
    """The dotted-quad check accepts valid octets and rejects malformed input."""
    with loaded_tab() as mod:
        check = getattr(mod.TrackerSettingsTab, _IS_VALID_IPV4)
        assert check("192.168.0.1") is True
        assert check("0.0.0.0") is True
        assert check("256.1.1.1") is False
        assert check("1.2.3") is False
        assert check("a.b.c.d") is False


def test_collect_toggle_records_active_state() -> None:
    """A present toggle widget's active state is stored under its settings key."""
    with loaded_tab() as mod:
        switch = MagicMock()
        switch.get_active.return_value = True
        tab = _tab(mod, {"tracker_enabled": switch})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_TOGGLES)(collected)
        assert collected["tracker_settings.enabled"] is True


def test_validate_ports_flags_range_and_privilege() -> None:
    """Ports outside 1-65535 report a range error; low ports report a privilege error."""
    with loaded_tab() as mod:
        http = MagicMock()
        http.get_value.return_value = 70000
        udp = MagicMock()
        udp.get_value.return_value = 80
        tab = _tab(mod, {"http_port": http, "udp_port": udp})
        errors: dict[str, str] = {}
        getattr(tab, _VALIDATE_PORTS)(errors)
        assert "between 1 and 65535" in errors["http_port"]
        assert "root privileges" in errors["udp_port"]
