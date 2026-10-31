"""
Unit tests for NotificationsTab settings loading.

These cover the behaviour-preserving refactor of _load_settings (split into
dropdown/switch/spin helpers): a known position maps to its index, an unknown
one falls back to the default, and spin buttons take the stored value or the
documented default. The shared ``settings_module`` / ``make_settings_tab``
fixtures provide the mocked GTK import and tab builder.
"""

import importlib
from typing import Any
from unittest.mock import MagicMock

_LOAD_DROPDOWNS = "_load_dropdown_settings"
_LOAD_SPINS = "_load_spin_settings"
_MODULE = "d_fake_seeder.components.component.settings.notifications_tab"


def test_known_position_maps_to_index(settings_module: Any, make_settings_tab: Any) -> None:
    """A known position value selects its index in POSITION_VALUES."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.notifications_tab")
        position = MagicMock()
        tab = make_settings_tab(mod.NotificationsTab, {"notification_position": position})
        getattr(tab, _LOAD_DROPDOWNS)({"position": "bottom-left"})
        position.set_selected.assert_called_once_with(mod.NotificationsTab.POSITION_VALUES.index("bottom-left"))


def test_unknown_position_falls_back_to_default(settings_module: Any, make_settings_tab: Any) -> None:
    """An unknown position falls back to the default index (2)."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.notifications_tab")
        position = MagicMock()
        tab = make_settings_tab(mod.NotificationsTab, {"notification_position": position})
        getattr(tab, _LOAD_DROPDOWNS)({"position": "nowhere"})
        position.set_selected.assert_called_once_with(2)


def test_spin_uses_stored_value_or_default(settings_module: Any, make_settings_tab: Any) -> None:
    """Spin buttons take the stored value when present, else the default."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.notifications_tab")
        info = MagicMock()
        max_visible = MagicMock()
        tab = make_settings_tab(
            mod.NotificationsTab,
            {"notification_info_timeout": info, "notification_max_visible": max_visible},
        )
        getattr(tab, _LOAD_SPINS)({"info_timeout_ms": 1234})
        info.set_value.assert_called_once_with(1234)
        max_visible.set_value.assert_called_once_with(3)  # default
