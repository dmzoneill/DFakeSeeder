"""
Unit tests for JackettTab's Torznab parsing helpers.

These cover the behaviour-preserving refactor that split the oversized
_parse_torznab_results into focused helpers: torznab:attr pairs are collected,
size falls back from the size attr to the enclosure length, leechers are derived
from peers minus seeders, and a pubDate is trimmed for display. The GTK stack is
mocked so the component imports headless; the helpers run on an instance built
without __init__ (and on the static helpers directly).
"""

import contextlib
import importlib
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock

_MODULE = "d_fake_seeder.components.component.jackett_tab"
_GI_MODULES = (
    "gi",
    "gi.repository",
    "gi.repository.Gtk",
    "gi.repository.Gdk",
    "gi.repository.Gio",
    "gi.repository.GLib",
    "gi.repository.GObject",
)

_CLEANUP_DONE = "_cleanup_done"
_PARSE_ITEM = "_parse_item"
_PARSE_PEERS = "_parse_peers"
_PARSE_SIZE = "_parse_size"
_SIMPLIFY_DATE = "_simplify_date"
_ATTR_VALUES = "_attr_values"

_NS = {"torznab": "http://torznab.com/schemas/2015/feed", "atom": "http://www.w3.org/2005/Atom"}

_RSS = """<rss xmlns:torznab="http://torznab.com/schemas/2015/feed">
  <channel>
    <item>
      <title>Example Release</title>
      <link>http://host/download.torrent</link>
      <category>4000</category>
      <guid>http://host/info</guid>
      <pubDate>Mon, 01 Jan 2024 12:00:00 +0000</pubDate>
      <torznab:attr name="size" value="1048576"/>
      <torznab:attr name="seeders" value="10"/>
      <torznab:attr name="peers" value="13"/>
      <torznab:attr name="jackettindexer" value="MyIndexer"/>
      <torznab:attr name="magneturl" value="magnet:?xt=urn:btih:abc"/>
    </item>
    <item>
      <title>Enclosure Only</title>
      <enclosure length="2048"/>
    </item>
  </channel>
</rss>"""


@contextlib.contextmanager
def _jackett_env() -> Iterator[None]:
    """Mock the GTK layer and AppSettings so the jackett module imports headless."""
    extra = ["d_fake_seeder.lib.gi_gtk4", "d_fake_seeder.domain.app_settings", _MODULE]
    saved = {name: sys.modules.get(name) for name in (*_GI_MODULES, *extra)}
    for name in _GI_MODULES:
        sys.modules[name] = MagicMock()
    sys.modules["d_fake_seeder.lib.gi_gtk4"] = MagicMock()
    sys.modules["d_fake_seeder.domain.app_settings"] = MagicMock()
    sys.modules.pop(_MODULE, None)
    try:
        yield
    finally:
        for name, module in saved.items():
            if module is not None:
                sys.modules[name] = module
            else:
                sys.modules.pop(name, None)


def _items() -> list:
    return ET.fromstring(_RSS).findall(".//item")


def _make_tab(mod: Any) -> Any:
    tab = mod.JackettTab.__new__(mod.JackettTab)
    setattr(tab, _CLEANUP_DONE, True)
    return tab


def test_parse_item_maps_all_fields() -> None:
    """A full torznab item is parsed into the expected result dict."""
    with _jackett_env():
        mod = importlib.import_module(_MODULE)
        tab = _make_tab(mod)
        result = getattr(tab, _PARSE_ITEM)(_items()[0], _NS)
        assert result["title"] == "Example Release"
        assert result["size"] == 1048576
        assert result["seeders"] == 10
        assert result["leechers"] == 3  # peers(13) - seeders(10)
        assert result["category"] == "4000"
        assert result["indexer"] == "MyIndexer"
        assert result["download_url"] == "http://host/download.torrent"
        assert result["magnet_url"] == "magnet:?xt=urn:btih:abc"
        assert result["info_url"] == "http://host/info"
        assert result["publish_date"] == "Mon, 01 Jan"


def test_parse_size_falls_back_to_enclosure() -> None:
    """When no size attr is present, the enclosure length is used."""
    with _jackett_env():
        mod = importlib.import_module(_MODULE)
        parse_size = getattr(mod.JackettTab, _PARSE_SIZE)
        attr_values = getattr(mod.JackettTab, _ATTR_VALUES)
        item = _items()[1]
        assert parse_size(item, attr_values(item, _NS)) == 2048


def test_parse_peers_clamps_at_zero() -> None:
    """Leechers never go negative when peers is below the seeder count."""
    with _jackett_env():
        mod = importlib.import_module(_MODULE)
        parse_peers = getattr(mod.JackettTab, _PARSE_PEERS)
        assert parse_peers({"seeders": "5", "peers": "8"}) == (5, 3)
        assert parse_peers({"seeders": "5", "peers": "2"}) == (5, 0)
        assert parse_peers({}) == (0, 0)


def test_simplify_date_trims_to_leading_tokens() -> None:
    """A pubDate is trimmed to its first three space-separated tokens."""
    with _jackett_env():
        mod = importlib.import_module(_MODULE)
        simplify = getattr(mod.JackettTab, _SIMPLIFY_DATE)
        assert simplify("Mon, 01 Jan 2024 12:00:00 +0000") == "Mon, 01 Jan"
        assert simplify("") == ""
