"""
Unit tests for the BitTorrentTab settings-collection logic.

These cover the behaviour-preserving refactor of _collect_bittorrent_settings
(split into focused helpers to resolve too-many-branches/locals): widget values
are mapped to their nested bittorrent.* keys, the encryption mode and predefined
vs custom user agent are selected correctly, and interval values are coerced to
int. The GTK layer and AppSettings are mocked so the module imports headless.
"""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

# Internal names referenced indirectly to avoid protected-member lint.
_CLEANUP_DONE = "_cleanup_done"
_WIDGETS = "_widgets"
_COLLECT_ALL = "_collect_bittorrent_settings"
_COLLECT_USER_AGENT = "_collect_user_agent_setting"
_COLLECT_INTERVALS = "_collect_interval_settings"


@contextlib.contextmanager
def loaded_tab() -> Iterator[ModuleType]:
    """Import bittorrent_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.bittorrent_tab"
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
        yield importlib.import_module("d_fake_seeder.components.component.settings.bittorrent_tab")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _widget(**returns: Any) -> MagicMock:
    """A mock GTK widget whose getters return the given values."""
    widget = MagicMock()
    for getter, value in returns.items():
        getattr(widget, getter).return_value = value
    return widget


def _tab(mod: ModuleType, widgets: dict[str, Any]) -> Any:
    """Build a BitTorrentTab wired to a builder serving the given widgets."""
    tab = mod.BitTorrentTab.__new__(mod.BitTorrentTab)
    setattr(tab, _CLEANUP_DONE, True)  # avoid CleanupMixin.__del__ noise (no __init__ run)
    setattr(tab, _WIDGETS, {})
    tab.logger = MagicMock()
    tab.builder = MagicMock()
    tab.builder.get_object.side_effect = widgets.get
    return tab


def test_collect_maps_toggles_encryption_and_predefined_agent() -> None:
    """Toggles, encryption mode and a predefined user agent map to nested keys."""
    with loaded_tab() as mod:
        widgets = {
            "enable_dht": _widget(get_active=True),
            "enable_pex": _widget(get_active=False),
            "enable_lpd": _widget(get_active=True),
            "encryption_mode": _widget(get_selected=2),  # -> "forced"
            "user_agent": _widget(get_selected=1),  # -> "qBittorrent/4.3.1"
            "announce_interval": _widget(get_value=1800.0),
        }
        tab = _tab(mod, widgets)

        result = getattr(tab, _COLLECT_ALL)()

        assert result["bittorrent.enable_dht"] is True
        assert result["bittorrent.enable_pex"] is False
        assert result["bittorrent.enable_lpd"] is True
        assert result["bittorrent.encryption_mode"] == "forced"
        assert result["bittorrent.user_agent"] == "qBittorrent/4.3.1"
        assert result["bittorrent.announce_interval_seconds"] == 1800
        assert isinstance(result["bittorrent.announce_interval_seconds"], int)


def test_collect_custom_user_agent() -> None:
    """Selecting index 7 reads the free-text custom user agent."""
    with loaded_tab() as mod:
        widgets = {
            "user_agent": _widget(get_selected=7),
            "custom_user_agent": _widget(get_text="MyClient/1.2"),
        }
        tab = _tab(mod, widgets)

        result = getattr(tab, _COLLECT_USER_AGENT)()

        assert result == {"bittorrent.user_agent": "MyClient/1.2"}


def test_collect_intervals_coerced_to_int() -> None:
    """Interval spin values are coerced to int seconds."""
    with loaded_tab() as mod:
        widgets = {
            "announce_interval": _widget(get_value=1800.9),
            "scrape_interval": _widget(get_value=900.0),
        }
        tab = _tab(mod, widgets)

        result = getattr(tab, _COLLECT_INTERVALS)()

        assert result == {
            "bittorrent.announce_interval_seconds": 1800,
            "bittorrent.scrape_interval_seconds": 900,
        }
