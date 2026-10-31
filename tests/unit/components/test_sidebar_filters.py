"""
Unit tests for the Sidebar filter-counting helpers.

These cover the behaviour-preserving refactor that extracted state matching
into ``_state_matches`` and split the oversized count/update methods: a
torrent's derived state is classified from its ``active``/``uploading``/
``progress`` attributes, tracker URLs are grouped by domain, and unimplemented
states (checking/error/queued) always count as zero. The GTK stack is mocked so
the component imports headless; the pure helpers are exercised on an instance
built without running ``__init__``.
"""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

_MODULE = "d_fake_seeder.components.component.sidebar"
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
_STATE_MATCHES = "_state_matches"
_GET_STATE_COUNT = "_get_state_count"
_EXTRACT_DOMAIN = "_extract_domain"
_GET_TRACKER_STATS = "_get_tracker_stats"


@contextlib.contextmanager
def _sidebar_env() -> Iterator[None]:
    """Mock the GTK layer and AppSettings so the sidebar module imports headless."""
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


def _make_sidebar(mod: Any, model: Any) -> Any:
    """Build a Sidebar without running __init__ (avoids GTK), with ``model`` attached."""
    sidebar = mod.Sidebar.__new__(mod.Sidebar)
    setattr(sidebar, _CLEANUP_DONE, True)
    sidebar.model = model
    return sidebar


def _torrent(**attrs: Any) -> SimpleNamespace:
    return SimpleNamespace(**attrs)


def test_state_matches_classifies_derived_states() -> None:
    """Derived states follow progress/active/uploading; unimplemented ones never match."""
    with _sidebar_env():
        mod = importlib.import_module(_MODULE)
        matches = getattr(mod.Sidebar, _STATE_MATCHES)
        assert matches("seeding", active=True, uploading=True, progress=100.0) is True
        assert matches("seeding", active=True, uploading=False, progress=100.0) is False
        assert matches("downloading", active=True, uploading=False, progress=40.0) is True
        assert matches("downloading", active=True, uploading=False, progress=100.0) is False
        assert matches("active", active=True, uploading=False, progress=10.0) is True
        assert matches("paused", active=False, uploading=False, progress=10.0) is True
        for unimplemented in ("checking", "error", "queued"):
            assert matches(unimplemented, active=True, uploading=True, progress=100.0) is False


def test_get_state_count_counts_all_and_derived() -> None:
    """``all`` returns the total; a derived state counts only matching torrents."""
    with _sidebar_env():
        mod = importlib.import_module(_MODULE)
        torrents = [
            _torrent(active=True, uploading=True, progress=100.0),
            _torrent(active=True, uploading=False, progress=50.0),
            _torrent(active=False, uploading=False, progress=0.0),
        ]
        sidebar = _make_sidebar(mod, SimpleNamespace(torrent_list=torrents))
        assert getattr(sidebar, _GET_STATE_COUNT)("all") == 3
        assert getattr(sidebar, _GET_STATE_COUNT)("seeding") == 1
        assert getattr(sidebar, _GET_STATE_COUNT)("downloading") == 1
        assert getattr(sidebar, _GET_STATE_COUNT)("paused") == 1


def test_get_state_count_without_model_is_zero() -> None:
    """A missing model yields a zero count rather than raising."""
    with _sidebar_env():
        mod = importlib.import_module(_MODULE)
        sidebar = _make_sidebar(mod, None)
        assert getattr(sidebar, _GET_STATE_COUNT)("all") == 0


def test_extract_domain_returns_hostname_or_raw() -> None:
    """A URL yields its hostname; an unparsable value falls back to the raw input."""
    with _sidebar_env():
        mod = importlib.import_module(_MODULE)
        sidebar = _make_sidebar(mod, None)
        assert getattr(sidebar, _EXTRACT_DOMAIN)("http://tracker.example.com:6969/announce") == "tracker.example.com"
        assert getattr(sidebar, _EXTRACT_DOMAIN)("not-a-url") == "not-a-url"


def test_get_tracker_stats_groups_and_sorts_by_count() -> None:
    """Ready torrents' trackers are grouped by domain and sorted by descending count."""
    with _sidebar_env():
        mod = importlib.import_module(_MODULE)

        def make_torrent(ready: bool, urls: list[str]) -> Any:
            torrent = MagicMock()
            torrent.is_ready.return_value = ready
            torrent.get_torrent_file.return_value.get_trackers.return_value = urls
            return torrent

        torrents = [
            make_torrent(True, ["http://a.example.com/x", "http://b.example.com/x"]),
            make_torrent(True, ["http://a.example.com/x"]),
            make_torrent(False, ["http://c.example.com/x"]),
        ]
        sidebar = _make_sidebar(mod, SimpleNamespace(torrent_list=torrents))
        stats = getattr(sidebar, _GET_TRACKER_STATS)()
        assert stats[0] == ("a.example.com", 2, False)
        assert ("b.example.com", 1, False) in stats
        assert all(domain != "c.example.com" for domain, _, _ in stats)
