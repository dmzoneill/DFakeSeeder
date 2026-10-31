"""
Unit tests for the shared ConnectionsTabBase behind the incoming/outgoing connections tabs.

The GTK layer, AppSettings and the connection manager are mocked so the modules import
headless; tab instances are created without running the GTK constructor.

Note: skipped on Python < 3.14 due to a MagicMock/typing.ForwardRef incompatibility when
importing GTK components with mocked gi (same constraint as the other component tests).
"""

import importlib
import sys
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 14),
    reason="MagicMock causes SyntaxError in typing.ForwardRef on Python < 3.14",
)

_PKG = "d_fake_seeder.components.component.torrent_details"
_MOCKED = (
    "gi",
    "gi.repository",
    "gi.repository.Gtk",
    "gi.repository.Gdk",
    "gi.repository.Gio",
    "gi.repository.GLib",
    "gi.repository.GObject",
    "gi.repository.Pango",
    "d_fake_seeder.domain.app_settings",
    "d_fake_seeder.domain.torrent.connection_manager",
    "d_fake_seeder.domain.torrent.model.connection_peer",
)
_BOOTSTRAP = ("d_fake_seeder.lib.gi_gtk4", "d_fake_seeder.lib.gi_base")
_TABS = (
    f"{_PKG}.connections_tab_base",
    f"{_PKG}.incoming_connections_tab",
    f"{_PKG}.outgoing_connections_tab",
)


class _GError(Exception):
    """Stand-in for GLib.Error used in the narrowed except tuples."""


@pytest.fixture(name="tabs")
def fixture_tabs() -> Iterator[SimpleNamespace]:
    """Import the connections tab modules with GTK mocked; restore sys.modules afterwards."""
    names = (*_MOCKED, *_BOOTSTRAP, *_TABS)
    saved = {n: sys.modules.get(n) for n in names}
    for n in _MOCKED:
        sys.modules[n] = MagicMock()
    for n in _BOOTSTRAP:
        fake = MagicMock()
        fake.GLib.Error = _GError
        fake.GLib.idle_add = lambda func, *args: func(*args)
        sys.modules[n] = fake
    for n in _TABS:
        sys.modules.pop(n, None)
    try:
        yield SimpleNamespace(
            base=importlib.import_module(_TABS[0]),
            incoming=importlib.import_module(_TABS[1]).IncomingConnectionsTab,
            outgoing=importlib.import_module(_TABS[2]).OutgoingConnectionsTab,
        )
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _peer(torrent_hash: str) -> SimpleNamespace:
    return SimpleNamespace(torrent_hash=torrent_hash)


def _bare(tab_class: Any) -> Any:
    """Instance without the GTK constructor; marked cleaned up so CleanupMixin.__del__ is quiet."""
    tab = object.__new__(tab_class)
    vars(tab)["_cleanup_done"] = True
    return tab


def _make(tab_class: Any, tabs: SimpleNamespace, connections: dict, filter_on: bool = False) -> Any:
    """A tab instance with just the attributes the tested methods use (no GTK constructor)."""
    tab = _bare(tab_class)
    manager = MagicMock()
    getattr(manager, f"get_all_{tab_class.DIRECTION}_connections").return_value = connections
    getattr(manager, f"get_global_{tab_class.DIRECTION}_count").return_value = len(connections)
    tab.connection_manager = manager
    tab.connections = {}
    tab.view = tabs.base.ConnectionView(columnview=MagicMock(), filter_checkbox=MagicMock(), store=MagicMock())
    tab.view.filter_checkbox.get_active.return_value = filter_on
    tab.state = tabs.base.ConnectionTabState()
    vars(tab)["_current_torrent"] = None
    return tab


@pytest.mark.parametrize("which", ["incoming", "outgoing"])
def test_direction_metadata(tabs: SimpleNamespace, which: str) -> None:
    """Each subclass keeps its widget id, title and columns."""
    tab_class = getattr(tabs, which)
    tab = _bare(tab_class)
    assert tab.tab_widget_id == f"{which}_connections_tab"
    assert tab.tab_name == f"{which.capitalize()} Connections"
    assert tab_class.COLUMNS[0][0] == "address"
    assert tab_class.COLUMNS[-1][0] == "failure_reason"


@pytest.mark.parametrize("which", ["incoming", "outgoing"])
def test_apply_filter_shows_all_or_selected_torrent(tabs: SimpleNamespace, which: str) -> None:
    """Without the filter every connection is shown; with it only the selected torrent's."""
    connections = {"a:1": _peer("h1"), "b:2": _peer("h2")}
    tab = _make(getattr(tabs, which), tabs, connections)
    tab.apply_filter()
    assert tab.get_connection_count() == 2
    assert tab.get_total_connection_count() == 2

    tab = _make(getattr(tabs, which), tabs, connections, filter_on=True)
    selected = MagicMock()
    selected.torrent_file.get_info_hash_hex.return_value = "h2"
    tab.update_content(selected)
    assert list(tab.connections) == ["b:2"]
    tab.view.store.append.assert_called_once_with(connections["b:2"])


def test_manager_calls_use_direction(tabs: SimpleNamespace) -> None:
    """add/update/remove wrappers delegate to the direction-specific manager methods."""
    incoming = _make(tabs.incoming, tabs, {})
    incoming.add_incoming_connection("1.2.3.4", 6881, "hash", client="x")
    incoming.connection_manager.add_incoming_connection.assert_called_once_with(
        "1.2.3.4", 6881, torrent_hash="hash", connected=True, client="x"
    )
    outgoing = _make(tabs.outgoing, tabs, {})
    outgoing.update_outgoing_connection("5.6.7.8", 1, status="failed")
    outgoing.connection_manager.update_outgoing_connection.assert_called_once_with("5.6.7.8", 1, status="failed")
    outgoing.remove_outgoing_connection("5.6.7.8", 1)
    outgoing.connection_manager.remove_outgoing_connection.assert_called_once_with("5.6.7.8", 1)


def test_clear_connections(tabs: SimpleNamespace) -> None:
    """Clearing empties the displayed rows only."""
    tab = _make(tabs.outgoing, tabs, {"a:1": _peer("h")})
    tab.connections["a:1"] = object()
    tab.clear_connections()
    assert tab.get_connection_count() == 0
    tab.view.store.remove_all.assert_called_once()
    tab.connection_manager.assert_not_called()
