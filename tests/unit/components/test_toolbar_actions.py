"""
Unit tests for Toolbar action and search helpers.

These cover the behaviour-preserving refactor that grouped widgets/state into
namespaces, routed model access through the typed ``_model`` property, and
demoted the signal handlers to protected methods. The GTK stack is mocked so the
component imports headless; handlers run on an instance built without __init__.
"""

import importlib
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

_MODULE = "d_fake_seeder.components.component.toolbar"
_SPEED_DOUBLE = "_on_toolbar_speed_double_clicked"
_SEARCH_CHANGED = "_on_search_entry_changed"
_WIDGETS = "_widgets"
_STATE = "_state"


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


def test_get_selected_and_selection_change(component_module: Any) -> None:
    """model_selection_changed stores the torrent that get_selected_torrent returns."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        toolbar = _make_toolbar(mod)
        assert toolbar.get_selected_torrent() is None
        sentinel = object()
        toolbar.model_selection_changed(None, None, sentinel)
        assert toolbar.get_selected_torrent() is sentinel


def test_toggle_search_entry_toggles_visibility(component_module: Any) -> None:
    """toggle_search_entry flips the flag and drives the entry's visibility."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        entry = MagicMock()
        toolbar = _make_toolbar(mod, model=MagicMock(), entry=entry)
        toolbar.toggle_search_entry()
        assert getattr(toolbar, _STATE).search_visible is True
        entry.set_visible.assert_called_with(True)
        entry.grab_focus.assert_called_once_with()


def test_speed_double_scales_uploads_and_emits(component_module: Any) -> None:
    """The speed-double handler doubles each torrent's upload speed and emits once."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        torrents = [SimpleNamespace(upload_speed=10), SimpleNamespace(upload_speed=5)]
        model = MagicMock()
        model.torrent_list = torrents
        toolbar = _make_toolbar(mod, model=model)
        getattr(toolbar, _SPEED_DOUBLE)(None)
        assert [t.upload_speed for t in torrents] == [20, 10]
        model.emit.assert_called_once_with("data-changed", model, None)


def test_search_entry_changed_sets_filter(component_module: Any) -> None:
    """Typing in the search entry forwards the trimmed text to the model filter."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        model = MagicMock()
        toolbar = _make_toolbar(mod, model=model)
        entry = SimpleNamespace(get_text=lambda: "  hello  ")
        getattr(toolbar, _SEARCH_CHANGED)(entry)
        model.set_search_filter.assert_called_once_with("hello")
