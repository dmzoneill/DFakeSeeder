"""
Unit tests for JackettTab's Torznab parsing helpers.

These cover the behaviour-preserving refactor that split the oversized
_parse_torznab_results into focused helpers: torznab:attr pairs are collected,
size falls back from the size attr to the enclosure length, leechers are derived
from peers minus seeders, and a pubDate is trimmed for display. The GTK stack is
mocked so the component imports headless; the helpers run on an instance built
without __init__ (and on the static helpers directly).

Lightweight stand-ins mimic the ElementTree ``item`` interface so the tests do
not parse XML (avoiding a real XML parser on test input entirely).
"""

import importlib
from typing import Any

_MODULE = "d_fake_seeder.components.component.jackett_tab"

_CLEANUP_DONE = "_cleanup_done"
_PARSE_ITEM = "_parse_item"
_PARSE_PEERS = "_parse_peers"
_PARSE_SIZE = "_parse_size"
_SIMPLIFY_DATE = "_simplify_date"
_ATTR_VALUES = "_attr_values"

_NS: dict[str, str] = {}


class _FakeElement:
    """Minimal ElementTree-like node exposing findtext/findall/find/get.

    One type stands in for the ``item``, its ``torznab:attr`` children and the
    ``enclosure`` child, so the parse helpers run without a real XML parser.
    """

    def __init__(
        self, texts: dict | None = None, attrs: list | None = None, enclosure: Any = None, data: dict | None = None
    ) -> None:
        self._texts = texts or {}
        self._attrs = attrs or []
        self._enclosure = enclosure
        self._data = data or {}

    def findtext(self, name: str, default: str = "") -> str:
        """Return the named child's text, or ``default``."""
        return self._texts.get(name, default)

    def findall(self, path: str, ns: Any = None) -> list:
        """Return the torznab:attr children for that path, else an empty list."""
        return self._attrs if path == "torznab:attr" else []

    def find(self, path: str) -> Any:
        """Return the enclosure child for that path, else ``None``."""
        return self._enclosure if path == "enclosure" else None

    def get(self, key: str, default: Any = None) -> Any:
        """Return the named attribute value, or ``default``."""
        return self._data.get(key, default)


def _attr(name: str, value: str) -> _FakeElement:
    """Build a fake torznab:attr element."""
    return _FakeElement(data={"name": name, "value": value})


def _full_item() -> _FakeElement:
    return _FakeElement(
        texts={
            "title": "Example Release",
            "link": "http://host/download.torrent",
            "category": "4000",
            "guid": "http://host/info",
            "pubDate": "Mon, 01 Jan 2024 12:00:00 +0000",
        },
        attrs=[
            _attr("size", "1048576"),
            _attr("seeders", "10"),
            _attr("peers", "13"),
            _attr("jackettindexer", "MyIndexer"),
            _attr("magneturl", "magnet:?xt=urn:btih:abc"),
        ],
    )


def _make_tab(mod: Any) -> Any:
    tab = mod.JackettTab.__new__(mod.JackettTab)
    setattr(tab, _CLEANUP_DONE, True)
    return tab


def test_parse_item_maps_all_fields(component_module: Any) -> None:
    """A full torznab item is parsed into the expected result dict."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        tab = _make_tab(mod)
        result = getattr(tab, _PARSE_ITEM)(_full_item(), _NS)
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


def test_parse_size_falls_back_to_enclosure(component_module: Any) -> None:
    """When no size attr is present, the enclosure length is used."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        parse_size = getattr(mod.JackettTab, _PARSE_SIZE)
        attr_values = getattr(mod.JackettTab, _ATTR_VALUES)
        item = _FakeElement(enclosure=_FakeElement(data={"length": "2048"}))
        assert parse_size(item, attr_values(item, _NS)) == 2048


def test_parse_peers_clamps_at_zero(component_module: Any) -> None:
    """Leechers never go negative when peers is below the seeder count."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        parse_peers = getattr(mod.JackettTab, _PARSE_PEERS)
        assert parse_peers({"seeders": "5", "peers": "8"}) == (5, 3)
        assert parse_peers({"seeders": "5", "peers": "2"}) == (5, 0)
        assert parse_peers({}) == (0, 0)


def test_simplify_date_trims_to_leading_tokens(component_module: Any) -> None:
    """A pubDate is trimmed to its first three space-separated tokens."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        simplify = getattr(mod.JackettTab, _SIMPLIFY_DATE)
        assert simplify("Mon, 01 Jan 2024 12:00:00 +0000") == "Mon, 01 Jan"
        assert simplify("") == ""
