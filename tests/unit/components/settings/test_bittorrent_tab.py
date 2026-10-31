"""
Unit tests for BitTorrentTab settings collection.

These cover the helpers extracted from the oversized _collect_bittorrent_settings
(too-many-branches/locals): toggles, encryption mode and user-agent selection map
to their nested keys, the custom user-agent free text is read on the custom
index, and interval spin values are coerced to int seconds. The shared
``settings_module`` / ``make_settings_tab`` fixtures provide the mocked GTK import
and tab builder.
"""

import importlib
from typing import Any
from unittest.mock import MagicMock

_COLLECT_ALL = "_collect_bittorrent_settings"
_COLLECT_USER_AGENT = "_collect_user_agent_setting"
_COLLECT_INTERVALS = "_collect_interval_settings"
_MODULE = "d_fake_seeder.components.component.settings.bittorrent_tab"


def _widget(**returns: Any) -> MagicMock:
    """A mock GTK widget whose getters return the given values."""
    widget = MagicMock()
    for getter, value in returns.items():
        getattr(widget, getter).return_value = value
    return widget


def test_collect_maps_toggles_encryption_and_predefined_agent(settings_module: Any, make_settings_tab: Any) -> None:
    """Toggles, encryption mode and a predefined user agent map to nested keys."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.bittorrent_tab")
        widgets = {
            "enable_dht": _widget(get_active=True),
            "enable_pex": _widget(get_active=False),
            "enable_lpd": _widget(get_active=True),
            "encryption_mode": _widget(get_selected=2),  # -> "forced"
            "user_agent": _widget(get_selected=1),  # -> "qBittorrent/4.3.1"
            "announce_interval": _widget(get_value=1800.0),
        }
        tab = make_settings_tab(mod.BitTorrentTab, widgets)

        result = getattr(tab, _COLLECT_ALL)()

        assert result["bittorrent.enable_dht"] is True
        assert result["bittorrent.enable_pex"] is False
        assert result["bittorrent.enable_lpd"] is True
        assert result["bittorrent.encryption_mode"] == "forced"
        assert result["bittorrent.user_agent"] == "qBittorrent/4.3.1"
        assert result["bittorrent.announce_interval_seconds"] == 1800
        assert isinstance(result["bittorrent.announce_interval_seconds"], int)


def test_collect_custom_user_agent(settings_module: Any, make_settings_tab: Any) -> None:
    """Selecting index 7 reads the free-text custom user agent."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.bittorrent_tab")
        widgets = {
            "user_agent": _widget(get_selected=7),
            "custom_user_agent": _widget(get_text="MyClient/1.2"),
        }
        tab = make_settings_tab(mod.BitTorrentTab, widgets)

        result = getattr(tab, _COLLECT_USER_AGENT)()

        assert result == {"bittorrent.user_agent": "MyClient/1.2"}


def test_collect_intervals_coerced_to_int(settings_module: Any, make_settings_tab: Any) -> None:
    """Interval spin values are coerced to int seconds."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.bittorrent_tab")
        widgets = {
            "announce_interval": _widget(get_value=1800.9),
            "scrape_interval": _widget(get_value=900.0),
        }
        tab = make_settings_tab(mod.BitTorrentTab, widgets)

        result = getattr(tab, _COLLECT_INTERVALS)()

        assert result == {
            "bittorrent.announce_interval_seconds": 1800,
            "bittorrent.scrape_interval_seconds": 900,
        }
