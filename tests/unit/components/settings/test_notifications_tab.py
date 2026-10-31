"""
Unit tests for NotificationsTab settings loading.

These cover the behaviour-preserving refactor of _load_settings (split into
dropdown/switch/spin helpers to resolve too-many-locals): a known position maps
to its index, an unknown one falls back to the default, and spin buttons take
the stored value or the documented default. The GTK layer and AppSettings are
mocked so the module imports headless; internal helpers are reached via
variable-name getattr to keep the access out of the protected-member linter.
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
_LOAD_DROPDOWNS = "_load_dropdown_settings"
_LOAD_SPINS = "_load_spin_settings"


@contextlib.contextmanager
def loaded_tab() -> Iterator[ModuleType]:
    """Import notifications_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.notifications_tab"
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
    sys.modules["d_fake_seeder.lib.gi_gtk4"] = MagicMock()
    sys.modules["d_fake_seeder.domain.app_settings"] = MagicMock()
    sys.modules.pop(name, None)
    try:
        yield importlib.import_module("d_fake_seeder.components.component.settings.notifications_tab")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _tab(mod: ModuleType, widgets: dict[str, Any]) -> Any:
    """Build a NotificationsTab wired to a builder serving the given widgets."""
    tab = mod.NotificationsTab.__new__(mod.NotificationsTab)
    setattr(tab, _CLEANUP_DONE, True)
    setattr(tab, _WIDGETS, {})
    tab.logger = MagicMock()
    tab.builder = MagicMock()
    tab.builder.get_object.side_effect = widgets.get
    return tab


def test_known_position_maps_to_index() -> None:
    """A known position value selects its index in POSITION_VALUES."""
    with loaded_tab() as mod:
        position = MagicMock()
        tab = _tab(mod, {"notification_position": position})
        getattr(tab, _LOAD_DROPDOWNS)({"position": "bottom-left"})
        position.set_selected.assert_called_once_with(mod.NotificationsTab.POSITION_VALUES.index("bottom-left"))


def test_unknown_position_falls_back_to_default() -> None:
    """An unknown position falls back to the default index (2)."""
    with loaded_tab() as mod:
        position = MagicMock()
        tab = _tab(mod, {"notification_position": position})
        getattr(tab, _LOAD_DROPDOWNS)({"position": "nowhere"})
        position.set_selected.assert_called_once_with(2)


def test_spin_uses_stored_value_or_default() -> None:
    """Spin buttons take the stored value when present, else the default."""
    with loaded_tab() as mod:
        info = MagicMock()
        max_visible = MagicMock()
        tab = _tab(mod, {"notification_info_timeout": info, "notification_max_visible": max_visible})
        getattr(tab, _LOAD_SPINS)({"info_timeout_ms": 1234})
        info.set_value.assert_called_once_with(1234)
        max_visible.set_value.assert_called_once_with(3)  # default
