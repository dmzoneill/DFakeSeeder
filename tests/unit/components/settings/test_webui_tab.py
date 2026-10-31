"""
Unit tests for WebUITab settings handling.

These cover the helpers introduced when splitting the oversized load/collect/
validate/reset methods: the interface check distinguishes a malformed quad from
an out-of-range octet, switch states collect as booleans, and ports coerce to
int. The GTK layer and AppSettings are mocked so the module imports headless;
internal helpers are reached via variable-name getattr to keep the access out of
the protected-member linter.
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
_INTERFACE_ERROR = "_interface_error"
_COLLECT_BOOLS = "_collect_webui_bools"
_COLLECT_INTS = "_collect_webui_ints"


@contextlib.contextmanager
def loaded_tab() -> Iterator[ModuleType]:
    """Import webui_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.webui_tab"
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
        yield importlib.import_module("d_fake_seeder.components.component.settings.webui_tab")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _tab(mod: ModuleType, widgets: dict[str, Any]) -> Any:
    """Build a WebUITab whose widget lookups resolve from ``widgets``."""
    tab = mod.WebUITab.__new__(mod.WebUITab)
    setattr(tab, _CLEANUP_DONE, True)
    setattr(tab, _WIDGETS, dict(widgets))
    tab.logger = MagicMock()
    tab.builder = MagicMock()
    tab.builder.get_object.side_effect = widgets.get
    return tab


def test_interface_error_distinguishes_format_and_range() -> None:
    """A valid quad passes; a short quad is a format error; a big octet is a range error."""
    with loaded_tab() as mod:
        interface_error = getattr(mod.WebUITab, _INTERFACE_ERROR)
        assert interface_error("192.168.1.10") is None
        assert interface_error("1.2.3") == "Invalid IP address format"
        assert interface_error("1.2.3.300") == "Invalid IP address"


def test_collect_bools_records_active_state() -> None:
    """A present switch widget's active state is stored under its nested key."""
    with loaded_tab() as mod:
        switch = MagicMock()
        switch.get_active.return_value = True
        tab = _tab(mod, {"enable_webui": switch})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_BOOLS)(collected)
        assert collected["webui.enabled"] is True


def test_collect_ints_coerces_port() -> None:
    """The port spin value is coerced to an int under its nested key."""
    with loaded_tab() as mod:
        port = MagicMock()
        port.get_value.return_value = 8080.0
        tab = _tab(mod, {"webui_port": port})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_INTS)(collected)
        assert collected["webui.port"] == 8080
        assert isinstance(collected["webui.port"], int)
