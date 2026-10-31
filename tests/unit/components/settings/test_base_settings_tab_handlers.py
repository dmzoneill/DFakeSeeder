"""
Unit tests for the BaseSettingsTab model/attribute/settings change handlers.

BaseSettingsTab now implements the handlers inherited as abstract from
Component (handle_model_changed / handle_attribute_changed /
handle_settings_changed / update_view), resolving the W0223 abstract-method
gap for every settings tab. Settings tabs are widget-driven, so these events
are behaviour-preservingly traced (matching Component's original bodies).

The GTK layer and AppSettings are mocked so the module imports headless; the
handlers are exercised as unbound calls on a stub ``self`` to avoid GTK
instantiation.
"""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock


@contextlib.contextmanager
def loaded_base() -> Iterator[ModuleType]:
    """Import settings.base_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.base_tab"
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
        yield importlib.import_module(name)
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _stub() -> SimpleNamespace:
    """A minimal stand-in self with just the attributes the handlers touch."""
    return SimpleNamespace(logger=MagicMock())


def test_handle_model_changed_traces() -> None:
    """handle_model_changed logs a trace and does not raise."""
    with loaded_base() as mod:
        stub = _stub()
        assert mod.BaseSettingsTab.handle_model_changed(stub, "src", "data", "changed") is None
        stub.logger.trace.assert_called_once()


def test_handle_attribute_changed_traces() -> None:
    """handle_attribute_changed logs a trace and does not raise."""
    with loaded_base() as mod:
        stub = _stub()
        assert mod.BaseSettingsTab.handle_attribute_changed(stub, "src", "key", "value") is None
        stub.logger.trace.assert_called_once()


def test_handle_settings_changed_traces() -> None:
    """handle_settings_changed logs a trace and does not raise."""
    with loaded_base() as mod:
        stub = _stub()
        assert mod.BaseSettingsTab.handle_settings_changed(stub, "src", "data", "changed") is None
        stub.logger.trace.assert_called_once()


def test_update_view_traces() -> None:
    """update_view logs a trace and does not raise."""
    with loaded_base() as mod:
        stub = _stub()
        assert mod.BaseSettingsTab.update_view(stub, "model", "torrent", "attr") is None
        stub.logger.trace.assert_called_once()
