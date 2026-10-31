"""
Unit tests for SettingsDialog tab-coordination helpers.

These exercise the pure coordination logic (lookup, name listing, tab switching)
and the aggregation helpers that now drive tabs through the public
BaseSettingsTab API (``collect_settings`` / ``load_settings``) instead of
protected members. Instances are built with ``__new__`` so no GTK window is
created; fake tabs stand in for the real settings tabs.
"""

import importlib
from types import SimpleNamespace
from typing import Any

_MODULE = "d_fake_seeder.components.component.settings.settings_dialog"
_UI = "_ui"
_STATE = "_state"


def _make_dialog(mod: Any, tabs: list) -> Any:
    """Build a SettingsDialog via __new__ with injected fake tabs and notebook."""
    dialog = mod.SettingsDialog.__new__(mod.SettingsDialog)
    dialog.tabs = tabs
    notebook = SimpleNamespace(page=None)
    notebook.set_current_page = lambda index: setattr(notebook, "page", index)
    setattr(dialog, _UI, SimpleNamespace(parent_window=None, builder=None, notebook=notebook))
    setattr(
        dialog,
        _STATE,
        SimpleNamespace(app=None, deferred_model=None, settings_dirty=False, first_show_complete=False),
    )
    return dialog


def _fake_tab(name: str, settings: dict) -> Any:
    """Return a stand-in tab exposing the public BaseSettingsTab API used here."""
    calls = {"load": 0, "init": 0, "deps": 0}

    def _record(key: str) -> Any:
        def _fn() -> None:
            calls[key] += 1

        return _fn

    return SimpleNamespace(
        tab_name=name,
        collect_settings=lambda: dict(settings),
        load_settings=_record("load"),
        ensure_initialized=_record("init"),
        update_dependencies=_record("deps"),
        calls=calls,
    )


def test_get_tab_by_name_and_names(settings_module: Any) -> None:
    """get_tab_by_name finds the matching tab and get_all_tab_names lists them."""
    with settings_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        tabs = [_fake_tab("General", {}), _fake_tab("Speed", {})]
        dialog = _make_dialog(mod, tabs)
        assert dialog.get_tab_by_name("Speed") is tabs[1]
        assert dialog.get_tab_by_name("Missing") is None
        assert dialog.get_all_tab_names() == ["General", "Speed"]


def test_switch_to_tab_sets_page(settings_module: Any) -> None:
    """switch_to_tab selects the notebook page for a known tab and reports success."""
    with settings_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        tabs = [_fake_tab("General", {}), _fake_tab("Speed", {})]
        dialog = _make_dialog(mod, tabs)
        assert dialog.switch_to_tab("Speed") is True
        assert getattr(dialog, _UI).notebook.page == 1
        assert dialog.switch_to_tab("Missing") is False


def test_export_settings_aggregates_via_public_api(settings_module: Any) -> None:
    """export_settings merges each tab's public collect_settings output."""
    with settings_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        tabs = [_fake_tab("General", {"a.b": 1}), _fake_tab("Speed", {"c.d": 2})]
        dialog = _make_dialog(mod, tabs)
        assert dialog.export_settings() == {"a.b": 1, "c.d": 2}


def test_import_settings_drives_tabs_via_public_api(settings_module: Any) -> None:
    """import_settings calls each tab's public load_settings and update_dependencies."""
    with settings_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        tabs = [_fake_tab("General", {}), _fake_tab("Speed", {})]
        dialog = _make_dialog(mod, tabs)
        assert dialog.import_settings({"a.b": 1}) is True
        assert all(t.calls["load"] == 1 and t.calls["deps"] == 1 for t in tabs)
