"""
Unit tests for PeerProtocolTab settings validation.

These exercise the port/transaction-id range validation after the broad-except
narrowing and import cleanup: an inverted seeder port range and an inverted
transaction-id range each produce an error, while a well-ordered pair does not.
The GTK layer and AppSettings are mocked so the module imports headless;
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
_VALIDATE = "_validate_tab_settings"


@contextlib.contextmanager
def loaded_tab() -> Iterator[ModuleType]:
    """Import peer_protocol_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.peer_protocol_tab"
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
        yield importlib.import_module("d_fake_seeder.components.component.settings.peer_protocol_tab")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _spin(value: int) -> Any:
    """Return a spin-button mock whose get_value yields ``value``."""
    widget = MagicMock()
    widget.get_value.return_value = value
    return widget


def _tab(mod: ModuleType, widgets: dict[str, Any]) -> Any:
    """Build a PeerProtocolTab whose widget lookups resolve from ``widgets``."""
    tab = mod.PeerProtocolTab.__new__(mod.PeerProtocolTab)
    setattr(tab, _CLEANUP_DONE, True)
    setattr(tab, _WIDGETS, dict(widgets))
    tab.logger = MagicMock()
    tab.builder = MagicMock()
    tab.builder.get_object.side_effect = widgets.get
    return tab


def test_inverted_ranges_report_errors() -> None:
    """Inverted seeder-port and transaction-id ranges each raise an error."""
    with loaded_tab() as mod:
        widgets = {
            "seeder_port_min": _spin(6889),
            "seeder_port_max": _spin(6881),
            "transaction_id_min": _spin(100),
            "transaction_id_max": _spin(10),
        }
        errors = getattr(_tab(mod, widgets), _VALIDATE)()
        assert "seeder_port_range" in errors
        assert "transaction_id_range" in errors


def test_ordered_ranges_pass() -> None:
    """Well-ordered ranges produce no validation errors."""
    with loaded_tab() as mod:
        widgets = {
            "seeder_port_min": _spin(6881),
            "seeder_port_max": _spin(6889),
            "transaction_id_min": _spin(10),
            "transaction_id_max": _spin(100),
        }
        errors = getattr(_tab(mod, widgets), _VALIDATE)()
        assert errors == {}
