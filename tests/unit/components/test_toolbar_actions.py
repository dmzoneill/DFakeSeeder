"""
Unit tests for Toolbar action and search helpers.

These cover the behaviour-preserving refactor that grouped widgets/state into
namespaces, routed model access through the typed ``_model`` property, and
demoted the signal handlers to protected methods. The GTK stack is mocked so the
component imports headless; handlers run on an instance built without __init__.
"""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

_MODULE = "d_fake_seeder.components.component.toolbar"
_GI_MODULES = (
    "gi",
    "gi.repository",
    "gi.repository.Gtk",
    "gi.repository.Gdk",
    "gi.repository.Gio",
    "gi.repository.GLib",
    "gi.repository.GObject",
)
_SPEED_DOUBLE = "_on_toolbar_speed_double_clicked"
_SEARCH_CHANGED = "_on_search_entry_changed"
_WIDGETS = "_widgets"
_STATE = "_state"


@contextlib.contextmanager
def _toolbar_env() -> Iterator[None]:
    """Mock the GTK layer and AppSettings so the toolbar module imports headless."""
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


def _make_toolbar(mod: Any, model: Any = None, entry: Any = None) -> Any:
    """Build a Toolbar without running __init__, with injected model/widgets/state."""
    toolbar = mod.Toolbar.__new__(mod.Toolbar)
    toolbar.model = model
    setattr(toolbar, _WIDGETS, SimpleNamespace(refresh_rate=None, search_entry=entry))
    setattr(
        toolbar,
        _STATE,
        SimpleNamespace(
            settings_dialog=None,
            selection=None,
            search_visible=False,
            tickspeed_pending=False,
            tickspeed_source_id=None,
        ),
    )
    return toolbar


def test_get_selected_and_selection_change() -> None:
    """model_selection_changed stores the torrent that get_selected_torrent returns."""
    with _toolbar_env():
        mod = importlib.import_module(_MODULE)
        toolbar = _make_toolbar(mod)
        assert toolbar.get_selected_torrent() is None
        sentinel = object()
        toolbar.model_selection_changed(None, None, sentinel)
        assert toolbar.get_selected_torrent() is sentinel


def test_toggle_search_entry_toggles_visibility() -> None:
    """toggle_search_entry flips the flag and drives the entry's visibility."""
    with _toolbar_env():
        mod = importlib.import_module(_MODULE)
        entry = MagicMock()
        toolbar = _make_toolbar(mod, model=MagicMock(), entry=entry)
        toolbar.toggle_search_entry()
        assert getattr(toolbar, _STATE).search_visible is True
        entry.set_visible.assert_called_with(True)
        entry.grab_focus.assert_called_once_with()


def test_speed_double_scales_uploads_and_emits() -> None:
    """The speed-double handler doubles each torrent's upload speed and emits once."""
    with _toolbar_env():
        mod = importlib.import_module(_MODULE)
        torrents = [SimpleNamespace(upload_speed=10), SimpleNamespace(upload_speed=5)]
        model = MagicMock()
        model.torrent_list = torrents
        toolbar = _make_toolbar(mod, model=model)
        getattr(toolbar, _SPEED_DOUBLE)(None)
        assert [t.upload_speed for t in torrents] == [20, 10]
        model.emit.assert_called_once_with("data-changed", model, None)


def test_search_entry_changed_sets_filter() -> None:
    """Typing in the search entry forwards the trimmed text to the model filter."""
    with _toolbar_env():
        mod = importlib.import_module(_MODULE)
        model = MagicMock()
        toolbar = _make_toolbar(mod, model=model)
        entry = SimpleNamespace(get_text=lambda: "  hello  ")
        getattr(toolbar, _SEARCH_CHANGED)(entry)
        model.set_search_filter.assert_called_once_with("hello")
