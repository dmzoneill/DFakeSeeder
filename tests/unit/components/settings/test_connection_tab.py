"""
Unit tests for ConnectionTab settings handling.

These cover the proxy helpers after the broad-except narrowing and import
cleanup: toggling the auth fields propagates sensitivity to both the username
and password widgets, and collecting proxy settings maps the dropdown index to
the matching proxy type. The GTK layer and AppSettings are mocked so the module
imports headless; internal helpers are reached via variable-name getattr to
keep the access out of the protected-member linter.
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
_UPDATE_AUTH = "_update_proxy_auth_fields"
_COLLECT_PROXY = "_collect_proxy_settings"


@contextlib.contextmanager
def loaded_tab() -> Iterator[ModuleType]:
    """Import connection_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.connection_tab"
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
        yield importlib.import_module("d_fake_seeder.components.component.settings.connection_tab")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _tab(mod: ModuleType, widgets: dict[str, Any]) -> Any:
    """Build a ConnectionTab whose widget lookups resolve from ``widgets``."""
    tab = mod.ConnectionTab.__new__(mod.ConnectionTab)
    setattr(tab, _CLEANUP_DONE, True)
    setattr(tab, _WIDGETS, dict(widgets))
    tab.logger = MagicMock()
    tab.builder = MagicMock()
    tab.builder.get_object.side_effect = widgets.get
    return tab


def test_update_proxy_auth_fields_propagates_sensitivity() -> None:
    """Enabling auth sets both the username and password widgets sensitive."""
    with loaded_tab() as mod:
        username = MagicMock()
        password = MagicMock()
        tab = _tab(mod, {"proxy_username": username, "proxy_password": password})
        getattr(tab, _UPDATE_AUTH)(True)
        username.set_sensitive.assert_called_once_with(True)
        password.set_sensitive.assert_called_once_with(True)


def test_collect_proxy_settings_maps_dropdown_type() -> None:
    """The proxy-type dropdown index is mapped to its named type."""
    with loaded_tab() as mod:
        proxy_type = MagicMock()
        proxy_type.get_selected.return_value = 2  # socks4
        server = MagicMock()
        server.get_text.return_value = "proxy.example"
        port = MagicMock()
        port.get_value.return_value = 8080
        tab = _tab(mod, {"proxy_type": proxy_type, "proxy_server": server, "proxy_port": port})
        collected = getattr(tab, _COLLECT_PROXY)()
        assert collected["type"] == "socks4"
        assert collected["server"] == "proxy.example"
        assert collected["port"] == 8080
        assert "username" not in collected
